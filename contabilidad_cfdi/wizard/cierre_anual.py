# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime
from datetime import date
import logging
_logger = logging.getLogger(__name__)

class CierreAnual(models.TransientModel):
    _name = 'cierre.anual'
    
    cuenta_de_resultados = fields.Many2one('account.account', string='Cuenta de resultados')
    ano = fields.Selection([('2025','2025'),('2024','2024'),('2023','2023'),('2022','2022'),('2021','2021')], string='Ano')
    journal_id = fields.Many2one('account.journal',string='Diario')

    def validar_cierre_anual(self):
        journal_entries = self.env['account.move'].search([('state', '=', 'posted'), ('contabilidad_electronica', '=', True)])
        lines_dict = {}
        for journal in journal_entries:
            if journal.date.year == int(self.ano):
                for line in journal.line_ids:
                    if line.account_id.account_type in ['income','income_other','expense','expense_depreciation','expense_direct_cost']:
                        if line.account_id.id in lines_dict.keys():
                            total = lines_dict[line.account_id.id] + line.balance
                            lines_dict[line.account_id.id] = total
                        else:
                            lines_dict.update({line.account_id.id:line.balance})
                
        lines_list = []
        debit_total = 0.0
        credit_total = 0.0
        for key,val in lines_dict.items():
            line_val = {'account_id':key}
            if val > 0:
                line_val.update({'credit': -val, 'balance': -val})
                credit_total += (val)
                #_logger.info('cuenta %s -- credito -- monto %s', key, -val)
            else:
                line_val.update({'debit': -val, 'balance': -val})
                debit_total += (-val)
                #_logger.info('cuenta %s -- debito -- monto %s', key, -val)

            lines_list.append((0,0,line_val))

        new_total = credit_total - debit_total
        #_logger.info('debito %s -- credito %s -- new_total %s', debit_total, credit_total, new_total)

        if debit_total > credit_total:
            lines_list.append((0,0,{'account_id': self.cuenta_de_resultados.id, 'credit': new_total, 'balance': new_total}))
        else:
            lines_list.append((0,0,{'account_id': self.cuenta_de_resultados.id, 'debit': new_total, 'balance': new_total}))

        values = {'line_ids': lines_list, 'journal_id': self.journal_id.id, 'ref': 'Cierre anual', 'cierre_anual': True, 'date': date(int(self.ano), 12, 31)}

        new_journal = self.env['account.move'].create(values)
