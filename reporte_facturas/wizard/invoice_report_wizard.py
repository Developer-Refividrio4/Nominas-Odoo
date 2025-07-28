# -*- coding: utf-8 -*-

from odoo import fields, models, api
from datetime import datetime, timedelta

class XlsInvoiceReport(models.Model):
    _name = "xls.invoice.report"
    _description = "Invoice Report"

    date_from = fields.Date(string='Periodo', required=True)
    date_to = fields.Date(string='Al', required=True)
    no_result = fields.Boolean(string='No Result', default=False)
    invoice_ids = fields.Char(string='Invoice IDs', readonly=True)

    def print_xls_report(self, context=None):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'xls.invoice.report'
        datas['form'] = self.read()[0]
        return self.env.ref('reporte_facturas.report_invoice_xls').report_action(self, data=datas)

    def print_report(self):
        self.ensure_one()
        datas = {
            'ids': [],
            'model': 'account.move',
            'form': self.read()[0]
        }
        self = self.with_context({'active_model': self._name, 'active_ids': self.ids})
        return self.env.ref('reporte_facturas.report_invoice_total').with_context(
            {'active_model': self._name, 'active_ids': self.ids}).report_action(self, data=datas)
