# -*- coding: utf-8 -*-
import io
from odoo import models, api, _, fields
from odoo.tools.misc import xlsxwriter
import datetime
from datetime import date
from odoo.tools import date_utils
from odoo.exceptions import ValidationError


class KsDynamicFinancialXlsxTR(models.Model):
    _inherit = 'ks.dynamic.financial.base'

    @api.model
    def ks_dynamic_tax_xlsx(self, ks_df_informations):
        if self.display_name in 'Tax Report':
            if ks_df_informations['date'].get('ks_start_date') == False and ks_df_informations['date'].get(
                    'ks_start_date') == False:
                raise ValidationError(_('No export file will get download without date.'))
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            sheet = workbook.add_worksheet(self.display_name[:31])
            lines = self.ks_process_tax_report(ks_df_informations)
            ks_company_id = self.env['res.company'].sudo().browse(ks_df_informations.get('company_id'))
            sheet.freeze_panes(4, 1)
            row_pos = 0
            row_pos_2 = 0
            format_title = workbook.add_format({
                'bold': True,
                'align': 'center',
                'font_size': 12,
                'border': False,
                'font': 'Arial',
            })
            format_header = workbook.add_format({
                'bold': True,
                'font_size': 10,
                'align': 'center',
                'font': 'Arial',
                'bottom': False
            })
            content_header = workbook.add_format({
                'bold': False,
                'font_size': 10,
                'align': 'center',
                'font': 'Arial',
            })
            content_header_date = workbook.add_format({
                'bold': False,
                'font_size': 10,
                'align': 'center',
                'font': 'Arial',
                # 'num_format': 'dd/mm/yyyy',
            })
            line_header = workbook.add_format({
                'bold': False,
                'font_size': 10,
                'align': 'right',
                'font': 'Arial',
                'bottom': True
            })
            line_header.set_num_format(
                '#,##0.' + '0' * ks_company_id.currency_id.decimal_places or 2)
            line_header_bold = workbook.add_format({
                'bold': True,
                'font_size': 10,
                'align': 'right',
                'font': 'Arial',
                'bottom': True
            })
            line_header_string = workbook.add_format({
                'bold': False,
                'font_size': 10,
                'align': 'left',
                'font': 'Arial',
                'bottom': True
            })
            line_header_string_bold = workbook.add_format({
                'bold': True,
                'font_size': 10,
                'align': 'left',
                'font': 'Arial',
                'bottom': True
            })
            # Date from
            lang = self.env.user.lang
            lang_id = self.env['res.lang'].search([('code', '=', lang)])['date_format'].replace('/', '-')
            x = date_utils.get_fiscal_year(date.today())[0]
            # x = date.today()
            y = date_utils.get_fiscal_year(date.today())[1]
            # y = date.today()
            for_start_date = ks_df_informations['date'].get('ks_start_date') if ks_df_informations['date'].get(
                'ks_start_date') else x
            for_end_date = ks_df_informations['date'].get('ks_end_date') if ks_df_informations['date'].get(
                'ks_end_date') else y
            ks_new_start_date = (datetime.datetime.strptime(
                str(for_start_date), '%Y-%m-%d').date()).strftime(lang_id)
            ks_new_end_date = (datetime.datetime.strptime(
                str(for_end_date), '%Y-%m-%d').date()).strftime(lang_id)
            if ks_df_informations['ks_diff_filter']['ks_diff_filter_enablity']:
                if not ks_df_informations['ks_differ'].get('ks_intervals'):
                    for_new_start_comp_date = date.today()
                    for_new_end_comp_date = date.today()
                    ks_new_start_comp_date = (datetime.datetime.strptime(
                        str(for_new_start_comp_date), '%Y-%m-%d').date()).strftime(
                        lang_id)
                    ks_new_end_comp_date = (datetime.datetime.strptime(
                        str(for_new_end_comp_date), '%Y-%m-%d').date()).strftime(
                        lang_id)
                else:
                    for_new_start_comp_date = ks_df_informations['ks_differ'].get('ks_intervals')[-1][
                        'ks_start_date'] if ks_df_informations['ks_differ'].get('ks_intervals')[-1][
                        'ks_start_date'] else date.today()
                    for_new_end_comp_date = ks_df_informations['ks_differ'].get('ks_intervals')[-1][
                        'ks_end_date'] if ks_df_informations['ks_differ'].get('ks_intervals')[-1][
                        'ks_end_date'] else date.today()
                    ks_new_start_comp_date = (datetime.datetime.strptime(
                        str(for_new_start_comp_date), '%Y-%m-%d').date()).strftime(
                        lang_id)
                    ks_new_end_comp_date = (datetime.datetime.strptime(
                        str(for_new_end_comp_date), '%Y-%m-%d').date()).strftime(
                        lang_id)

            if not ks_df_informations['ks_diff_filter']['ks_diff_filter_enablity']:
                if ks_df_informations['date']['ks_process'] == 'range':
                    sheet.write_string(row_pos_2, 0, _('Date From'),
                                       format_header)
                    if for_start_date:
                        sheet.write_string(row_pos_2, 1, ks_new_start_date,
                                           content_header_date)
                    row_pos_2 += 1
                    # Date to
                    sheet.write_string(row_pos_2, 0, _('Date To'),
                                       format_header)

                    if for_end_date:
                        sheet.write_string(row_pos_2, 1, ks_new_end_date,
                                           content_header_date)
                else:
                    sheet.write_string(row_pos_2, 0, _('As of Date'),
                                       format_header)
                    if for_end_date:
                        sheet.write_string(row_pos_2, 1, ks_new_end_date,
                                           content_header_date)

            if ks_df_informations['ks_diff_filter']['ks_diff_filter_enablity']:
                sheet.write_string(row_pos_2, 0, _('Comparison Date From'),
                                   format_header)
                sheet.write_string(row_pos_2, 1, ks_new_start_comp_date,
                                   content_header_date)
                row_pos_2 += 1
                # Date to
                sheet.write_string(row_pos_2, 0, _('Comparison Date To'),
                                   format_header)

                sheet.write_string(row_pos_2, 1, ks_new_end_comp_date,
                                   content_header_date)

            row_pos += 3
            if ks_df_informations['ks_diff_filter']['ks_debit_credit_visibility']:

                sheet.set_column(0, 0, 90)
                sheet.set_column(1, 1, 15)
                sheet.set_column(2, 3, 15)
                sheet.set_column(3, 3, 15)

                sheet.write_string(row_pos, 1, _('Net Amount'),
                                   format_header)
                sheet.write_string(row_pos, 2, _('Tax'),
                                   format_header)

                for a in lines:
                    if a['ks_level'] == 2:
                        row_pos += 1
                    row_pos += 1
                    if a.get('account', False):
                        tmp_style_str = line_header_string
                        tmp_style_num = line_header
                    else:
                        tmp_style_str = line_header_string_bold
                        tmp_style_num = line_header_bold
                    tmp_style_num.set_num_format(
                        '#,##0.' + '0' * ks_company_id.currency_id.decimal_places or 2)
                    sheet.write_string(row_pos, 0, '   ' * len(a.get('list_len', [])) + a.get('ks_name'),
                                       tmp_style_str)
                    sheet.write_number(row_pos, 1, float(a.get('ks_net_amount', 0.0)), tmp_style_num)

                    sheet.write_number(row_pos, 2, float(a.get('tax', 0.0)), tmp_style_num)
            if not ks_df_informations['ks_diff_filter']['ks_debit_credit_visibility']:

                sheet.set_column(0, 0, 50)
                sheet.set_column(1, 1, 15)
                sheet.set_column(2, 3, 15)
                sheet.set_column(3, 3, 15)
                sheet.write_string(row_pos, 0, _('Name'),
                                   format_header)

                sheet.write_string(row_pos, 1, _('Net Amount') + ks_df_informations['date']['ks_string'],
                                   format_header)
                sheet.write_string(row_pos, 2, _('Net Tax') + ks_df_informations['date']['ks_string'],
                                   format_header)
                ks_col = 3
                # for x in range(3):

                for i in ks_df_informations['ks_differ']['ks_intervals']:
                    sheet.write_string(row_pos, ks_col, _('Net Amount') + i['ks_string'],
                                       format_header)
                    sheet.set_column(ks_col, ks_col, 20)
                    ks_col += 1
                    sheet.write_string(row_pos, ks_col, _('Net Tax') + i['ks_string'],
                                       format_header)
                    sheet.set_column(ks_col, ks_col, 20)
                    ks_col += 1

                ks_col_line = 0
                for line in lines:
                    sheet.write(row_pos + 1, 0, line['ks_name'],
                                format_header)
                    for ks in line['balance_cmp']:
                        sheet.write(row_pos + 1, ks_col_line + 1, ks[0]['ks_com_net'],
                                    line_header)
                        ks_col_line = ks_col_line + 1
                        sheet.write(row_pos + 1, ks_col_line + 1, ks[1]['ks_com_tax'],
                                    line_header)
                        ks_col_line += 1
                    ks_col_line = 0
                    row_pos += 1

            workbook.close()
            output.seek(0)
            generated_file = output.read()
            output.close()

            return generated_file
