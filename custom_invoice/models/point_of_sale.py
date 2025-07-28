# -*- coding: utf-8 -*-

import logging
import psycopg2
from odoo.tools import float_is_zero
from datetime import datetime
from odoo import fields, models, api, _,tools, SUPERUSER_ID
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class PosConfig(models.Model):
    _inherit = 'pos.config'

    default_customer = fields.Many2one('res.partner', string=_('Cliente Default'),
                                       domain=[('customer','=',True)])
    product_total = fields.Many2one('product.product', string=_('Producto total'))


class PosOrder(models.Model):
    _inherit = 'pos.order'

    #main_journal_id = fields.Many2one(related='session_id.statement_ids.journal_id', string='Metodo de Pago', readonly=True, store=True)
    factura_global_id = fields.Many2one('factura.global',string="Factura Global" ,readonly=True, store=True)

    tipo_comprobante = fields.Selection(
        selection=[('I', 'Ingreso'),
                   ('E', 'Egreso'),
                    ('T', 'Traslado'),],
        string=_('Tipo de comprobante'),
    )

    forma_pago_id  = fields.Many2one('catalogo.forma.pago', string='Forma de pago')
    #num_cta_pago = fields.Char(string=_('Núm. Cta. Pago'))
    methodo_pago = fields.Selection(
        selection=[('PUE', _('Pago en una sola exhibición')),
                   ('PPD', _('Pago en parcialidades o diferido')),
                  ],
        string=_('Método de pago'),
    )
    uso_cfdi_id  = fields.Many2one('catalogo.uso.cfdi', string='Uso CFDI (cliente)')

    @api.model
    def get_invoice_information(self, name, session, sequence):
        order = self.search([('session_id','=',session), ('sequence_number', '=', sequence)], limit=1)
        cfdi_vals = {'uso_cfdi_id':order.uso_cfdi_id.id}
        if order.partner_id:
            cfdi_vals.update({'client_name' : order.partner_id.name, 'client_rfc': order.partner_id.vat})
        else:
            cfdi_vals.update({'client_name' : '', 'client_rfc': ''})

        if order.account_move:
            invoice = order.account_move
            cfdi_vals.update({
                'methodo_pago' : invoice.methodo_pago or '',
                'regimen_fiscal' : invoice.company_id.regimen_fiscal_id.id or '',
                'forma_pago_id' : invoice.forma_pago_id.code or '',
                'numero_cetificado' : invoice.numero_cetificado or '',
                'moneda' : invoice.moneda or '',
                'cetificaso_sat' : invoice.cetificaso_sat or '',
                'tipocambio' : invoice.tipocambio or '',
                'folio_fiscal' : invoice.folio_fiscal or '',
                'fecha_certificacion' : invoice.fecha_certificacion or '',
                'cadena_origenal' : invoice.cadena_origenal or '',
                'selo_digital_cdfi' : invoice.selo_digital_cdfi or '',
                'selo_sat' : invoice.selo_sat or '',
                'invoice_id' : invoice.id,
                'tipo_comprobante' : invoice.tipo_comprobante or 'I',
                'invoice_date' : invoice.invoice_date and invoice.invoice_date.strftime('%Y-%m-%d %H:%M:%S') or '',
                'folio_factura' : invoice.name.replace('INV','').replace('/','') or '',
                'nombre_fiscal': invoice.company_id.nombre_fiscal,
                'expedicion': invoice.company_id.zip,
                })
        else:
            cfdi_vals.update({
                'methodo_pago' : '',
                'regimen_fiscal' : '',
                'forma_pago_id' : '',
                'numero_cetificado' : '',
                'moneda' : '',
                'cetificaso_sat' : '',
                'tipocambio' : '',
                'folio_fiscal' : '',
                'fecha_certificacion' : '',
                'cadena_origenal' : '',
                'selo_digital_cdfi' : '',
                'selo_sat': '',
                'invoice_id' : '',
                'tipo_comprobante' : '',
                'invoice_date': '',
                'folio_factura' : '',
                'nombre_fiscal': '',
                'expedicion': '',
                })
        return cfdi_vals

    @api.model
    def _order_fields(self, ui_order):
        res = super(PosOrder, self)._order_fields(ui_order)
        amount_paid = 0
        metodo_pago_pos_id = None
        for statement in ui_order['statement_ids']:
            payment = statement[2]
            if amount_paid > 0:
                if payment['amount'] > amount_paid:
                    metodo_pago_pos_id = self.env['pos.payment.method'].sudo().search([('id','=',payment['payment_method_id'])], limit=1)
            else:
                metodo_pago_pos_id = self.env['pos.payment.method'].sudo().search([('id','=',payment['payment_method_id'])], limit=1)
                amount_paid = payment['amount']
        if metodo_pago_pos_id:
            forma_pago_obj = metodo_pago_pos_id.forma_pago_id
            res.update({'forma_pago_id': forma_pago_obj and forma_pago_obj.id or None})
            res.update({'methodo_pago': metodo_pago_pos_id.methodo_pago or None})
#        if 'forma_pago_id' in ui_order:
#            if ui_order['forma_pago_id']:
#                forma_pago_obj = self.env['catalogo.forma.pago'].sudo().search([('code','=',ui_order['forma_pago_id'])], limit=1)
#            res.update({'forma_pago_id': forma_pago_obj and forma_pago_obj.id or None})
#        if 'methodo_pago' in ui_order:
#            res.update({'methodo_pago': ui_order['methodo_pago'] or None})
        if 'uso_cfdi_id' in ui_order:
            if ui_order['uso_cfdi_id']:
                uso_cfdi_obj = self.env['catalogo.uso.cfdi'].sudo().search([('code','=',ui_order['uso_cfdi_id'])], limit=1)
            res.update({'uso_cfdi_id': uso_cfdi_obj and uso_cfdi_obj.id or None})
        return res

    def _prepare_invoice(self):
        res = super(PosOrder, self)._prepare_invoice()

        res.update({'forma_pago_id': self.forma_pago_id.id,
                    'methodo_pago': self.methodo_pago,
                    'uso_cfdi_id': self.uso_cfdi_id.id,
                    'tipo_comprobante': 'I',
                    #'factura_cfdi': True,
                    })
        return res

    def action_invoice(self, partner_total=None):
        Invoice = self.env['account.move']
        inv_ids = []
        invoices = {}
        origin = []
        orders = self.browse()
        note = ''
        invoice_lines=[]
        sale_journal = self[0].session_id.config_id.invoice_journal_id #self[0].sale_journal

        for order in self:
            if self.env['ir.config_parameter'].sudo().get_param('custom_invoice.fg_code'):
               order_name = order.ticket_code
            else:
               order_name = order.name
            origin.append(order_name)
            orders += order
            for order_line in order.lines:
                invoice_lines.append((0, None,order._prepare_invoice_line(order_line)))

        for order in self:
            if self.env['ir.config_parameter'].sudo().get_param('custom_invoice.fg_code'):
               order_name = order.ticket_code
            else:
               order_name = order.name
            local_context = dict(self.env.context, force_company=order.company_id.id, company_id=order.company_id.id)
            if order.account_move:
                Invoice += order.account_move
                continue

            if not order.partner_id and not partner_total:
                raise UserError(_('Favor de ingresar un cliente para la factura.'))
            if partner_total and not self.env['ir.config_parameter'].sudo().get_param('custom_invoice.fg_client'):
                order.write({'partner_id': partner_total.id})

            partner = order.partner_id
            note += '%s, %s;' % (order.pos_reference, order.amount_total)
            group_key = partner.id

            inv_dict = order._prepare_invoice_vals_new(invoice_lines)
            inv_dict['partner_id'] = partner.id
            invoice = Invoice.new(inv_dict)
            invoice._onchange_partner_id()
            invoice.fiscal_position_id = order.fiscal_position_id

            inv = invoice._convert_to_write({name: invoice[name] for name in invoice._cache})
            inv.update({'forma_pago_id': order.forma_pago_id.id,
                        'methodo_pago': order.methodo_pago,
                        'uso_cfdi_id': order.uso_cfdi_id.id,
                        'tipo_comprobante': 'I',
                        'journal_id': sale_journal and sale_journal.id or None,
                        'invoice_origin': ', '.join(origin),
                        })

            move_lines=[]

            move_lines=invoice_lines

            if group_key not in invoices:
                if move_lines:
                    inv.update({'invoice_line_ids': move_lines})
                    if 'line_ids' in inv:
                        inv.pop('line_ids')
                new_invoice = Invoice.with_context(local_context).sudo().create(inv)
                order.sudo().write({'account_move': new_invoice.id, 'state': 'invoiced'})
                inv_ids.append(new_invoice.id)
                invoices[group_key] = new_invoice.id
                Invoice += new_invoice
            elif group_key in invoices:
                invoice_obj = Invoice.sudo().with_context(local_context).browse(invoices[group_key])
                order.sudo().write({'account_move': invoice_obj.id, 'state': 'invoiced'})
                if order_name not in invoice_obj.invoice_origin:
                    invoice_obj.write({'invoice_origin': invoice_obj.invoice_origin + ', ' + order_name})
            inv_id = invoices[group_key]
            new_invoice = Invoice.sudo().with_context(local_context).browse(inv_id)

            for line in order.lines:
                if line.discount:
                    new_invoice.write({'discount':line.discount})
            for order in self:
                order.sudo().write({'state': 'invoiced','partner_id': partner.id,'account_move': new_invoice.id, 'state': 'invoiced'})

            new_invoice.sudo().write({'narration': note})
            if order.account_move:
                order.sudo().account_move.write({'partner_id': partner.id})
                order.sudo().account_move.line_ids.write({'partner_id': partner.id})
            for line in order.session_id.statement_line_ids:
                line.move_line_ids.write({'partner_id':partner.id})
            break
            # this workflow signal didn't exist on account.invoice -> should it have been 'invoice_open' ? (and now method .action_invoice_open())
            # shouldn't the created invoice be marked as paid, seing the customer paid in the POS?
            # new_invoice.sudo().signal_workflow('validate')
#            new_invoice.sudo().action_invoice_open()
#            new_invoice.sudo().force_invoice_send()

        if not Invoice:
            return {}

        return {
            'name': _('Customer Invoice'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_move_form').id,
            'res_model': 'account.move',
            'context': "{'move_type':'out_invoice'}",
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': Invoice and Invoice.ids[0] or False,
        }


    def action_invoice_compacta(self, partner_total=None):
        Invoice = self.env['account.move']
        inv_ids = []
        invoices = {}
        origin =[]
        note = ''
        invoice_lines=[]
        all_order_lines=[]
        sale_journal = self[0].session_id.config_id.invoice_journal_id #self[0].sale_journal

        for order in self:
            if self.env['ir.config_parameter'].sudo().get_param('custom_invoice.fg_code'):
               order_name = order.ticket_code
            else:
               order_name = order.name
            for order_line in order.lines:
                if not all_order_lines:
                    all_order_lines.append(order._prepare_invoice_line(order_line))
                else:
                    is_add=True;
                    for data in all_order_lines:
                        if data.get('product_id') == order_line.product_id.id and data.get('tax_ids')[0][2]==order_line.tax_ids_after_fiscal_position.ids:
                            data['quantity']= data['quantity']+order_line.qty
                            is_add=False
                    if is_add:
                        all_order_lines.append(order._prepare_invoice_line(order_line))
            origin.append(order_name)

        for line in all_order_lines:
            invoice_lines.append((0, None,line))

        for order in self:
            if self.env['ir.config_parameter'].sudo().get_param('custom_invoice.fg_code'):
               order_name = order.ticket_code
            else:
               order_name = order.name
            local_context = dict(self.env.context, force_company=order.company_id.id, company_id=order.company_id.id)
            if order.account_move:
                Invoice += order.account_move
                continue

            if not order.partner_id and not partner_total:
                raise UserError(_('Favor de ingresar un cliente para la factura.'))
            if partner_total and not self.env['ir.config_parameter'].sudo().get_param('custom_invoice.fg_client'):
                order.write({'partner_id': partner_total.id})

            partner = order.partner_id
            note += '%s, %s;' % (order.pos_reference, order.amount_total)
            group_key = partner.id

            inv_dict = order._prepare_invoice_vals_new(invoice_lines)
            inv_dict['partner_id'] = partner.id
            invoice = Invoice.new(inv_dict)
            invoice._onchange_partner_id()
            invoice.fiscal_position_id = order.fiscal_position_id

            inv = invoice._convert_to_write({name: invoice[name] for name in invoice._cache})
            inv.update({
                        'forma_pago_id': order.forma_pago_id.id,
                        'methodo_pago': order.methodo_pago,
                        'uso_cfdi_id': order.uso_cfdi_id.id,
                        'tipo_comprobante': 'I',
                        'journal_id': sale_journal and sale_journal.id or None,
                        })

            move_lines=[]
#             for line in order.lines:
#                 invoice_line_vals = order.with_context(local_context)._prepare_invoice_line(line)
            move_lines=invoice_lines

            if group_key not in invoices:
                if move_lines:
                    inv.update({'invoice_line_ids': move_lines})
                    inv.update({'invoice_origin': ', '.join(origin)})
                    if 'line_ids' in inv:
                        inv.pop('line_ids')
                new_invoice = Invoice.with_context(local_context).sudo().create(inv)
                order.write({'account_move': new_invoice.id, 'state': 'invoiced'})
                inv_ids.append(new_invoice.id)
                invoices[group_key] = new_invoice.id
                Invoice += new_invoice
            elif group_key in invoices:
                invoice_obj = Invoice.with_context(local_context).browse(invoices[group_key])
                order.write({'account_move': invoice_obj.id, 'state': 'invoiced'})
                if order_name not in invoice_obj.invoice_origin:
                    invoice_obj.write({'invoice_origin': invoice_obj.invoice_origin + ', ' + order_name})
            inv_id = invoices[group_key]
            new_invoice = Invoice.with_context(local_context).browse(inv_id)

            for line in order.lines:
                if line.discount:
                    new_invoice.write({'discount':line.discount})
            for order in self:
                order.sudo().write({'state': 'invoiced','partner_id': partner.id,'account_move': new_invoice.id, 'state': 'invoiced'})
            new_invoice.sudo().write({'narration': note})
            if order.account_move:
                order.account_move.write({'partner_id': partner.id})
                order.account_move.line_ids.write({'partner_id': partner.id})
            for line in order.session_id.statement_line_ids:
                line.move_line_ids.write({'partner_id':partner.id})
            break
            # this workflow signal didn't exist on account.invoice -> should it have been 'invoice_open' ? (and now method .action_invoice_open())
            # shouldn't the created invoice be marked as paid, seing the customer paid in the POS?
            # new_invoice.sudo().signal_workflow('validate')
#            new_invoice.sudo().action_invoice_open()
#            new_invoice.sudo().force_invoice_send()

        if not Invoice:
            return {}

        return {
            'name': _('Customer Invoice'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_move_form').id,
            'res_model': 'account.move',
            'context': "{'move_type':'out_invoice'}",
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': Invoice and Invoice.ids[0] or False,
        }

    @api.model
    def _process_order(self, order, draft, existing_order):
        """Create or update an pos.order from a given dictionary.

        :param pos_order: dictionary representing the order.
        :type pos_order: dict.
        :param draft: Indicate that the pos_order is not validated yet.
        :type draft: bool.
        :param existing_order: order to be updated or False.
        :type existing_order: pos.order.
        :returns number pos_order id
        """
        order = order['data']
        pos_session = self.env['pos.session'].browse(order['pos_session_id'])
        if pos_session.state == 'closing_control' or pos_session.state == 'closed':
            order['pos_session_id'] = self._get_valid_session(order).id

        pos_order = False
        if not existing_order:
            pos_order = self.create(self._order_fields(order))
        else:
            pos_order = existing_order
            pos_order.lines.unlink()
            order['user_id'] = pos_order.user_id.id
            pos_order.write(self._order_fields(order))

        pos_order = pos_order.with_company(pos_order.company_id)
        self = self.with_company(pos_order.company_id)
        self._process_payment_lines(order, pos_order, pos_session, draft)

        if not draft:
            try:
                pos_order.action_pos_order_paid()
            except psycopg2.DatabaseError:
                # do not hide transactional errors, the order(s) won't be saved!
                raise
            except Exception as e:
                _logger.error('No pudo procesar completamente el pedido de venta: %s', tools.ustr(e))
            pos_order._create_order_picking()
            pos_order._compute_total_cost_in_real_time()

        if pos_order.to_invoice and pos_order.state == 'paid':
            pos_order._generate_pos_order_invoice()
            #pos_order.action_pos_order_invoice()

            #Add BY Nilesh
            pos_order.account_move.update({'forma_pago_id': pos_order.forma_pago_id.id,
                        'methodo_pago': pos_order.methodo_pago,
                        'uso_cfdi_id': pos_order.uso_cfdi_id.id,
                        'tipo_comprobante': 'I',
                        #'factura_cfdi': True
                        })
            try:
               pos_order.account_move.sudo().action_cfdi_generate()
               pos_order.account_move.sudo().force_invoice_send()
            except Exception as e:
               _logger.error('No pudo crear la factura: %s', tools.ustr(e))

        return pos_order.id

    def action_invoice_total(self, product_total=None, partner_total=None, invoice_format=None):
        Invoice = self.env['account.move']
        inv_line_ref = self.env['account.move.line']
        inv_ids = []
        invoices = {}

        if not product_total:
            raise UserError(_('Falta agregar un producto para la factura.'))

        note = ''
        origin = []
        if not partner_total:
            raise UserError(_('Favor de ingresar un cliente para la factura.'))

        partner = partner_total
        group_key = partner.id
        if not self:
            return
        sale_journal = self[0].session_id.config_id.invoice_journal_id #self[0].sale_journal
        company_id = self[0].company_id.id
        local_context = dict(self.env.context, force_company=self[0].company_id.id, company_id=self[0].company_id.id)
        orders = self.browse()
        taxes_group  = {}
        order_lines=[]
        move_lines=[]
        for order in self:
            if self.env['ir.config_parameter'].sudo().get_param('custom_invoice.fg_code'):
               order_name = order.ticket_code
            else:
               order_name = order.name
            if order.account_move:
                inv_ids.append(order.account_move)
                continue
            if partner_total and not self.env['ir.config_parameter'].sudo().get_param('custom_invoice.fg_client'):
                order.write({'partner_id': partner_total.id})

            for line in order.lines:
                if invoice_format=='cfdi':
                    if (line.tax_ids_after_fiscal_position,order) not in taxes_group:
                        taxes_group.update({(line.tax_ids_after_fiscal_position,order):line})
                    else:
                        taxes_group[(line.tax_ids_after_fiscal_position,order)] +=line
                else:
                    if (line.tax_ids_after_fiscal_position,self) not in taxes_group:
                        taxes_group.update({(line.tax_ids_after_fiscal_position,self):line})
                    else:
                        taxes_group[(line.tax_ids_after_fiscal_position,self)] +=line

                invoice_line_vals = order.with_context(local_context)._prepare_invoice_line(line)
                move_lines.append((0,0,invoice_line_vals))
            if order.pos_reference:
                note += '%s, %s;' % (order.pos_reference.replace('Pedido ',''), order.amount_total)
            else:
                note += '%s;' % (order.amount_total)
            origin.append(order_name)

            if order.account_move:
                order.account_move.write({'partner_id': partner.id})
                order.account_move.line_ids.write({'partner_id': partner.id})
            for line in order.session_id.statement_line_ids:
                line.move_line_ids.write({'partner_id':partner.id})
            orders += order

        if taxes_group:
            acc = partner.property_account_receivable_id.id
            inv = {
               # 'name': origin and origin[0],
                'invoice_origin': ', '.join(origin),
                'journal_id': sale_journal and sale_journal.id or None,
                'move_type': 'out_invoice',
                'ref': origin and origin[0],
                'partner_id': partner.id,
                'currency_id': self[0].pricelist_id.currency_id.id, # considering partner's sale pricelist's currency
                'company_id': company_id,
                'user_id': self.env.uid,
                'forma_pago_id': self.env['catalogo.forma.pago'].sudo().search([('code','=','01')], limit=1).id,
                'methodo_pago': 'PUE',
                'uso_cfdi_id': self.env['catalogo.uso.cfdi'].sudo().search([('code','=','S01')], limit=1).id,
                'tipo_comprobante': 'I',
                }
            invoice = Invoice.new(inv)
            invoice_line_dict=[]
            for order_taxes, order_lines in taxes_group.items():
                taxes = order_taxes[0]
                price_unit = 0.0
                for line in order_lines:
                    if line.discount:
                        price_unit += (line.price_unit * (1 - (line.discount or 0.0) / 100.0))*line.qty
                    else:
                        price_unit += line.price_unit*line.qty
                if order_taxes[1]:
                    if order_taxes[1][0].pos_reference:
                        inv_line_name = (invoice_format == 'cfdi') and '[%s] %s' % (order_taxes[1].pos_reference.replace('Pedido ',''), product_total.name) or  product_total.name
                    else:
                        inv_line_name = (invoice_format == 'cfdi') and '[%s] %s' % (order_taxes[1][0].name, product_total.name) or  product_total.name
                inv_line = {
                    'move_id': invoice.id,
                    'product_id': product_total.id,
                    'price_unit': price_unit,
                    'quantity': 1,
                    'name': inv_line_name,
                }
                invoice_line = inv_line_ref.new(inv_line)
                invoice_line._onchange_product_id()
                taxes_new=[]
                for tax in taxes:
                    taxes_new.append(tax.id)
                invoice_line
                # We convert a new id object back to a dictionary to write to bridge between old and new api
                inv_line = invoice_line._convert_to_write({name: invoice_line[name] for name in invoice_line._cache})
                inv_line.update({'price_unit': price_unit,'name': inv_line_name})
                inv_line.update({'tax_ids': [(6,0,taxes_new)]})
                invoice_line_dict.append((0, None,inv_line))
            inv.update({'invoice_line_ids': invoice_line_dict})
            invoice = Invoice.sudo().with_context(local_context).create(inv)
            inv_ids.append(invoice)

            orders.sudo().write({'state': 'invoiced', 'account_move': invoice.id})

        if not inv_ids: return {}

        return {
            'name': _('Customer Invoice'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'account.move',
            'context': {},
            'type': 'ir.actions.act_window',
            'res_id': inv_ids[0],
        }

    def action_factura_global(self, partner_total=None):
        factura = self.env['factura.global']
        factura_dic={}
        invoices = {}
        sale_journal = self[0].sale_journal
        note = ''
        for order in self:
            # Force company for all SUPERUSER_ID action
            if order.refunded_orders_count > 0:
               continue

            local_context = dict(self.env.context, force_company=order.company_id.id, company_id=order.company_id.id)
            if order.factura_global_id:
                factura += order.factura_global_id
                continue

            if not order.partner_id and not partner_total:
                raise UserError(_('Falta agregar un cliente para la factura.'))
            if partner_total and not self.env['ir.config_parameter'].sudo().get_param('custom_invoice.fg_client'):
                order.write({'partner_id': partner_total.id})

            if self.env['ir.config_parameter'].sudo().get_param('custom_invoice.fg_code'):
               order_name = order.ticket_code
            else:
               order_name = order.name

            partner = order.partner_id
            note += '%s, %s;' % (order.pos_reference, order.amount_total)
            group_key = partner_total.id
            factura_line = []
            for line in order.lines:
                factura_line.append((0,0,{'product_id':line.product_id.id,
                                     'name':line.product_id.partner_ref,
                                     'price_unit':line.price_unit,
                                     'quantity':line.qty,
                                     'discount': line.discount,
                                     'invoice_line_tax_ids': [(6, 0, line.tax_ids.ids)]
                                     }))
            factura_dic.update({
                                'partner_id': partner_total.id,
                                'invoice_date': datetime.today(),
                                'factura_line_ids': factura_line,
                                'source_document': order_name,
                                'forma_pago_id': self.env['catalogo.forma.pago'].sudo().search([('code','=','01')], limit=1).id,
                                'methodo_pago': 'PUE',
                                'journal_id': sale_journal and sale_journal.id or None,
                                'tipo_comprobante': 'I',
                                })
            if group_key not in invoices:
                new_invoice = factura.with_context(local_context).sudo().create(factura_dic)
                order.write({'factura_global_id': new_invoice.id, 'state': 'invoiced'})
                invoices[group_key] = new_invoice.id
                factura += new_invoice
            elif group_key in invoices:
                invoice_obj = factura.with_context(local_context).browse(invoices[group_key])
                order.write({'factura_global_id': invoice_obj.id, 'state': 'invoiced'})
                if invoice_obj.source_document:
                    if order_name not in invoice_obj.source_document.split(', '):
                        invoice_obj.write({'source_document': invoice_obj.source_document + ', ' + order_name})
                else:
                    invoice_obj.write({'source_document': order_name})
                new_invoice.write({'factura_line_ids':factura_line})
            order.sudo().write({'state': 'invoiced'})

        fg_nc_create = self.env['ir.config_parameter'].sudo().get_param('custom_invoice.fg_nc_create')
        if fg_nc_create:
           self.action_check_nota_credito(partner_total)

        if not factura:
            return {}

        return {
            'name': _('Factura Global'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('custom_invoice.view_fatura_global_form').id,
            'res_model': 'factura.global',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': factura and factura.ids[0] or False,
        }

    def action_factura_global_total(self, product_total=None, partner_total=None, invoice_format=None):
        factura = self.env['factura.global']
        inv_ids = []
        if not product_total:
            raise UserError(_('Falta agregar un producto para la factura.'))

        note = ''
        origin = []
        if not partner_total:
            raise UserError(_('Falta agregar un cliente para la factura.'))

        partner = partner_total
        if not self:
            return
        sale_journal = self[0].sale_journal
        company_id = self[0].company_id.id
        local_context = dict(self.env.context, force_company=self[0].company_id.id, company_id=self[0].company_id.id)
        orders = self.browse()
        taxes_group  = {}
        order_lines=[]
        move_lines=[]

        for order in self:
            if order.refunded_orders_count > 0:
               continue
            if order.factura_global_id:
                inv_ids.append(order.factura_global_id)
                continue
            if partner_total and not self.env['ir.config_parameter'].sudo().get_param('custom_invoice.fg_client'):
                order.write({'partner_id': partner_total.id})

            if self.env['ir.config_parameter'].sudo().get_param('custom_invoice.fg_code'):
               order_name = order.ticket_code
            else:
               order_name = order.name

            for line in order.lines:
                if invoice_format=='cfdi':
                    if (line.tax_ids_after_fiscal_position,order) not in taxes_group:
                        taxes_group.update({(line.tax_ids_after_fiscal_position,order):line})
                    else:
                        taxes_group[(line.tax_ids_after_fiscal_position,order)] +=line
                else:
                    if (line.tax_ids_after_fiscal_position,self) not in taxes_group:
                        taxes_group.update({(line.tax_ids_after_fiscal_position,self):line})
                    else:
                        taxes_group[(line.tax_ids_after_fiscal_position,self)] +=line

                invoice_line_vals = order.with_context(local_context)._prepare_invoice_line(line)
                move_lines.append((0,0,invoice_line_vals))
            if order.pos_reference:
                note += '%s, %s;' % (order.pos_reference.replace('Pedido ',''), order.amount_total)
            else:
                note += '%s;' % (order.amount_total)
            origin.append(order_name)

            #if order.account_move:
            #    order.account_move.write({'partner_id': partner.id})
            #    order.account_move.line_ids.write({'partner_id': partner.id})
            #for line in order.session_id.statement_line_ids:
            #    line.move_line_ids.write({'partner_id':partner.id})
            orders += order

        if taxes_group:
            inv = {
                'source_document': ', '.join(origin),
                'journal_id': sale_journal and sale_journal.id or None,
                'partner_id': partner.id,
              #  'currency_id': self[0].pricelist_id.currency_id.id,
                'company_id': company_id,
                'activity_user_id': self.env.uid,
                'invoice_date':datetime.today(),
                'forma_pago_id': self.env['catalogo.forma.pago'].sudo().search([('code','=','01')], limit=1).id,
                'methodo_pago': 'PUE',
                'uso_cfdi_id': self.env['catalogo.uso.cfdi'].sudo().search([('code','=','S01')], limit=1).id,
                'tipo_comprobante': 'I',
                }

            #invoice = factura.new(inv)
            invoice_line_dict=[]
            for order_taxes, order_lines in taxes_group.items():
                taxes = order_taxes[0]
                price_unit = 0.0
                for line in order_lines:
                    if line.discount:
                        price_unit += (line.price_unit * (1 - (line.discount or 0.0) / 100.0))*line.qty
                    else:
                        price_unit += line.price_unit*line.qty

                if order_taxes[1]:
                    if order_taxes[1][0].pos_reference:
                        if self.env['ir.config_parameter'].sudo().get_param('custom_invoice.fg_code'):
                           order_name = order_taxes[1].ticket_code
                        else:
                           order_name = order_taxes[1].name
                        inv_line_name = (invoice_format == 'cfdi') and '[%s] %s' % (order_name, product_total.name) or  product_total.name
                    else:
                        if self.env['ir.config_parameter'].sudo().get_param('custom_invoice.fg_code'):
                           order_name = order_taxes[1][0].ticket_code
                        else:
                           order_name = order_taxes[1][0].name
                        inv_line_name = (invoice_format == 'cfdi') and '[%s] %s' % (order_name, product_total.name) or  product_total.name
                inv_line = {
                    'product_id': product_total.id,
                    'price_unit': price_unit,
                    'quantity': 1,
                    'name': inv_line_name,

                }

                taxes_new=[]
                for tax in taxes:
                    taxes_new.append(tax.id)

                inv_line.update({'price_unit': price_unit,'name': inv_line_name})
                inv_line.update({'invoice_line_tax_ids': [(6,0,taxes_new)]})
                invoice_line_dict.append((0, 0,inv_line))

            inv.update({'factura_line_ids': invoice_line_dict})
            invoice = factura.with_context(local_context).sudo().create(inv)
            inv_ids.append(invoice)

            orders.sudo().write({'state': 'invoiced', 'factura_global_id': invoice.id})

        fg_nc_create = self.env['ir.config_parameter'].sudo().get_param('custom_invoice.fg_nc_create')
        if fg_nc_create:
           self.action_check_nota_credito(partner)

        if not inv_ids: return {}

        return {
            'name': _('Factura Global'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'factura.global',
            'context': {},
            'type': 'ir.actions.act_window',
            'res_id': inv_ids[0],
        }

    def action_factura_global_compacta(self, partner_total=None):
        factura = self.env['factura.global']
        inv_ids = []
        invoices = {}
        factura_dic={}
        note = ''
        origin = []
        factura_line = []
        all_factura_line = []
        sale_journal = self[0].sale_journal

        if not partner_total:
            raise UserError(_('Falta agregar un cliente para la factura.'))

        for order in self:
            if order.refunded_orders_count > 0:
               continue
            if self.env['ir.config_parameter'].sudo().get_param('custom_invoice.fg_code'):
               order_name = order.ticket_code
            else:
               order_name = order.name
            for line in order.lines:
                if not all_factura_line:
                    all_factura_line.append(order._prepare_invoice_line(line))
                else:
                    is_add=True;
                    for data in all_factura_line:
                        if data.get('product_id') == line.product_id.id and data.get('tax_ids')[0][2]==line.tax_ids_after_fiscal_position.ids:
                            data['quantity']= data['quantity']+line.qty
                            is_add=False
                    if is_add:
                        all_factura_line.append(order._prepare_invoice_line(line))
            origin.append(order_name)

        for data in all_factura_line:
            if 'tax_ids' in data:
                data['invoice_line_tax_ids'] = data.get('tax_ids')
                data.pop('tax_ids')
                data.pop('product_uom_id')

        for line in all_factura_line:
            factura_line.append((0, 0,line))

        for order in self:
            if order.refunded_orders_count > 0 or order.refund_orders_count > 0:
               continue
            company_id = order.company_id.id
            local_context = dict(self._context.copy() or {}, force_company=company_id, company_id=company_id)
            if order.factura_global_id:
                inv_ids.append(order.factura_global_id)
                continue

            if partner_total and not self.env['ir.config_parameter'].sudo().get_param('custom_invoice.fg_client'):
                order.write({'partner_id': partner_total.id})

            if self.env['ir.config_parameter'].sudo().get_param('custom_invoice.fg_code'):
               order_name = order.ticket_code
            else:
               order_name = order.name

            if order.pos_reference:
                note += '%s, %s;' % (order.pos_reference.replace('Pedido ',''), order.amount_total)
            else:
                note += '%s;' % (order.amount_total)
            origin.append(order_name)

            partner = partner_total
            group_key = partner.id

            factura_dic.update({
                        'forma_pago_id': self.env['catalogo.forma.pago'].sudo().search([('code','=','01')], limit=1).id,
                        'methodo_pago': 'PUE',
                        'journal_id': sale_journal and sale_journal.id or None,
                        'tipo_comprobante': 'I',
                        'factura_cfdi': False,
                        'partner_id': partner.id,
                        'invoice_date': datetime.today(),
                        'factura_line_ids': factura_line,
                        'source_document': order_name,
                        })

            if group_key not in invoices:
                new_invoice = factura.with_context(local_context).sudo().create(factura_dic)
                order.write({'factura_global_id': new_invoice.id, 'state': 'invoiced'})
                invoices[group_key] = new_invoice.id
                factura += new_invoice
            elif group_key in invoices:
                invoice_obj = factura.with_context(local_context).browse(invoices[group_key])
                order.write({'factura_global_id': invoice_obj.id, 'state': 'invoiced'})
                if invoice_obj.source_document:
                    if order_name not in invoice_obj.source_document.split(', '):
                        invoice_obj.write({'source_document': invoice_obj.source_document + ', ' + order_name})
                else:
                    invoice_obj.write({'source_document': order_name})
            order.sudo().write({'state': 'invoiced'})

        fg_nc_create = self.env['ir.config_parameter'].sudo().get_param('custom_invoice.fg_nc_create')
        if fg_nc_create:
           self.action_check_nota_credito(partner_total)

        if not inv_ids:
            return {}

        return {
            'name': _('Factura Global'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'factura.global',
            'context': {},
            'type': 'ir.actions.act_window',
            'res_id': inv_ids[0],
        }

    def action_check_nota_credito(self, partner_total=None):
        factura = self.env['factura.global']
        factura_dic={}
        invoices = {}
        sale_journal = self[0].sale_journal
        note = ''
        for order in self:
            if not order.refunded_orders_count > 0:
                continue

            local_context = dict(self.env.context, force_company=order.company_id.id, company_id=order.company_id.id)
            if order.factura_global_id:
                factura += order.factura_global_id
                continue

            if not order.partner_id and not partner_total:
                raise UserError(_('Falta agregar un cliente para la factura.'))
            if partner_total and not self.env['ir.config_parameter'].sudo().get_param('custom_invoice.fg_client'):
                order.write({'partner_id': partner_total.id})

            if self.env['ir.config_parameter'].sudo().get_param('custom_invoice.fg_code'):
               order_name = order.ticket_code
            else:
               order_name = order.name

            partner = order.partner_id
            note += '%s, %s;' % (order.pos_reference, order.amount_total)
            group_key = partner_total.id
            factura_line = []
            for line in order.lines:
                factura_line.append((0,0,{'product_id':line.product_id.id,
                                     'name':line.product_id.partner_ref,
                                     'price_unit':line.price_unit,
                                     'quantity': abs(line.qty),
                                     'discount': line.discount,
                                     'invoice_line_tax_ids': [(6, 0, line.tax_ids.ids)]
                                     }))
            factura_dic.update({
                                'partner_id': partner_total.id,
                                'invoice_date': datetime.today(),
                                'factura_line_ids': factura_line,
                                'source_document': order_name,
                                'forma_pago_id': self.env['catalogo.forma.pago'].sudo().search([('code','=','01')]).id,
                                'methodo_pago': 'PUE',
                                'journal_id': sale_journal and sale_journal.id or None,
                                'tipo_comprobante': 'E',
                                })
            if group_key not in invoices:
                new_invoice = factura.with_context(local_context).sudo().create(factura_dic)
                order.write({'factura_global_id': new_invoice.id, 'state': 'invoiced'})
                invoices[group_key] = new_invoice.id
                factura += new_invoice
            elif group_key in invoices:
                invoice_obj = factura.with_context(local_context).browse(invoices[group_key])
                order.write({'factura_global_id': invoice_obj.id, 'state': 'invoiced'})
                if invoice_obj.source_document:
                    if order_name not in invoice_obj.source_document.split(', '):
                        invoice_obj.write({'source_document': invoice_obj.source_document + ', ' + order_name})
                else:
                    invoice_obj.write({'source_document': order_name})
                new_invoice.write({'factura_line_ids':factura_line})
            order.sudo().write({'state': 'invoiced'})

#    def _process_payment_lines(self, pos_order, order, pos_session, draft):
#        """Create account.bank.statement.lines from the dictionary given to the parent function.

#        If the payment_line is an updated version of an existing one, the existing payment_line will first be
#        removed before making a new one.
#        :param pos_order: dictionary representing the order.
#        :type pos_order: dict.
#        :param order: Order object the payment lines should belong to.
#        :type order: pos.order
#        :param pos_session: PoS session the order was created in.
#        :type pos_session: pos.session
#        :param draft: Indicate that the pos_order is not validated yet.
#        :type draft: bool.
#        """
#        prec_acc = order.pricelist_id.currency_id.decimal_places

#        order_bank_statement_lines= self.env['pos.payment'].search([('pos_order_id', '=', order.id)])
#        order_bank_statement_lines.unlink()
#        for payments in pos_order['statement_ids']:
#            if not float_is_zero(payments[2]['amount'], precision_digits=prec_acc):
#                order.add_payment(self._payment_fields(order, payments[2]))

#        order.amount_paid = sum(order.payment_ids.mapped('amount'))

#        if not draft and not float_is_zero(pos_order['amount_return'], prec_acc):
#            cash_payment_method = pos_session.payment_method_ids.filtered('is_cash_count')[:1]

            #Add By Nilesh
#            if order.amount_total==-pos_order['amount_return'] and pos_order.get('payment_line_journals'):
#                jurnal_ids = list(pos_order.get('payment_line_journals').keys())
#                if jurnal_ids:
#                    cash_payment_method = self.env['pos.payment.method'].browse(int(jurnal_ids[0]))
            #Add Over

#            if not cash_payment_method:
#                raise UserError(_("No cash statement found for this session. Unable to record returned cash."))
#            return_payment_vals = {
#                'name': _('return'),
#                'pos_order_id': order.id,
#                'amount': -pos_order['amount_return'],
#                'payment_date': fields.Datetime.now(),
#                'payment_method_id': cash_payment_method.id,
#            }
#            order.add_payment(return_payment_vals)

    def _prepare_invoice_vals_new(self,order_lines):
        self.ensure_one()
        vals = {

            'journal_id': self.session_id.config_id.invoice_journal_id.id,
            'move_type': 'out_invoice' if self.amount_total >= 0 else 'out_refund',
            'ref': self.name,
            'partner_id': self.partner_id.id,
            'narration': self.note or '',
            'currency_id': self.pricelist_id.currency_id.id,
            'invoice_user_id': self.user_id.id,
            'invoice_date': self.date_order.date(),
            'fiscal_position_id': self.fiscal_position_id.id,
            'invoice_line_ids': order_lines,
        }
        return vals

    def _prepare_invoice_line(self, order_line):
        #apply customer language on invoice
        name = order_line.product_id.with_context(lang=order_line.order_id.partner_id.lang or self.env.user.lang).get_product_multiline_description_sale()
        return {
            'product_id': order_line.product_id.id,
            'quantity': order_line.qty if self.amount_total >= 0 else -order_line.qty,
            'discount': order_line.discount,
            'price_unit': order_line.price_unit,
            'name': name,
            'tax_ids': [(6, 0, order_line.tax_ids_after_fiscal_position.ids)],
            'product_uom_id': order_line.product_uom_id.id,
        }

    def action_view_factura_global(self):
        return {
            'name': _('Factura global'),
            'view_mode': 'form',
            'view_id': self.env.ref('custom_invoice.view_fatura_global_form').id,
            'res_model': 'factura.global',
           # 'context': "{'move_type':'out_invoice'}",
            'type': 'ir.actions.act_window',
            'res_id': self.factura_global_id.id,
        }

class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    forma_pago_id  =  fields.Many2one('catalogo.forma.pago', string='Forma de pago')
    methodo_pago = fields.Selection(
        selection=[('PUE', _('Pago en una sola exhibición')),
                   ('PPD', _('Pago en parcialidades o diferido')),
                  ],
        string=_('Método de pago'),
    )
