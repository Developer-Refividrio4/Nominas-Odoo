# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class CerateInvoiceTotalWizard(models.TransientModel):

    _name = 'create.invoice.total.wizard'

    invoice_format = fields.Selection(selection=[('detailed', 'Detallada'), ('one', 'Una partida'), ('cfdi', 'CFDI'), ('compacta','Compacta')], 
                                      string='Facturar en forma', required=True, default='detailed')
    partner_id = fields.Many2one('res.partner', string=_('Cliente'))
    product_id = fields.Many2one('product.product', string=_('Artículo general'))
    order_num = fields.Integer(string=_('No. de pedidos'), readonly=True)
    total = fields.Float(string=_('Total'), readonly=True)
    date_from = fields.Datetime(string=_('Periodo'), required=True)
    date_to = fields.Datetime(string=_('Al'), required=True)
    pos_config_id = fields.Many2many('pos.config', string=_('Punto de venta'))
    journal_id2 = fields.Many2one('pos.payment.method', string=_('Método de pago'))
    oreder_ids = fields.Many2many('pos.order', string=_('Orders'))
    amount_max = fields.Float(string=_('Monto maximo'))

    @api.model
    def default_get(self, fields_list):
        data = super(CerateInvoiceTotalWizard, self).default_get(fields_list)
        client = self.env.ref("custom_invoice.cliente_cfdi",False)
        product = self.env.ref("custom_invoice.producto_cfdi",False)
        if client:
            data['partner_id']=client.id
        if product:
            data['product_id']=product.id
        return data

    def action_validate_invoice_total(self):
        domain = [('state', 'not in', ['cancel', 'invoiced'])]
        if self.date_from:
            domain.append(('date_order', '>=', self.date_from.strftime('%Y-%m-%d %H:%M:%S')))
        if self.date_to:
            domain.append(('date_order', '<=', self.date_to.strftime('%Y-%m-%d %H:%M:%S')))

        if self.pos_config_id:
            domain += [('config_id', '=', self.pos_config_id.ids)]
        if self.journal_id2:
            domain += [('payment_ids.payment_method_id', '=', self.journal_id2.id)]
        orders_all = self.env['pos.order'].search(domain, order='date_order asc')
        orders = []
        fg_nc_create = self.env['ir.config_parameter'].sudo().get_param('custom_invoice.fg_nc_create')
        for order in orders_all:
           if not fg_nc_create:
              if order.refunded_orders_count > 0 or order.refund_orders_count > 0:
                 continue
           orders.append(order)

        order_ids = []
        amount_total = 0.0
        if self.amount_max > 0:
            amount_max = 0.0
            for order in orders:
                amount_max += order.amount_total
                if amount_max > (self.amount_max + 50):
                    break
                order_ids.append(order.id)
                amount_total += order.amount_total
        else:
            for order in orders:
               order_ids.append(order.id)
            amount_total = sum(o.amount_total for o in orders)

        self.write({'order_num': len(order_ids), 'total': amount_total, 'oreder_ids':[(6,0,order_ids)]})
        return {'type': 'ir.actions.act_window',
                'res_model': self._name,
                'view_mode': 'form',
                'res_id': self.id,
                'target': 'new'}

    def action_create_invoice_total(self):
        orders = self.oreder_ids

        if self.invoice_format in ['one', 'cfdi']:
            orders.action_factura_global_total(product_total=self.product_id, partner_total=self.partner_id, invoice_format=self.invoice_format)
        elif self.invoice_format == 'compacta':
            orders.action_factura_global_compacta(partner_total=self.partner_id)
        else:
            orders.action_factura_global(partner_total=self.partner_id)
        return True
