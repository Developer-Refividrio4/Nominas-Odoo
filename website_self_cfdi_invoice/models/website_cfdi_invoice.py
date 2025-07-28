# -*- coding: utf-8 -*-

from odoo import models, fields, api, SUPERUSER_ID
import base64
import time
import logging
_logger = logging.getLogger(__name__)
from datetime import date, timedelta
import datetime

class account_invoice(models.Model):
    _name = 'account.move'
    _inherit = 'account.move'

    def invoice_validate(self):
        res = super(account_invoice, self).invoice_validate()
        for invoice in self:
            self.env.cr.execute("delete from ir_attachment where name like 'Invoice_%s' and res_id = %s and res_model='account.move';" % ('%',invoice.id,))
        return res

class website_self_invoice_web(models.Model):
    _name = 'website.self.invoice.web'
    _description = 'Portal de Autofacturacion Integrado a Odoo'
    _rec_name = 'order_number'
    _order = 'create_date desc'

    datas_fname = fields.Char('File Name', size=256)
    file = fields.Binary('Layout')
    download_file = fields.Boolean('Descargar Archivo')
    cadena_decoding = fields.Text('Binario sin encoding')
    type = fields.Selection([('csv', 'CSV'), ('xlsx', 'Excel')], 'Tipo Exportacion',
                            required=False, )
    rfc_partner = fields.Char('RFC', size=15)
    order_number = fields.Char('Folio Pedido de Venta', size=128)
    monto_total = fields.Float('Monto total')
    mail_to = fields.Char('Correo Electronico', size=256)
    ticket_pos = fields.Boolean('Ticket', default=False)
    state = fields.Selection([('draft', 'Borrador'), ('error', 'Error'), ('done', 'Relizado')])

    attachment_ids = fields.One2many('website.self.invoice.web.attach','website_auto_id','Adjuntos del Portal')
    
    error_message = fields.Text('Mensaje de Error')
    partner_id = fields.Many2one('res.partner', string="Cliente interno")
    uso_cfdi = fields.Char('Uso de CFDI')

    _defaults = {
        'download_file': False,
        'type': 'csv',
        'state': 'draft',
    }

    def website_form_input_filter(self, request, values):
        values['medium_id'] = (
                values.get('medium_id') or
                self.default_get(['medium_id']).get('medium_id') or
                self.sudo().env['ir.model.data'].xmlid_to_res_id('utm.utm_medium_website')
        )
        return values

    def cfdi_get_invoice_lines(self, line_values):
        return {
            'product_id': line_values.product_id.id,
            'quantity': line_values.qty,
            'discount':  line_values.discount,
            'price_unit': line_values.price_unit,
            'name': line_values.name,
            'tax_ids': [(6, 0, line_values.tax_ids_after_fiscal_position.ids)],
            'product_uom_id': line_values.product_uom_id.id,
        }

    def write(self, values):
        result = super(website_self_invoice_web, self).write(values)
        return result

    @api.model
    def create(self, values):
        result = super(website_self_invoice_web, self).create(values)
        ### Validacion de Campos Obligatorios ###
        if not result.rfc_partner or not result.order_number or not result.monto_total:
            result.write({
                'error_message': 'Los campos Marcados con un ( * ) son Obligatorios.',
                'state': 'error',
            })
            return result
        if not result.partner_id:
            self.env.cr.execute("""
                select id from res_partner where UPPER(vat) like %s;
                """, ('%' + result.rfc_partner.upper() + '%',))
            cr_res = self.env.cr.fetchall()
            order_id = False

            try:
                partner_id = cr_res[0][0]
            except:
                result.write({
                    'error_message': 'El RFC %s no existe en la Base de Datos.' % result.rfc_partner,
                    'state': 'error',
                })
                return result
        else:
            partner_id = result.partner_id.id
        ##### Retornamos  la Factura en caso que exista ####
        self.env.cr.execute("""
                select id from sale_order where UPPER(name)=%s and round(amount_total,2)=%s;
                """, (result.order_number.upper(),result.monto_total or 0))
        cr_res = self.env.cr.fetchall()
        ticket_pos = False
        try:
            order_id = cr_res[0][0]
            ticket_pos = False
        except:
            enable_pos = False
            module = self.env['ir.module.module'].sudo().search([('name','=','custom_invoice')])
            if module and module.state == 'installed':
                enable_pos = True
            if enable_pos:
                self.env.cr.execute("""
                    select id from pos_order where pos_reference like %s and round(amount_total,2)=%s;
                    """, ('%'+result.order_number,result.monto_total or 0))
                cr_res = self.env.cr.fetchall()
                if not cr_res:
                    self.env.cr.execute("""
                         select id from pos_order where ticket_code like %s and round(amount_total,2)=%s;
                         """, ('%'+result.order_number,result.monto_total or 0))
                    cr_res = self.env.cr.fetchall()
                try:
                    order_id = cr_res[0][0]
                    ticket_pos = True
                except:
                    result.write({
                        'error_message':'El Ticket %s no existe en la Base de Datos.' % result.order_number,
                        'state': 'error',
                    })
                    return result
            else:
                result.write({
                        'error_message':'El Pedido %s no existe en la Base de Datos.' % result.order_number,
                        'state': 'error',
                })
                return result

        tryagain = False
        if order_id and ticket_pos == False:
            order_obj = self.env['sale.order'].sudo()
            order_br = order_obj.browse(order_id)
            if order_br.state in ('draft','sent'):
                result.write({
                            'error_message':'El Pedido %s se encuentra en espera de ser procesado, por favor comuniquese con la compañia.' % order_br.name,
                            'state': 'error',
                        })
                return result

            if order_br.invoice_status != 'no':
                invoice_return = None
                if order_br.invoice_status == 'invoiced':
                    invoice_return = order_br.invoice_ids.filtered(lambda r: r.state != 'cancel')
                    if invoice_return and invoice_return[0].estado_factura in['factura_correcta', 'factura_cancelada']:
                        result.write({
                            'error_message': 'El Pedido %s ya fue Facturado.' % result.order_number,
                            'state': 'error',
                        })
                        return result
                else:
                    if not result.uso_cfdi:
                        result.write({
                           'error_message':'No tiene asignado un USO DE CFDI en su cuenta de usuario. Favor de asignar uno antes de facturar el pedido %s.' % order_br.name,
                           'state': 'error',
                        })
                        return result
                    if not order_br.forma_pago_id:
                        result.write({
                               'error_message':'El pedido %s no pudo facturarse ya que no cuenta con una forma de pago asignada, comuniquese con la compañia.' % order_br.name,
                               'state': 'error',
                        })
                        return result
                    if not order_br.methodo_pago:
                        result.write({
                               'error_message':'El pedido %s no pudo facturarse ya que no cuenta con un método de pago asignado, comuniquese con la compañia.' % order_br.name,
                               'state': 'error',
                        })
                        return result
                    invoice_return = order_br._create_invoices()
                invoice_br = self.env['account.move'].sudo().search([('id','=',invoice_return.id)])
                vals = {}
                vals.update({'partner_id': result.partner_id})
                if not invoice_br.tipo_comprobante:
                  vals.update({'tipo_comprobante': 'I'})
                vals.update({'uso_cfdi_id': self.env['catalogo.uso.cfdi'].sudo().search([('code','=',result.uso_cfdi)]).id })
                if not invoice_br.forma_pago_id:
                    vals.update({'forma_pago_id': order_br.forma_pago_id.id })
                if not invoice_br.methodo_pago:
                    vals.update({'methodo_pago': order_br.methodo_pago})
                vals.update({'fecha_factura': (datetime.datetime.now() - timedelta(hours=6))})
                invoice_br.write(vals)

                if invoice_br.state == 'draft':
                    invoice_br.sudo().action_post()

                try:
                    invoice_br.sudo().action_cfdi_generate()
                except:
                    result.write({
                        'error_message':'El pedido %s no se pudo timbrar correctamente, favor de contactar al departamento de facturación para asistirlo.' % result.order_number,
                        'state': 'error',
                    })
                    return result

                if invoice_br.estado_factura != 'factura_correcta':
                    result.write({
                        'error_message': 'El pedido %s no se pudo timbrar correctamente, favor de contactar al departamento de facturación para asistirlo.' % result.order_number,
                        'state': 'error',
                    })
                    return result

                ir_attach = self.env['ir.attachment'].sudo()
                attachment_ids = ir_attach.search([('res_model','=','account.move'),('res_id','=',invoice_br.id)])
                Attachment = self.env['ir.attachment'].sudo()

                if not attachment_ids.filtered(lambda x: '.pdf' in x.store_fname or '.pdf' in x.name):
                     report = self.env['ir.actions.report'].with_user(SUPERUSER_ID)._render_qweb_pdf("account.account_invoices", invoice_br.id)[0]
                     report = base64.b64encode(report)
                     fname =  'CDFI_' + invoice_br.name.replace('/', '_') + '.pdf'
                     attachment_data = {
                            'name': fname,
                            'store_fname': fname,
                            'type': 'binary',
                            'datas': report,
                            'res_model': 'account.move',
                            'res_id': invoice_br.id,
                        }
                     attachment_ids += Attachment.create(attachment_data)
                if not attachment_ids.filtered(lambda x: '.xml' in x.store_fname or '.xml' in x.name):
                     xml_file = open(invoice_br.xml_invoice_link, 'rb').read()
                     fname_xml = 'CDFI_' + invoice_br.name.replace('/', '_') + '.xml'
                     attachment_xml = {
                             'name': fname_xml,
                             'store_fname': fname_xml,
                             'type': 'binary',
                             'datas': base64.b64encode(xml_file),
                             'res_model': 'account.move',
                             'res_id': invoice_br.id,
                     }
                     attachment_ids += Attachment.create(attachment_xml)

                if attachment_ids:
                     attachment_web =[]
                     for attach in attachment_ids:
                            xval = (0,0,{'attach_id': attach.id,})
                            attachment_web.append(xval)
                     result.write({'attachment_ids':attachment_web})
                result.write({'state':'done'})

                email_template = self.env.ref("account.account_invoice_send_wizard_form",False)
                if email_template:
                    emails = invoice_br.partner_id.email.split(",")
                    for email in emails:
                        email = email.strip()
                        if email:
                           email_template.send_mail(invoice_br.id, force_send=True,email_values={'email_to':email})
            else:
                result.write({
                            'error_message':'El Pedido %s ya fue Facturado.' % result.order_number,
                            'state': 'error',
                        })
                return result
        if order_id and ticket_pos == True:
            invoice_obj = self.env['account.move'].sudo()
            pos_order_obj = self.env['pos.order'].sudo()
            pos_br = pos_order_obj.browse(order_id)
            pos_br.write({'partner_id':partner_id})
            if pos_br.partner_id:
                if pos_br.partner_id.id != partner_id:
                    result.write({
                                'error_message':'El RFC %s no pertenece al Pedido de Venta %s.' % (result.rfc_partner,result.order_number,),
                                'state': 'error',
                            }) 
                    return result
            if pos_br.state != 'cancel' and pos_br.state != 'draft':
               #revisa la factura global
               factglob_return = self.env['factura.global'].sudo().search([('source_document', '=', pos_br.name), ('state', '!=', 'cancel')], limit=1)
               if factglob_return and factglob_return.state == 'valid':
                   invoice_br = factglob_return
                   tryagain = True

               if pos_br.state == 'invoiced' and not tryagain:
                   result.write({
                                'error_message':'El ticket %s ya fue facturado previamente.' % (result.order_number,),
                                'state': 'error',
                            }) 
                   return result

               if not result.uso_cfdi:
                        result.write({
                           'error_message':'No tiene asignado un USO DE CFDI en su cuenta de usuario. Favor de asignar uno antes de facturar el pedido %s.' % order_br.name,
                           'state': 'error',
                        })
                        return result

               if not tryagain: # create new document type "factura global"
                    facture_obj=self.env['factura.global'].sudo()
                    pos_order=self.env['pos.order'].sudo().browse(order_id)
                    lines=[]
                    for line in pos_order.lines:
                        lines.append((0,0,{'product_id':line.product_id.id,'name':line.product_id.name,'quantity':line.qty,'price_unit':line.price_unit,
                                          'discount':line.discount,'invoice_line_tax_ids': [(6,0,line.tax_ids.ids)],'price_subtotal':line.price_subtotal}))
                    invoice_br = facture_obj.create({'partner_id':partner_id,
                                                     'invoice_date':datetime.datetime.now(),
                                                     'source_document':pos_order.name,
                                                     'factura_line_ids':lines,
                                                     'company_id': pos_order.company_id.id})
                    pos_order.write({'factura_global_id': invoice_br.id, 'state': 'invoiced'})

               vals = {}
               if not invoice_br.tipo_comprobante:
                   vals.update({'tipo_comprobante': 'I'})
               vals.update({'uso_cfdi_id': self.env['catalogo.uso.cfdi'].sudo().search([('code','=',result.uso_cfdi)]).id })
               if not invoice_br.methodo_pago:
                   vals.update({'methodo_pago': "PUE"})
               vals.update({'fecha_factura': (datetime.datetime.now() - timedelta(hours=6))})
               if pos_br.payment_ids:
                   payment_method_code = pos_br.payment_ids[0].payment_method_id.forma_pago_id
                   if payment_method_code.code not in ('01', '02', '03', '04', '05', '06', '08', '28', '29'):
                       result.write({
                          'error_message':'Forma de pago desconocido %s: %s.' % (payment_method_code, pos_br.payment_ids[0].payment_method_id.name),
                          'state': 'error',
                          })
                       return result
                   vals.update({'forma_pago_id': payment_method_code.id})
               invoice_br.write(vals)

               invoice_br.sudo().action_valid()
               if invoice_br.proceso_timbrado:
                     invoice_br.write({'proceso_timbrado': False})
               invoice_br.action_cfdi_generate()

               if invoice_br.estado_factura != 'factura_correcta':
                    result.write({
                        'error_message': 'El ticket %s no se pudo timbrar correctamente, favor de contactar al departamento de facturación para asistirlo.' % result.order_number,
                        'state': 'error',
                    })
                    return result

               ir_attach = self.env['ir.attachment'].sudo()
               attachment_ids = ir_attach.search([('res_model','=','factura.global'),('res_id','=',invoice_br.id)])
               Attachment = self.env['ir.attachment'].sudo()

               if not attachment_ids.filtered(lambda x: '.pdf' in x.store_fname or '.pdf' in x.name):
                 report = self.env['ir.actions.report'].with_user(SUPERUSER_ID)._render_qweb_pdf("custom_invoice.report_facturaglobals", invoice_br.id)[0]
                 report = base64.b64encode(report)
                 fname =  'CDFI_' + invoice_br.number.replace('/', '_') + '.pdf'
                 attachment_data = {
                            'name': fname,
                            'store_fname': fname,
                            'datas': report,
                            'type': 'binary',
                            'res_model': 'factura.global',
                            'res_id': invoice_br.id,
                        }
                 attachment_ids += Attachment.create(attachment_data)

               if attachment_ids:
                   attachment_web =[]
                   for attach in attachment_ids:
                       xval = (0,0,{'attach_id': attach.id,})
                       attachment_web.append(xval)
                   result.write({'attachment_ids':attachment_web})
                   result.write({'state':'done'})
                   email_template = self.env.ref("custom_invoice.email_template_factura_global",False)
                   if email_template:
                       email_template.attachment_ids = None
                       domain = [
                             ('res_id', '=', invoice_br.id),
                             ('res_model', '=', invoice_br._name),
                             ('name', '=', invoice_br.number.replace('/', '_') + '.xml')]
                       xml_file = self.env['ir.attachment'].search(domain, limit=1)
                       if xml_file:
                          new_xml_file = xml_file.copy()
                          email_template.attachment_ids = [(4, new_xml_file.id)]
                       emails = pos_br.partner_id.email.split(",")
                       for email in emails:
                          email = email.strip()
                          if email:
                             email_template.send_mail(invoice_br.id, force_send=True,email_values={'email_to':email})
                       email_template.attachment_ids = None
            else:
                result.write({
                            'error_message':'El Ticket %s no se puede facturar, favor de contactar al departamento de facturación.' % result.order_number,
                            'state': 'error',
                        })
                return result

        return result

class website_self_invoice_web_attach(models.Model):
    _name = 'website.self.invoice.web.attach'
    _description = 'Adjuntos para Portal de Auto Facturacion'

    website_auto_id = fields.Many2one('website.self.invoice.web', 'ID Ref')
    attach_id = fields.Many2one('ir.attachment', 'Adjunto')
    store_fname = fields.Char('File Name', size=256, related="attach_id.store_fname")
    file = fields.Binary('Archivo Binario', related="attach_id.datas")
    file_name = fields.Char('File Name', related="attach_id.name")
