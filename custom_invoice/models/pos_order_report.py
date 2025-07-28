# -*- coding: utf-8 -*-

from odoo import fields, models

class PosOrderReport(models.Model):
    _inherit = "report.pos.order"
    _description = "Point of Sale Orders Statistics"
    _order = 'date desc'

    payment_method_id = fields.Many2one('account.journal', string='Payment Method', readonly=True)
    
    def _select(self):
        return super(PosOrderReport, self)._select() + ", s.main_journal_id AS payment_method_id"

    def _group_by(self):
        return super(PosOrderReport, self)._group_by() + ", s.main_journal_id"
