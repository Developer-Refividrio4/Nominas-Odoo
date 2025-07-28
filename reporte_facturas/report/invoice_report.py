# -*- encoding: utf-8 -*-

import time
from datetime import datetime
from dateutil import relativedelta
from odoo import models, api
from odoo import fields, models, api,_ 

#from odoo.report import report_sxw


class cantu_invoice_report(models.AbstractModel):
    _name = 'report.reporte_facturas.report_invoice_report'

    sub_total = fields.Float()
    total = fields.Float()
    taxes = fields.Float()

    @api.model
    def _get_report_values(self, docids, data=None):

        #self.model = self.env.context.get('active_model')
        model = self._context.get('active_model', False)
        docs = self.env[model].browse(self.env.context.get('active_ids', []))

        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'get_lines': self._get_lines,
            'get_sub_total': self.get_sub_total,
            'get_total': self.get_total,
            'get_taxes': self.get_taxes,
            #'get_currency': self.get_currency,
        }

    def set_context(self, objects, data, ids, report_type=None):
        self.date_from = data['form'].get('date_from', time.strftime('%Y-%m-%d'))
        self.date_to = data['form'].get('date_to', str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10])
        return super(cantu_invoice_report, self).set_context(objects, data, ids, report_type=report_type)

    #def get_currency(self):
    #    return self.currency
    
    def get_sub_total(self):
        return self.sub_total
    
    def get_total(self):
        return self.total
    
    def get_taxes(self):
        return self.taxes

    def _get_lines(self, obj):
        invoice_obj = obj.env['account.move']
        invoice_ids = invoice_obj.search([
                                                             ('move_type', '=', 'out_invoice'),
                                                             ('state', '!=', 'draft'),
                                                      #       ('estado_factura', '!=', 'factura_cancelada'),
                                                             ('invoice_date', '>=', obj.date_from), 
                                                             ('invoice_date', '<=', obj.date_to)], order='invoice_date asc')
        #print 'invoices: cantu_invoice_report ', invoice_ids
        #invoices = invoice_obj.browse(invoice_ids)
        self.sub_total = 0
        self.total = 0
        self.taxes = []
        taxes_dict = {}
        for inv in invoice_ids:
            #self.currency = inv.currency_id
            if inv.estado_factura != 'factura_cancelada' and inv.state != 'cancel':
                self.sub_total += inv.amount_untaxed
                self.total += inv.amount_total
                for tax in inv.invoice_line_ids.tax_ids:
                    if tax.name in taxes_dict:
                        taxes_dict[tax.name] += tax.amount
                    else:
                        taxes_dict[tax.name] = tax.amount
        #for tax in   taxes_dict:
        #    self.taxes.append({'name': tax, 'amount': taxes_dict[tax]})
        return invoice_ids


# class wrapped_cantu_invoice_report(osv.AbstractModel):
#     _name = 'report.reporte_facturas.report_invoice_report'
#     _inherit = 'report.abstract_report'
#     _template = 'reporte_facturas.report_invoice_report'
#     _wrapped_report_class = cantu_invoice_report
