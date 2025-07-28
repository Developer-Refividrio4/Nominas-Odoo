# -*- coding: utf-8 -*-
from odoo import models

class ksDynamicFinancialBase(models.Model):
    _inherit = 'ks.dynamic.financial.base'

    def get_general_ledger_hierarchy_data(self, ks_report_lines, start=False):
        updated_report_lines = {}
        any_parent = False
        for line, values in ks_report_lines.items():
            if start:
                if not 'tr_count' in values:
                    values.update({
                        'tr_count': 1
                    })
                accounts = self.env['account.account'].search([('code', '=', line)], order="code asc")
                if accounts.group_id:
                    any_parent = True
                if accounts.group_id.code_prefix_start in updated_report_lines:
                    updated_report_lines[accounts.group_id.code_prefix_start].update({
                        "initial_balance": values['initial_balance']+updated_report_lines[accounts.group_id.code_prefix_start]['initial_balance'],
                        "debit": values['debit']+updated_report_lines[accounts.group_id.code_prefix_start]['debit'],
                        "credit": values['credit']+updated_report_lines[accounts.group_id.code_prefix_start]['credit'],
                        "balance": values['balance']+updated_report_lines[accounts.group_id.code_prefix_start]['balance'],
                        "tr_count": values['tr_count']+updated_report_lines[accounts.group_id.code_prefix_start]['tr_count']+1,
                        "children": [values] + updated_report_lines[accounts.group_id.code_prefix_start]['children']
                    })
                elif accounts.group_id.code_prefix_start:
                    updated_report_lines[accounts.group_id.code_prefix_start] = {
                        "name": accounts.group_id.name,
                        "code": accounts.group_id.code_prefix_start,
                        "company_currency_id": values['company_currency_id'],
                        "company_currency_symbol": values['company_currency_symbol'],
                        "company_currency_precision": values['company_currency_precision'],
                        "company_currency_position": values['company_currency_position'],
                        "initial_balance": values['initial_balance'],
                        "debit": values['debit'],
                        "credit": values['credit'],
                        "balance": values['balance'],
                        "children": [values],
                        "tr_count": values['tr_count'] + 1
                    }
                else:
                    if 'undefined' in updated_report_lines:
                        if isinstance(values, list):
                            updated_report_lines['undefined'] += values
                        else:
                            updated_report_lines['undefined'] += [values]
                    else:
                        if isinstance(values, list):
                            updated_report_lines['undefined'] = values
                        else:
                            updated_report_lines['undefined'] = [values]
            else:
                accounts = self.env['account.group'].search([('code_prefix_start', '=', line)], order="code_prefix_start asc")
                if accounts.parent_id:
                    any_parent = True

                if accounts.parent_id.code_prefix_start in updated_report_lines:
                    updated_report_lines[accounts.parent_id.code_prefix_start].update({
                        "initial_balance": values['initial_balance']+updated_report_lines[accounts.parent_id.code_prefix_start]['initial_balance'],
                        "debit": values['debit']+updated_report_lines[accounts.parent_id.code_prefix_start]['debit'],
                        "credit": values['credit']+updated_report_lines[accounts.parent_id.code_prefix_start]['credit'],
                        "balance": values['balance']+updated_report_lines[accounts.parent_id.code_prefix_start]['balance'],
                        "tr_count": values['tr_count']+updated_report_lines[accounts.parent_id.code_prefix_start]['tr_count'] + 1,
                        "children": [values] + updated_report_lines[accounts.parent_id.code_prefix_start]['children'],
                    })
                elif accounts.parent_id.code_prefix_start:
                    updated_report_lines[accounts.parent_id.code_prefix_start] = {
                        "name": accounts.parent_id.name,
                        "code": accounts.parent_id.code_prefix_start,
                        "company_currency_id": values['company_currency_id'],
                        "company_currency_symbol": values['company_currency_symbol'],
                        "company_currency_precision": values['company_currency_precision'],
                        "company_currency_position": values['company_currency_position'],
                        "initial_balance": values['initial_balance'],
                        "debit": values['debit'],
                        "credit": values['credit'],
                        "balance": values['balance'],
                        "children": [values],
                        "tr_count": values['tr_count']+1
                    }
                else:
                    if 'undefined' in updated_report_lines:
                        if isinstance(values, list):
                            updated_report_lines['undefined'] += values
                        else:
                            updated_report_lines['undefined'] += [values]
                    else:
                        if isinstance(values, list):
                            updated_report_lines['undefined'] = values
                        else:
                            updated_report_lines['undefined'] = [values]

        if any_parent:
            return self.get_general_ledger_hierarchy_data(updated_report_lines)
        else:
            return updated_report_lines

    def get_trial_balance_hierarchy_data(self, ks_report_lines, start=False):
        updated_report_lines = {}
        any_parent = False
        debit_tag = self.env.ref('l10n_mx.tag_debit_balance_account', raise_if_not_found=False)
        credit_tag = self.env.ref('l10n_mx.tag_credit_balance_account', raise_if_not_found=False)
        for line, values in ks_report_lines.items():
            if start:
                if not 'tr_count' in values:
                    values.update({
                        'tr_count': 1
                    })
                accounts = self.env['account.account'].search([('code', '=', line)], order="code asc")
                if accounts.group_id:
                    any_parent = True
                if accounts.group_id.code_prefix_start in updated_report_lines:
                    updated_report_lines[accounts.group_id.code_prefix_start].update({
                        "initial_balance": values['initial_balance']+updated_report_lines[accounts.group_id.code_prefix_start]['initial_balance'],
                        "initial_debit": values['initial_debit']+updated_report_lines[accounts.group_id.code_prefix_start]['initial_debit'],
                        "initial_credit": values['initial_credit']+updated_report_lines[accounts.group_id.code_prefix_start]['initial_credit'],
                        "debit": values['debit']+updated_report_lines[accounts.group_id.code_prefix_start]['debit'],
                        "credit": values['credit']+updated_report_lines[accounts.group_id.code_prefix_start]['credit'],
                        "balance": values['balance']+updated_report_lines[accounts.group_id.code_prefix_start]['balance'],
                        "ending_credit": values['ending_credit']+updated_report_lines[accounts.group_id.code_prefix_start]['ending_credit'],
                        "ending_debit": values['ending_debit']+updated_report_lines[accounts.group_id.code_prefix_start]['ending_debit'],
                        "ending_balance": values['ending_balance']+updated_report_lines[accounts.group_id.code_prefix_start]['ending_balance'],
                        "tr_count": values['tr_count']+updated_report_lines[accounts.group_id.code_prefix_start]['tr_count'],
                        "children": [values] + updated_report_lines[accounts.group_id.code_prefix_start]['children']
                    })
                elif accounts.group_id.code_prefix_start:
                    natur = ''
                    if debit_tag in accounts.tag_ids:
                        natur = 'D'
                    if credit_tag in accounts.tag_ids:
                        natur = 'A'
                    updated_report_lines[accounts.group_id.code_prefix_start] = {
                        "name": accounts.group_id.name,
                        "code": accounts.group_id.code_prefix_start,
                        "company_currency_id": values['company_currency_id'],
                        "initial_balance": values['initial_balance'],
                        "initial_debit": values['initial_debit'],
                        "initial_credit": values['initial_credit'],
                        "debit": values['debit'],
                        "credit": values['credit'],
                        "balance": values['balance'],
                        "ending_credit": values['ending_credit'],
                        "ending_debit": values['ending_debit'],
                        "ending_balance": values['ending_balance'],
                        "children": [values],
                        "tr_count": values['tr_count'] + 1,
                        "natur": natur,
                    }
                else:
                    if 'undefined' in updated_report_lines:
                        if isinstance(values, list):
                            updated_report_lines['undefined'] += values
                        else:
                            updated_report_lines['undefined'] += [values]
                    else:
                        if isinstance(values, list):
                            updated_report_lines['undefined'] = values
                        else:
                            updated_report_lines['undefined'] = [values]
            else:
                accounts = self.env['account.group'].search([('code_prefix_start', '=', line)], order="code_prefix_start asc")
                if accounts.parent_id:
                    any_parent = True

                if accounts.parent_id.code_prefix_start in updated_report_lines:
                    updated_report_lines[accounts.parent_id.code_prefix_start].update({
                        "initial_balance": values['initial_balance']+updated_report_lines[accounts.parent_id.code_prefix_start]['initial_balance'],
                        "initial_debit": values['initial_debit']+updated_report_lines[accounts.parent_id.code_prefix_start]['initial_debit'],
                        "initial_credit": values['initial_credit']+updated_report_lines[accounts.parent_id.code_prefix_start]['initial_credit'],
                        "debit": values['debit']+updated_report_lines[accounts.parent_id.code_prefix_start]['debit'],
                        "credit": values['credit']+updated_report_lines[accounts.parent_id.code_prefix_start]['credit'],
                        "balance": values['balance']+updated_report_lines[accounts.parent_id.code_prefix_start]['balance'],
                        "ending_credit": values['ending_credit']+updated_report_lines[accounts.parent_id.code_prefix_start]['ending_credit'],
                        "ending_debit": values['ending_debit']+updated_report_lines[accounts.parent_id.code_prefix_start]['ending_debit'],
                        "ending_balance": values['ending_balance']+updated_report_lines[accounts.parent_id.code_prefix_start]['ending_balance'],
                        "tr_count": values['tr_count']+updated_report_lines[accounts.parent_id.code_prefix_start]['tr_count'],
                        "children": [values] + updated_report_lines[accounts.parent_id.code_prefix_start]['children']
                    })
                elif accounts.parent_id.code_prefix_start:
                    acc_acc = self.env['account.account'].search([('group_id', '=', accounts.id)], limit=1)
                    natur = ''
                    if debit_tag in acc_acc.tag_ids:
                        natur = 'D'
                    if credit_tag in acc_acc.tag_ids:
                        natur = 'A'
                    updated_report_lines[accounts.parent_id.code_prefix_start] = {
                        "name": accounts.parent_id.name,
                        "code": accounts.parent_id.code_prefix_start,
                        "company_currency_id": values['company_currency_id'],
                        "initial_balance": values['initial_balance'],
                        "initial_debit": values['initial_debit'],
                        "initial_credit": values['initial_credit'],
                        "debit": values['debit'],
                        "credit": values['credit'],
                        "balance": values['balance'],
                        "ending_credit": values['ending_credit'],
                        "ending_debit": values['ending_debit'],
                        "ending_balance": values['ending_balance'],
                        "children": [values],
                        "tr_count": values['tr_count'] + 1,
                        "natur": natur,
                    }
                else:
                    if 'undefined' in updated_report_lines:
                        if isinstance(values, list):
                            updated_report_lines['undefined'] += values
                        else:
                            updated_report_lines['undefined'] += [values]
                    else:
                        if isinstance(values, list):
                            updated_report_lines['undefined'] = values
                        else:
                            updated_report_lines['undefined'] = [values]

        if any_parent:
            return self.get_trial_balance_hierarchy_data(updated_report_lines)
        else:
            return updated_report_lines

    def ks_get_dynamic_fin_info(self, ks_df_informations,offset={}):
        res = super(ksDynamicFinancialBase, self).ks_get_dynamic_fin_info(ks_df_informations, offset)
        show_hierarchy = ks_df_informations.get('show_hierarchy') if ks_df_informations else False
        res['ks_df_informations']['show_hierarchy'] = show_hierarchy

        if show_hierarchy and self.report_name == 'Trial Balance':
            hierarchy_data = self.get_trial_balance_hierarchy_data(res['ks_report_lines'], start=True)
            if hierarchy_data:
                res['ks_report_lines'] = hierarchy_data['undefined']
                return res

        if show_hierarchy and self.report_name == 'General Ledger':
            hierarchy_data = self.get_general_ledger_hierarchy_data(res['ks_report_lines'], start=True)
            if hierarchy_data:
                res['ks_report_lines'] = hierarchy_data['undefined']
                return res
        return res

    def ks_fetch_report_account_lines(self, ks_df_informations,offset={}):
        ks_df_informations.get('ks_differ')['ks_intervals'] = sorted(ks_df_informations.get('ks_differ')['ks_intervals'], key=lambda x: x['ks_start_date'])
        return super(ksDynamicFinancialBase, self).ks_fetch_report_account_lines(ks_df_informations,offset)


    def ks_df_build_where_clause(self, ks_df_informations=False):

        if ks_df_informations:
            WHERE = '(1=1)'
            journal_domain = None
            analytics_domain = None
            analytics_tag_domain = None
            account_domain = None
            for journal in ks_df_informations.get('journals', []):
                if not journal['id'] in ('divider', 'group') and journal['selected']:
                    if not journal_domain:
                        journal_domain = 'j.id = %s' % journal['id']
                    else:
                        journal_domain += ' OR j.id = %s' % journal['id']

            if journal_domain:
                WHERE += ' AND' + '(' + journal_domain + ')'

            for account in ks_df_informations.get('account', []):
                # pass
                if not account['id'] in ('divider', 'group') and account['selected']:
                    if not account_domain:
                        account_domain = 'a.id = %s' % (account['id'])
                    else:
                        account_domain += ' OR a.id = %s' % (account['id'])

            if account_domain:
                WHERE += ' AND' + '(' + account_domain + ')'

            if ks_df_informations.get('analytic_accounts'):
                analytic_distribution_filter_conditions = []

                for ks_ana_id in ks_df_informations['analytic_accounts']:
                    i_str = str(ks_ana_id)
                    condition = f"(jsonb_exists(analytic_distribution, '{i_str}'))"
                    analytic_distribution_filter_conditions.append(condition)
                analytic_distribution_filter = ' OR '.join(analytic_distribution_filter_conditions)
                WHERE += " AND " + "(" + analytic_distribution_filter + ")"

            if ks_df_informations.get('partner_ids', []):
                WHERE += ' AND p.id IN %s' % str(tuple(ks_df_informations.get('ks_partner_ids')) + tuple([0]))

            if ks_df_informations.get('company_id', False):
                WHERE += ' AND l.company_id in %s' % str(tuple(ks_df_informations.get('company_ids')) + tuple([0]))

            if ks_df_informations.get('ks_posted_entries') and not ks_df_informations.get('ks_unposted_entries'):
                WHERE += " AND m.state = 'posted'"
            elif ks_df_informations.get('ks_unposted_entries') and not ks_df_informations.get('ks_posted_entries'):
                WHERE += " AND m.state = 'draft'"
            else:
                WHERE += " AND m.state IN ('posted', 'draft') "
            if ks_df_informations.get('show_ce'):
                WHERE += " AND m.contabilidad_electronica = True "
            return WHERE

    def _ks_get_df_informations(self, ks_earlier_informations=None):
        ks_df_informations = {
            'unfolded_lines': ks_earlier_informations and ks_earlier_informations.get('unfolded_lines') or [],
            'account_type': ks_earlier_informations and ks_earlier_informations.get(
                'account_type') or self.ks_aged_filter,
            'ks_posted_entries': ks_earlier_informations and ks_earlier_informations.get(
                'ks_posted_entries') or False,
            'ks_unposted_entries': ks_earlier_informations and ks_earlier_informations.get(
                'ks_unposted_entries') or False,
            'ks_reconciled': ks_earlier_informations and ks_earlier_informations.get(
                'ks_reconciled') or False,
            'ks_unreconciled': ks_earlier_informations and ks_earlier_informations.get(
                'ks_unreconciled') or False,
            'ks_diff_filter': ks_earlier_informations and ks_earlier_informations.get(
                'ks_diff_filter') or {'ks_diff_filter_enablity': self.ks_dif_filter_bool,
                                      'ks_debit_credit_visibility': self.ks_debit_credit,
                                      'ks_label_filter': self.ks_label_filter

                                      },
            'ks_comparison_range': self.ks_comparison_range,

            'ks_report_with_lines': ks_earlier_informations and ks_earlier_informations.get(
                'ks_report_with_lines') or False,
            'ks_journal_filter_visiblity': self.ks_journal_filter_visiblity,
            'ks_account_filter_visiblity': self.ks_account_filter_visiblity,
            'ks_partner_filter': self.ks_partner_filter,
            'ks_partner_account_type_filter': self.ks_partner_account_type_filter,
            'ks_analytic_account_visibility': self.ks_analytic_account_visibility,
            'ks_intervals': self.ks_intervals,
            'ks_differentiation': self.ks_differentiation,
            'company_id': self.env.company.id,
            'company_ids': self.env.context.get('allowed_company_ids', False) if self.env.context.get(
                'allowed_company_ids', False) else [self.env.company.id],
            'show_ce': ks_earlier_informations and ks_earlier_informations.get(
                'show_ce') or False,
        }

        if ks_earlier_informations and ks_earlier_informations.get('account_ids', False):
            ks_df_informations['account_ids'] = ks_earlier_informations.get('account_ids')

        if self.ks_date_filter:
            self.ks_construct_date_filter(ks_df_informations, ks_earlier_informations)
        if self.ks_differentiation_filter:
            self.ks_construct_differentiation_filter(ks_df_informations,
                                                     ks_earlier_informations)

        if self.ks_journals_filter:
            self.ks_construct_journal_filter(ks_df_informations, ks_earlier_informations)
            self.ks_construct_journals_by_informations(ks_df_informations,
                                                       ks_earlier_informations)

        self._ks_construct_partner_filter(ks_df_informations, ks_earlier_informations=ks_earlier_informations)
        if self.ks_analytic_filter:
            self.ks_construct_analytic_filter(ks_df_informations, ks_earlier_informations)

        if self.ks_account_filter:
            self.ks_construct_account_filter(ks_df_informations, ks_earlier_informations)
            self.ks_construct_account_by_informations(ks_df_informations,
                                                      ks_earlier_informations)

        # self.ks_construct_summary_tax_report(ks_df_informations, ks_earlier_informations)

        return ks_df_informations
