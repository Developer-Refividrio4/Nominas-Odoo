/** @odoo-module **/

import { registry } from "@web/core/registry";
const actionRegistry = registry.category("actions");
import { Component, onWillStart, onMounted, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { Layout } from "@web/search/layout";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { ControlPanel } from "@web/search/control_panel/control_panel";
import { _t } from "@web/core/l10n/translation";
import { DateTimePicker } from "@web/core/datetime/datetime_picker";
import { renderToElement } from "@web/core/utils/render";
const { DateTime } = luxon;
import { DateTimeInput } from '@web/core/datetime/datetime_input';
import { session } from "@web/session";
import { getCurrency } from "@web/core/currency";
import { formatMonetary } from "@web/views/fields/formatters";
import { formatFloat } from "@web/core/utils/numbers";
import { parseFloat } from "@web/views/fields/parsers";
//import { KSReportFilters } from "./filters";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { MultiRecordSelector } from "@web/core/record_selectors/multi_record_selector";
import { downloadFile } from "@web/core/network/download";


export class ksDynamicReportsWidget extends Component {

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.user = useService("user");
        this.rpc = useService("rpc");
        this.dialogService = useService('dialog');
        this.notificationService = useService("notification");
        this.state = useState({
            offset_dict: {},
        });

        onWillStart(async () => {
            await this.ksRenderBody()
        });

        onMounted(() => {
            if (this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_gl_action' ||
                this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_pl_action' ||
                this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_rec_action' ||
                this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_pay_action')
                {
                if (this.state.offset_dict.next_offset >= this.state.offset_dict.limit){
                    $('.ks_pager').find('.ks_load_next').addClass('ks_event_offer_list');
                }
            }
        });

    }
    async ksSetReportInfo(values) {
        this.ks_df_reports_ids = values.ks_df_reports_ids;
        this.ks_df_report_opt = values.ks_df_informations;
        this.ks_df_context = values.context;
        this.ks_report_manager_id = values.ks_report_manager_id;
        this.ks_remarks = values.ks_remarks;
        this.$ks_buttons = $(values.ks_buttons);
        this.$ks_searchview_buttons = $(values.ks_searchview_html);
        this.ks_currency = values.ks_currency;
        this.ks_report_lines = values.ks_report_lines;
        this.ks_enable_ledger_in_bal = values.ks_enable_ledger_in_bal;
        this.ks_initial_balance = values.ks_initial_balance;
        this.ks_current_balance = values.ks_current_balance;
        this.ks_ending_balance = values.ks_ending_balance;
        this.ks_diff_filter = values.ks_diff_filter;
        this.ks_retained = values.ks_retained;
        this.ks_subtotal = values.ks_subtotal;
        this.ks_partner_dict = values.ks_partner_dict
        this.ks_period_list = values.ks_period_list
        this.ks_period_dict = values.ks_period_dict
        this.ks_month_lines = values.ks_month_lines
        this.state.offset_dict = values.offset_dict;
        if (this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_gl_action' ||
                this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_pl_action' ||
                this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_rec_action' ||
                this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_pay_action')
                {
                if (this.state.offset_dict.next_offset >= this.state.offset_dict.limit){
                    $('.ks_pager').find('.ks_load_next').addClass('ks_event_offer_list');
                }
            }
        //            this.ksSaveReportInfo();
    }



    async ksRenderBody() {

        await this.orm.call('ks.dynamic.financial.reports', 'ks_get_dynamic_fin_info', [this.props.action.context.id,
        this.ks_df_report_opt],{context:this.props.action.context}).then((result) => {

            //            if (this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_rec_action'){
            this.props.date_to_cmp =""
            this.props.date_from_cmp =""
            this.props.ks_end_date =""
            this.props.previos =""
            this.props.ks_master_value = result
            this.ksSetReportInfo(result);
            this.ks_df_context = result.context
            this.ks_df_report_opt = result['ks_df_informations']
            this.props.ks_df_report_opt = result['ks_df_informations']
            this.props.ks_df_report_opt = result['ks_df_informations']
            var ksFormatConfigurations = {
                currency_id: result.ks_currency,
                noSymbol: true,
            };
            this.initial_balance = this.ksFormatCurrencySign(result.ks_initial_balance, ksFormatConfigurations, result.ks_initial_balance < 0 ? '-' : '');
            this.current_balance = this.ksFormatCurrencySign(result.ks_current_balance, ksFormatConfigurations, result.ks_current_balance < 0 ? '-' : '');
            this.ending_balance = this.ksFormatCurrencySign(result.ks_ending_balance, ksFormatConfigurations, result.ks_ending_balance < 0 ? '-' : '');

            this.ks_partner_dict = result['ks_partner_dict']
            this.ks_period_list = result['ks_period_list']
            this.ks_period_dict = result['ks_period_dict']
            this.ks_report_lines = result['ks_report_lines']
            this.state.offset_dict = result['offset_dict']
            if (this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_gl_action' ||
                this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_pl_action' ||
                this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_rec_action' ||
                this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_pay_action')
                {
                if (this.state.offset_dict.next_offset >= this.state.offset_dict.limit){
                    $('.ks_pager').find('.ks_load_next').addClass('ks_event_offer_list');
                }
            }

            if (this.props.action.xml_id != 'ks_dynamic_financial_report.ks_df_tax_report_action' && this.props.action.xml_id != 'ks_dynamic_financial_report.ks_df_es_action') {
                this.ksSetReportCurrencyConfig();
            } else if (this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_tax_report_action') {
                this.ksSetTaxReportCurrencyConfig();
            } else if (this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_es_action') {
                this.ksSetExecutiveReportCurrencyConfig();
            }



            if (this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_tax_report_action') {
                this.props.ks_df_report_opt = result['ks_df_informations']
                this.props.ks_report_lines = result['ks_report_lines']
            } else if (this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_rec_action') {
                this.ksRenderAgeReceivable()
            } else if (this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_pay_action') {
                this.ksRenderAgePayable()
            } else if (this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_cj_action') {
                this.props.lang = result.context.lang
                this.ksRenderConsolidateJournal()
            } else if (this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_es_action') {
                this.props.ks_df_report_opt = result['ks_df_informations']
                this.props.ks_report_lines = result['ks_report_lines']
                this.ksRenderExecutiveSummary(result)
            } else if (this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_tb_action') {
                this.ks_report_lines = result['ks_report_lines']
                this.ks_retained = result['ks_retained']
                this.ks_subtotal = result['ks_subtotal']
                this.props.ks_report_lines = result['ks_report_lines']
                this.ks_df_report_opt = result['ks_df_informations']
                this.ksRenderTrialBalance();
            } else if (this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_gl_action') {
                this.props.ks_report_lines = result['ks_report_lines']
                this.props.ks_enable_ledger_in_bal = result['ks_enable_ledger_in_bal']
            } else if (this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_pl_action') {
                this.props.ks_report_lines = result['ks_report_lines']
                this.props.ks_enable_ledger_in_bal = result['ks_enable_ledger_in_bal']
            } else {
                this.props.ks_report_lines = result['ks_report_lines']
                this.props.ks_df_report_opt = result['ks_df_informations']
                this.props.ks_initial_balance = result['ks_initial_balance']
                this.props.ks_current_balance = result['ks_current_balance']
                this.props.ks_ending_balance = result['ks_ending_balance']
                if (parseFloat(String(result.ks_initial_balance)) > 0 || parseFloat(String(result.ks_current_balance)) > 0 || parseFloat(String(result.ks_ending_balance)) > 0) {
                    this.props.showgenreport = true
                } else {
                    this.props.showgenesreport = false
                }
            }
            //            }
        })


    }
    async _ksRenderBody() {
        this.ks_result = this.orm.silent.call('ks.dynamic.financial.reports', 'ks_get_dynamic_fin_info', [this.props.action.context.id,
            this.ks_df_report_opt
        ], {
            context: this.props.action.context
        })
        var ks_result = this.ks_result
        return Promise.resolve(ks_result);
    }

    async ksRenderTrialBalance() {
        var self = this;

        Object.entries(self.ks_report_lines).forEach(([v, k]) => {
            var ksFormatConfigurations = {
                currency_id: k.company_currency_id,
                noSymbol: true,
            };
            k.initial_debit = self.ksFormatCurrencySign(k.initial_debit, ksFormatConfigurations, k.initial_debit < 0 ? '-' : '');
            k.initial_credit = self.ksFormatCurrencySign(k.initial_credit, ksFormatConfigurations, k.initial_credit < 0 ? '-' : '');
            k.initial_balance = self.ksFormatCurrencySign(k.initial_balance, ksFormatConfigurations, k.initial_balance < 0 ? '-' : '');
            k.ending_debit = self.ksFormatCurrencySign(k.ending_debit, ksFormatConfigurations, k.ending_debit < 0 ? '-' : '');
            k.ending_credit = self.ksFormatCurrencySign(k.ending_credit, ksFormatConfigurations, k.ending_credit < 0 ? '-' : '');
            k.ending_balance = self.ksFormatCurrencySign(k.ending_balance, ksFormatConfigurations, k.ending_balance < 0 ? '-' : '');
        });
        Object.entries(self.ks_retained).forEach(([v, k]) => {
            var ksFormatConfigurations = {
                currency_id: k.company_currency_id,
                noSymbol: true,
            };
            k.debit = self.ksFormatCurrencySign(k.debit, ksFormatConfigurations, k.debit < 0 ? '-' : '');
            k.credit = self.ksFormatCurrencySign(k.credit, ksFormatConfigurations, k.credit < 0 ? '-' : '');
            k.balance = self.ksFormatCurrencySign(k.balance, ksFormatConfigurations, k.balance < 0 ? '-' : '');
            k.initial_debit = self.ksFormatCurrencySign(k.initial_debit, ksFormatConfigurations, k.initial_debit < 0 ? '-' : '');
            k.initial_credit = self.ksFormatCurrencySign(k.initial_credit, ksFormatConfigurations, k.initial_credit < 0 ? '-' : '');
            k.initial_balance = self.ksFormatCurrencySign(k.initial_balance, ksFormatConfigurations, k.initial_balance < 0 ? '-' : '');
            k.ending_debit = self.ksFormatCurrencySign(k.ending_debit, ksFormatConfigurations, k.ending_debit < 0 ? '-' : '');
            k.ending_credit = self.ksFormatCurrencySign(k.ending_credit, ksFormatConfigurations, k.ending_credit < 0 ? '-' : '');
            k.ending_balance = self.ksFormatCurrencySign(k.ending_balance, ksFormatConfigurations, k.ending_balance < 0 ? '-' : '');
        });
        Object.entries(self.ks_subtotal).forEach(([v, k]) => {
            var ksFormatConfigurations = {
                currency_id: k.company_currency_id,
                noSymbol: true,
            };
            k.debit = self.ksFormatCurrencySign(k.debit, ksFormatConfigurations, k.debit < 0 ? '-' : '');
            k.credit = self.ksFormatCurrencySign(k.credit, ksFormatConfigurations, k.credit < 0 ? '-' : '');
            k.balance = self.ksFormatCurrencySign(k.balance, ksFormatConfigurations, k.balance < 0 ? '-' : '');
            k.initial_debit = self.ksFormatCurrencySign(k.initial_debit, ksFormatConfigurations, k.initial_debit < 0 ? '-' : '');
            k.initial_credit = self.ksFormatCurrencySign(k.initial_credit, ksFormatConfigurations, k.initial_credit < 0 ? '-' : '');
            k.initial_balance = self.ksFormatCurrencySign(k.initial_balance, ksFormatConfigurations, k.initial_balance < 0 ? '-' : '');
            k.ending_debit = self.ksFormatCurrencySign(k.ending_debit, ksFormatConfigurations, k.ending_debit < 0 ? '-' : '');
            k.ending_credit = self.ksFormatCurrencySign(k.ending_credit, ksFormatConfigurations, k.ending_credit < 0 ? '-' : '');
            k.ending_balance = self.ksFormatCurrencySign(k.ending_balance, ksFormatConfigurations, k.ending_balance < 0 ? '-' : '');
        });
        var new_date_format = 'yyyy-M-d';
        //                    if (this.ks_df_report_opt['date']['ks_end_date']) {
        //                         this.ks_df_report_opt['date']['ks_end_date'] = moment(this.ks_df_report_opt['date']['ks_end_date']).format(new_date_format)
        //                        }
        //                     ks_df_new_report_opt['date']['ks_end_date'] = moment(self.ks_df_report_opt['date']['ks_end_date']).format(new_date_format)
        //                     ks_df_report_new_opt['date']['ks_start_date'] = moment(self.ks_df_report_opt['date']['ks_start_date']).format(new_date_format)
        self.props.ks_df_new_start_report_opt = DateTime.fromISO(self.ks_df_report_opt['date']['ks_start_date']).toISODate(new_date_format)
        self.props.account_data = this.ks_report_lines
        self.props.retained = this.ks_retained
        self.props.subtotal = this.ks_subtotal
        self.props.ks_df_new_end_report_opt = DateTime.fromISO(self.ks_df_report_opt['date']['ks_end_date']).toISODate(new_date_format)
        //            self.$('.o_content').html(QWeb.render('ks_df_trial_balance', {
        //
        //                    account_data: self.ks_report_lines,
        //                    retained: self.ks_retained,
        //                    ks_df_new_start_report_opt: ks_df_new_start_report_opt,
        //                    ks_df_new_end_report_opt: ks_df_new_end_report_opt,
        //                    subtotal: self.ks_subtotal,
        //                }));
        //                ks_df_report_opt['date']['ks_end_date'] = moment(ks_df_report_opt['date']['ks_end_date']).format(new_date_format)
    }
    async onDateTimeChanged(e){
        this.props.ks_end_date = e
    }
    async onDateTimeChangedStartDate(e){
        this.props.ks_start_date = e
    }
    async fdate_from_cmp(e){
        this.props.date_from_cmp = e
    }
    async fdate_to_cmp(e){

        this.props.date_to_cmp = e
    }
    /**
     * @method to render Age Receivable report
     */
    async ksRenderAgeReceivable() {
        var self = this;

        Object.entries(self.ks_partner_dict).forEach(([v, k]) => {
            var ksFormatConfigurations = {
                currency_id: k.company_currency_id,
                noSymbol: true,
            };
            for (var z = 0; z < self.ks_period_list.length; z++) {
                k[self.ks_period_list[z]] = self.ksFormatCurrencySign(k[self.ks_period_list[z]], ksFormatConfigurations, k[self.ks_period_list[z]] < 0 ? '-' : '');
            }
            k.total = self.ksFormatCurrencySign(k.total, ksFormatConfigurations, k.total < 0 ? '-' : '');
        });
        self.props.ks_period_list = self.ks_period_list
        self.props.ks_period_dict = self.ks_period_dict
        self.props.ks_partner_dict = self.ks_partner_dict
    }




    /**
     * @method to render Age Payable report
     */
    async ksRenderAgePayable() {
        var self = this;

        Object.entries(self.ks_partner_dict).forEach(([v, k]) => {
            var ksFormatConfigurations = {
                currency_id: k.company_currency_id,
                noSymbol: true,
            };
            for (var z = 0; z < self.ks_period_list.length; z++) {
                k[self.ks_period_list[z]] = self.ksFormatCurrencySign(k[self.ks_period_list[z]], ksFormatConfigurations, k[self.ks_period_list[z]] < 0 ? '-' : '');
            }
            k.total = self.ksFormatCurrencySign(k.total, ksFormatConfigurations, k.total < 0 ? '-' : '');
        });
        self.props.ks_period_list = self.ks_period_list
        self.props.ks_period_dict = self.ks_period_dict
        self.props.ks_partner_dict = self.ks_partner_dict
    }
    async ksSetReportCurrencyConfig() {
        var self = this;

        Object.entries(self.ks_report_lines).forEach(([v, k]) => {
            var ksFormatConfigurations = {
                currency_id: k.company_currency_id,
                noSymbol: true,
            };
            k.debit = self.ksFormatCurrencySign(k.debit, ksFormatConfigurations, k.debit < 0 ? '-' : '');
            k.credit = self.ksFormatCurrencySign(k.credit, ksFormatConfigurations, k.credit < 0 ? '-' : '');
            if (self.props.action.xml_id == _t('ks_dynamic_financial_report.ks_df_tb_action')) {

            } else {
                k.initial_balance = self.ksFormatCurrencySign(k.initial_balance, ksFormatConfigurations, k.initial_balance < 0 ? '-' : '');
            }
            //  changed the values of balance
            if (!k['percentage']) {
                k.balance = self.ksFormatCurrencySign(k.balance, ksFormatConfigurations, k.balance < 0 ? '-' : '');
            } else {
                k.balance = String(Math.round(k.balance)) + "%";
            }

            for (const prop in k.balance_cmp) {
                k.balance_cmp[prop] = self.ksFormatCurrencySign(k.balance_cmp[prop], ksFormatConfigurations, k.balance[prop] < 0 ? '-' : '');
            }
        });
    }
    async ksSetTaxReportCurrencyConfig() {
        var self = this;

        Object.entries(self.ks_report_lines).forEach(([v, k]) => {
            var ksFormatConfigurations = {
                currency_id: k.company_currency_id,
                noSymbol: true,
            };
            k.ks_net_amount = self.ksFormatCurrencySign(k.ks_net_amount, ksFormatConfigurations, k.ks_net_amount < 0 ? '-' : '');
            k.tax = self.ksFormatCurrencySign(k.tax, ksFormatConfigurations, k.tax < 0 ? '-' : '');

            for (const prop in k.balance_cmp) {
                k.balance_cmp[prop][0]['ks_com_net'] = self.ksFormatCurrencySign(k.balance_cmp[prop][0]['ks_com_net'], ksFormatConfigurations, k.balance_cmp[prop][0]['ks_com_net'] < 0 ? '-' : '');
                k.balance_cmp[prop][1]['ks_com_tax'] = self.ksFormatCurrencySign(k.balance_cmp[prop][1]['ks_com_tax'], ksFormatConfigurations, k.balance_cmp[prop][1]['ks_com_tax'] < 0 ? '-' : '');
            }
        });
    }
    async ksSetExecutiveReportCurrencyConfig() {
        var self = this;

        Object.entries(self.ks_report_lines).forEach(([v, k]) => {
            var ksFormatConfigurations = {
                currency_id: k.company_currency_id,
                noSymbol: true,
            };

            for (const prop in k.debit) {
                k.debit[prop] = self.ksFormatCurrencySign(k.debit[prop], ksFormatConfigurations, k.debit[prop] < 0 ? '-' : '');
            }
            for (const prop in k.credit) {
                k.credit[prop] = self.ksFormatCurrencySign(k.credit[prop], ksFormatConfigurations, k.credit[prop] < 0 ? '-' : '');
            }

            //  changed the values of balance
            if (!k['percentage']) {
                for (const prop in k.balance) {
                    k.balance[prop] = self.ksFormatCurrencySign(k.balance[prop], ksFormatConfigurations, k.balance[prop] < 0 ? '-' : '');
                }
            } else {
                for (const prop in k.balance) {
                    k.balance[prop] = String(formatFloat(k.balance[prop])) + "%";
                }
            }

            for (const prop in k.balance_cmp) {
                k.balance_cmp[prop] = self.ksFormatCurrencySign(k.balance_cmp[prop], ksFormatConfigurations, k.balance[prop] < 0 ? '-' : '');
            }
        });
    }

    async ksRenderExecutiveSummary(result) {
        var self = this;

        if (parseFloat(String(result.ks_initial_balance)) > 0 || parseFloat(String(result.ks_current_balance)) > 0 || parseFloat(String(result.ks_ending_balance)) > 0) {
            this.props.showesreport = true

        } else {
            this.props.showesreport = false
        }

    }

    ksFormatCurrencySign(amount, ksFormatConfigurations, sign) {
        var currency_id = ksFormatConfigurations.currency_id;
        currency_id = getCurrency(currency_id);
        var without_sign = formatMonetary(Math.abs(amount), {}, ksFormatConfigurations);
        if (!amount) {
            return '-'
        };
        if (currency_id) {
            if (currency_id.position === "after") {
                return sign + '' + without_sign + '' + currency_id.symbol;
            } else {
                return currency_id.symbol + '' + sign + '' + without_sign;
            }
        }
        return without_sign;
    }
    async ksRenderConsolidateJournal() {
        var self = this;

        Object.entries(self.ks_partner_dict).forEach(([v, k]) => {
            var ksFormatConfigurations = {
                currency_id: k.company_currency_id,
                noSymbol: true,
            };
            k.debit = self.ksFormatCurrencySign(k.debit, ksFormatConfigurations, k.debit < 0 ? '-' : '');
            k.credit = self.ksFormatCurrencySign(k.credit, ksFormatConfigurations, k.credit < 0 ? '-' : '');
            k.balance = self.ksFormatCurrencySign(k.balance, ksFormatConfigurations, k.balance < 0 ? '-' : '')

        });
        this.props.ks_report_lines = self.ks_report_lines,
            this.props.ks_month_lines = self.ks_month_lines
    }


    async OnPrintPdf() {
        var self = this;
        if ((self.props.action.xml_id == _t('ks_dynamic_financial_report.ks_df_gl_action'))||
            (self.props.action.xml_id == _t('ks_dynamic_financial_report.ks_df_pl_action'))||
            (self.props.action.xml_id == _t('ks_dynamic_financial_report.ks_df_pay_action'))||
            (self.props.action.xml_id == _t('ks_dynamic_financial_report.ks_df_rec_action'))) {
                this.props.action.context['OFFSET']=true
                }
        var pdf_data = await this.orm.call("ks.dynamic.financial.reports", 'ks_get_dynamic_fin_info', [this.props.action.context.id, this.ks_df_report_opt], {
            context: this.props.action.context
        }).then(async (data) => {
            var report_name = self.ksGetReportName();
            var action = self.ksGetReportAction(report_name, data);
            self.props.action.context['OFFSET']=false;
             var pdf_report = await this.rpc("/dfr/pdf/download", {
                id: self.props.action.context.id,
                data: action.data,
                context: action.context,
                reportname: report_name
            });
            return pdf_report;
        });
        var filename = self.props.action.name;
        const byteArray = new Uint8Array(pdf_data.length);
        for (let i = 0; i < pdf_data.length; i++) {
            byteArray[i] = pdf_data.charCodeAt(i);
        }
        const blob = new Blob([byteArray], { type: "application/pdf" });
        await downloadFile(blob, filename, "application/pdf");
    }
    async ksPrintReportXlsx() {

        var self = this;
        this.orm.call("ks.dynamic.financial.reports", 'ks_print_xlsx', [this.props.action.context.id, this.ks_df_report_opt], {
            context: this.props.action.context
        }).then((data) => {
            return self.action.doAction(data);
        });

    }

    ksGetReportName() {
        var self = this;
        if (self.props.action.xml_id == _t('ks_dynamic_financial_report.ks_df_tb_action')) {
            return 'ks_dynamic_financial_report.ks_account_report_trial_balance';
        } else if (self.props.action.xml_id == _t('ks_dynamic_financial_report.ks_df_gl_action')) {
            return 'ks_dynamic_financial_report.ks_dynamic_financial_general_ledger';
        } else if (self.props.action.xml_id == _t('ks_dynamic_financial_report.ks_df_pl_action')) {
            return 'ks_dynamic_financial_report.ks_dynamic_financial_partner_ledger';
        } else if (self.props.action.xml_id == _t("ks_dynamic_financial_report.ks_df_rec_action")) {
            return 'ks_dynamic_financial_report.ks_dynamic_financial_age_receivable';
        } else if (self.props.action.xml_id == _t("ks_dynamic_financial_report.ks_df_pay_action")) {
            return 'ks_dynamic_financial_report.ks_dynamic_financial_age_payable';
        } else if (self.props.action.xml_id == _t('ks_dynamic_financial_report.ks_df_cj_action')) {
            return 'ks_dynamic_financial_report.ks_dynamic_financial_consolidate_journal';
        } else if (self.props.action.xml_id == _t('ks_dynamic_financial_report.ks_df_tax_report_action')) {
            return 'ks_dynamic_financial_report.ks_dynamic_financial_tax_report';
        } else if (self.props.action.xml_id == _t('ks_dynamic_financial_report.ks_df_es_action')) {
            return 'ks_dynamic_financial_report.ks_df_executive_summary';
        } else {
            return 'ks_dynamic_financial_report.ks_account_report_lines';
        }
    }
    async ksReportSendEmail(e) {
        e.preventDefault();
        var self = this;
        this.orm.call("ks.dynamic.financial.reports", 'ks_get_dynamic_fin_info', [this.props.action.context.id, this.ks_df_report_opt], {
            context: this.props.action.context
        }).then((data) => {
            var ks_report_action = self.ksGetReportActionName();
            this.orm.call("ks.dynamic.financial.reports", 'ks_action_send_email', [this.props.action.context.id, data, ks_report_action], {
                context: data['context']

            })
            this.notificationService.add(_t("Email Sent!"), { type: 'success' });

        });

    }
    ksGetReportActionName() {
        var self = this;

        if (self.props.action.xml_id == _t('ks_dynamic_financial_report.ks_df_tb_action')) {
            return 'ks_dynamic_financial_report.ks_dynamic_financial_trial_bal_action';
        } else if (self.props.action.xml_id == _t('ks_dynamic_financial_report.ks_df_gl_action')) {
            return 'ks_dynamic_financial_report.ks_dynamic_financial_gel_bal_action';
        } else if (self.props.action.xml_id == _t('ks_dynamic_financial_report.ks_df_pl_action')) {
            return 'ks_dynamic_financial_report.ks_dynamic_financial_partner_led_action';
        } else if (self.props.action.xml_id == _t("ks_dynamic_financial_report.ks_df_rec_action")) {
            return 'ks_dynamic_financial_report.ks_dynamic_financial_age_rec_action';
        } else if (self.props.action.xml_id == _t("ks_dynamic_financial_report.ks_df_pay_action")) {
            return 'ks_dynamic_financial_report.ks_dynamic_financial_age_pay_action';
        } else if (self.props.action.xml_id == _t('ks_dynamic_financial_report.ks_df_cj_action')) {
            return 'ks_dynamic_financial_report.ks_dynamic_financial_cons_journal_action';
        } else if (self.props.action.xml_id == _t('ks_dynamic_financial_report.ks_df_tax_report_action')) {
            return 'ks_dynamic_financial_report.ks_dynamic_financial_tax_action';
        } else if (self.props.action.xml_id == _t('ks_dynamic_financial_report.ks_df_es_action')) {
            return 'ks_dynamic_financial_report.ks_dynamic_financial_executive_action';
        } else {
            return 'ks_dynamic_financial_report.ks_dynamic_financial_report_action';
        }
    }
    ksGetReportAction(report_name, data) {
        var self = this;

        var new_date_format = 'yyyy-M-d';
        //            var dt = new datepicker.DateWidget(options);
        data.ks_df_informations.date.ks_end_date = DateTime.fromISO(data.ks_df_informations.date.ks_end_date).toISODate(new_date_format);
        data.ks_df_informations.date.ks_start_date = DateTime.fromISO(data.ks_df_informations.date.ks_start_date).toISODate(new_date_format);

        if (data['ks_df_informations']['ks_differ']['ks_intervals'].length !== 0) {
            data['ks_df_informations']['ks_differ']['ks_end_date'] = DateTime.fromISO(data['ks_df_informations']['ks_differ']['ks_end_date']).toISODate(new_date_format);
            data['ks_df_informations']['ks_differ']['ks_start_date'] = DateTime.fromISO(data['ks_df_informations']['ks_differ']['ks_start_date']).toISODate(new_date_format);
        }
        return {
            'type': 'ir.actions.report',
            'report_type': 'qweb-pdf',
            'report_name': report_name,
            'report_file': report_name,
            'data': {
                'js_data': data
            },
            'context': {
                'active_model': this.props.action.context.model,
                'landscape': 1,
                'from_js': true,
            },
            'display_name': self.props.action.name,
        };
    }


    async updateFilter(bsFilter) {
        var self = this

        self.ks_df_context.ks_option_enable = false;
        self.ks_df_context.ks_journal_enable = false
        self.ks_df_context.ks_account_enable = false
        self.ks_df_context.ks_account_both_enable = false
        self.ks_df_report_opt.date.ks_filter = bsFilter
        var error = false;
        var new_date_format = 'yyyy-M-d';

        if (bsFilter === 'custom' ) {
            var ks_start_date = ''
            var ks_end_date = ''
            if (this.props.ks_end_date != '' && this.props.ks_start_date !== undefined && this.props.ks_start_date !== false){
                ks_start_date = this.props.ks_start_date.toISODate('yyyy-M-d')
                ks_end_date = this.props.ks_end_date.toISODate('yyyy-M-d')
            }else if(this.props.ks_end_date != ''){
            ks_end_date = this.props.ks_end_date.toISODate('yyyy-M-d')
            }
            if (ks_start_date != "") {
                error = ks_start_date === "" || ks_end_date === "";
                self.ks_df_report_opt.date.ks_start_date = ks_start_date
                self.ks_df_report_opt.date.ks_end_date = ks_end_date;
            } else {
                error = ks_end_date === "";
                if (!error){
                self.ks_df_report_opt.date.ks_end_date = ks_end_date;
                }
            }
        }
        //                if (error) {
        if (error) {

            this.dialogService.add(AlertDialog, {
                title: _t('Odoo Warning'),
                body: _t("Date cannot be empty."),
                confirmLabel: _t('Ok'),
            });
            return
            //                    new WarningDialog(self, {
            //                        title: _t("Odoo Warning"),
            //                    }, {
            //                        message: _t("Date cannot be empty")
            //                    }).open();
        } else {

            const result = await this._ksRenderBody();
            this.setReportValues(result)

        }



    }
    async setReportValues(result){
        this.props.ks_master_value = result
            this.ksSetReportInfo(result);
            this.ks_df_context = result.context
            this.ks_df_report_opt = result['ks_df_informations']
            var ksFormatConfigurations = {
                currency_id: result.ks_currency,
                noSymbol: true,
            };
            this.initial_balance = this.ksFormatCurrencySign(result.ks_initial_balance, ksFormatConfigurations, result.ks_initial_balance < 0 ? '-' : '');
            this.current_balance = this.ksFormatCurrencySign(result.ks_current_balance, ksFormatConfigurations, result.ks_current_balance < 0 ? '-' : '');
            this.ending_balance = this.ksFormatCurrencySign(result.ks_ending_balance, ksFormatConfigurations, result.ks_ending_balance < 0 ? '-' : '');

            this.ks_partner_dict = result['ks_partner_dict']
            this.ks_period_list = result['ks_period_list']
            this.ks_period_dict = result['ks_period_dict']
            this.ks_report_lines = result['ks_report_lines']

            if (this.props.action.xml_id != 'ks_dynamic_financial_report.ks_df_tax_report_action' && this.props.action.xml_id != 'ks_dynamic_financial_report.ks_df_es_action') {
                this.ksSetReportCurrencyConfig();
            } else if (this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_tax_report_action') {
                this.ksSetTaxReportCurrencyConfig();
            } else if (this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_es_action') {
                this.ksSetExecutiveReportCurrencyConfig();
            }



            if (this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_tax_report_action') {
                this.props.ks_df_report_opt = result['ks_df_informations']
                this.props.ks_report_lines = result['ks_report_lines']
            } else if (this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_rec_action') {
                this.ksRenderAgeReceivable()
            } else if (this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_pay_action') {
                this.ksRenderAgePayable()
            } else if (this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_cj_action') {
                this.ksRenderConsolidateJournal()
            } else if (this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_es_action') {
                this.props.ks_df_report_opt = result['ks_df_informations']
                this.props.ks_report_lines = result['ks_report_lines']
                this.ksRenderExecutiveSummary(result)
            } else if (this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_tb_action') {
                this.ks_report_lines = result['ks_report_lines']
                this.ks_retained = result['ks_retained']
                this.ks_subtotal = result['ks_subtotal']
                this.props.ks_report_lines = result['ks_report_lines']
                this.ks_df_report_opt = result['ks_df_informations']
                this.ksRenderTrialBalance();
            } else if (this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_gl_action') {
                this.props.ks_report_lines = result['ks_report_lines']
                this.props.ks_enable_ledger_in_bal = result['ks_enable_ledger_in_bal']
            } else if (this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_pl_action') {
                this.props.ks_report_lines = result['ks_report_lines']
                this.props.ks_enable_ledger_in_bal = result['ks_enable_ledger_in_bal']
            } else {
                this.props.ks_report_lines = result['ks_report_lines']
                this.props.ks_df_report_opt = result['ks_df_informations']
                this.props.ks_initial_balance = result['ks_initial_balance']
                this.props.ks_current_balance = result['ks_current_balance']
                this.props.ks_ending_balance = result['ks_ending_balance']
                if (parseFloat(String(result.ks_initial_balance)) > 0 || parseFloat(String(result.ks_current_balance)) > 0 || parseFloat(String(result.ks_ending_balance)) > 0) {
                    this.props.showgenreport = true
                } else {
                    this.props.showgenesreport = false
                }
            }
             this.render()
    }
    async ksGetAgedReportDetailedInfo(offset, partner_id) {
            var self = this;
            var lines = await this.orm.call("ks.dynamic.financial.reports", 'ks_process_aging_data', [this.props.action.context.id, self.ks_df_report_opt, offset, partner_id])
            return Promise.resolve(lines);
        }

    async ksGetAgedLinesInfo(event) {
            var ev = event.currentTarget
             $('.o_filter_menu').removeClass('ks_d_block')
            event.preventDefault();


            var self = this;
            var partner_id = $(ev).data('bsPartnerId');
            var offset = 0;

            if ($(event.currentTarget).hasClass('ks_load_previous_new')){
                var offset = parseInt($(event.currentTarget).parent().attr('offset'));
                offset = offset-1;

                if(offset >= 0){
                    $(event.currentTarget).parent().attr('offset', offset)
                }else{
                    var total_pages = parseInt($(event.currentTarget).parent().attr('total_pages'));
                    offset = total_pages-1;
                    $(event.currentTarget).parent().attr('offset', offset)
                }
                $(event.currentTarget).parent().parent().find(".ks_new_text")[0].innerText = offset+1;
            }
            if ($(event.currentTarget).hasClass('ks_load_next_new')){
                var offset = parseInt($(ev).parent().attr('offset'));
                offset = offset+1;
                var total_pages = parseInt($(event.currentTarget).parent().attr('total_pages'));

                if(offset < total_pages){
                    $(event.currentTarget).parent().attr('offset', offset)
                }else{
                    offset = 0;
                    $(event.currentTarget).parent().attr('offset', offset)
                }
                $(event.currentTarget).parent().parent().find(".ks_new_text")[0].innerText = offset+1;
            }
            var td = $(ev).next('tr').find('td');
            if (td.length == 1 || $(event.currentTarget).hasClass('ks_pr-py-mline')) {
                self.ksGetAgedReportDetailedInfo(offset, partner_id).then(function (datas) {
                    var count = datas[0];
                    var offset = datas[1];
                    var account_data = datas[2];
                    var period_list = datas[3];
                    Object.entries(self.ks_partner_dict).forEach(([v, k]) => {
                        var ksFormatConfigurations = {
                            currency_id: k.company_currency_id,
                            noSymbol: true,
                        };
                        k.range_0 = self.ksFormatCurrencySign(k.range_0, ksFormatConfigurations, k.range_0 < 0 ? '-' : '');
                        k.range_1 = self.ksFormatCurrencySign(k.range_1, ksFormatConfigurations, k.range_1 < 0 ? '-' : '');
                        k.range_2 = self.ksFormatCurrencySign(k.range_2, ksFormatConfigurations, k.range_2 < 0 ? '-' : '');
                        k.range_3 = self.ksFormatCurrencySign(k.range_3, ksFormatConfigurations, k.range_3 < 0 ? '-' : '');
                        k.range_4 = self.ksFormatCurrencySign(k.range_4, ksFormatConfigurations, k.range_4 < 0 ? '-' : '');
                        k.range_5 = self.ksFormatCurrencySign(k.range_5, ksFormatConfigurations, k.range_5 < 0 ? '-' : '');
                        k.range_6 = self.ksFormatCurrencySign(k.range_6, ksFormatConfigurations, k.range_6 < 0 ? '-' : '');
                        k.date_maturity = DateTime.fromISO(k.date_maturity, { zone: 'utc' });
                    });

                    if ($(event.target).hasClass('ks_pr-py-mline')) {
                        $(ev).next('div').find('td .ks_py-mline-table-div').remove();
                        const content = renderToElement('ks_df_sub_receivable0', {
                                count: count,
                                self: self,
                                offset: offset,
                                account_data: account_data,
                                period_list: period_list,
                                lang: self.ks_df_context.lang
                            })
                        $(ev).parent().parent().next('div').replaceWith(content)
                    }else {
                        $(ev).next('tr').find('td .ks_py-mline-table-div').remove();
                        const content = renderToElement('ks_df_sub_receivable0', {
                                count: count,
                                self: self,
                                offset: offset,
                                account_data: account_data,
                                period_list: period_list,
                                lang: self.ks_df_context.lang
                            })
                        $(ev).next('tr').find('td ul').after(content)
                    }


                    $(ev).next('tr').find('td ul li:first a').css({
                        'background-color': '#00ede8',
                        'font-weight': 'bold',
                    });
                    self.render()
                })
            }
        }

        renderPagesBody(result){
            this.props.date_to_cmp =""
            this.props.date_from_cmp =""
            this.props.ks_end_date =""
            this.props.previos =""
            this.props.ks_master_value = result
            this.ksSetReportInfo(result);
            this.ks_df_context = result.context
            this.ks_df_report_opt = result['ks_df_informations']
            this.props.ks_df_report_opt = result['ks_df_informations']
            this.props.ks_df_report_opt = result['ks_df_informations']
            var ksFormatConfigurations = {
                currency_id: result.ks_currency,
                noSymbol: true,
            };
            this.initial_balance = this.ksFormatCurrencySign(result.ks_initial_balance, ksFormatConfigurations, result.ks_initial_balance < 0 ? '-' : '');
            this.current_balance = this.ksFormatCurrencySign(result.ks_current_balance, ksFormatConfigurations, result.ks_current_balance < 0 ? '-' : '');
            this.ending_balance = this.ksFormatCurrencySign(result.ks_ending_balance, ksFormatConfigurations, result.ks_ending_balance < 0 ? '-' : '');

            this.ks_partner_dict = result['ks_partner_dict']
            this.ks_period_list = result['ks_period_list']
            this.ks_period_dict = result['ks_period_dict']
            this.ks_report_lines = result['ks_report_lines']
            this.state.offset_dict = result['offset_dict']
            if (this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_gl_action' ||
                this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_pl_action' ||
                this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_rec_action' ||
                this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_pay_action')
                {
                if (this.state.offset_dict.next_offset >= this.state.offset_dict.limit){
                    $('.ks_pager').find('.ks_load_next').addClass('ks_event_offer_list');
                }
            }

            if (this.props.action.xml_id != 'ks_dynamic_financial_report.ks_df_tax_report_action' && this.props.action.xml_id != 'ks_dynamic_financial_report.ks_df_es_action') {
                this.ksSetReportCurrencyConfig();
            } else if (this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_tax_report_action') {
                this.ksSetTaxReportCurrencyConfig();
            } else if (this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_es_action') {
                this.ksSetExecutiveReportCurrencyConfig();
            }



            if (this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_tax_report_action') {
                this.props.ks_df_report_opt = result['ks_df_informations']
                this.props.ks_report_lines = result['ks_report_lines']
            } else if (this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_rec_action') {
                this.ksRenderAgeReceivable()
            } else if (this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_pay_action') {
                this.ksRenderAgePayable()
            } else if (this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_cj_action') {
                this.props.lang = result.context.lang
                this.ksRenderConsolidateJournal()
            } else if (this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_es_action') {
                this.props.ks_df_report_opt = result['ks_df_informations']
                this.props.ks_report_lines = result['ks_report_lines']
                this.ksRenderExecutiveSummary(result)
            } else if (this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_tb_action') {
                this.ks_report_lines = result['ks_report_lines']
                this.ks_retained = result['ks_retained']
                this.ks_subtotal = result['ks_subtotal']
                this.props.ks_report_lines = result['ks_report_lines']
                this.ks_df_report_opt = result['ks_df_informations']
                this.ksRenderTrialBalance();
            } else if (this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_gl_action') {
                this.props.ks_report_lines = result['ks_report_lines']
                this.props.ks_enable_ledger_in_bal = result['ks_enable_ledger_in_bal']
            } else if (this.props.action.xml_id == 'ks_dynamic_financial_report.ks_df_pl_action') {
                this.props.ks_report_lines = result['ks_report_lines']
                this.props.ks_enable_ledger_in_bal = result['ks_enable_ledger_in_bal']
            } else {
                this.props.ks_report_lines = result['ks_report_lines']
                this.props.ks_df_report_opt = result['ks_df_informations']
                this.props.ks_initial_balance = result['ks_initial_balance']
                this.props.ks_current_balance = result['ks_current_balance']
                this.props.ks_ending_balance = result['ks_ending_balance']
                if (parseFloat(String(result.ks_initial_balance)) > 0 || parseFloat(String(result.ks_current_balance)) > 0 || parseFloat(String(result.ks_ending_balance)) > 0) {
                    this.props.showgenreport = true
                } else {
                    this.props.showgenesreport = false
                }
            }

        }

        async ksLoadPreviousRecords(e) {
        var paginationlimit=10;
        var self = this;
        var ks_offset =  parseInt(e.target.parentElement.dataset.prevOffset) - (paginationlimit+1) ;
        var ks_intial_count = e.target.parentElement.dataset.next_offset;


        return await this.orm.call('ks.dynamic.financial.reports', 'ks_get_dynamic_fin_info', [this.props.action.context.id,
            this.ks_df_report_opt,{ks_intial_count: ks_intial_count,offset: ks_offset}],{context:this.props.action.context}).then(function (result) {
                $('.ks_pager').find('.ks_value').text(result.offset_dict.offset + "-" + result.offset_dict.next_offset);
                e.target.parentElement.dataset.next_offset = result.offset_dict.next_offset;
                e.target.parentElement.dataset.prevOffset = result.offset_dict.offset;
                $('.ks_pager').find('.ks_load_next').removeClass('ks_event_offer_list');

                if (result.offset_dict.offset === 1) {
                   $(e.target).addClass('ks_event_offer_list');
                }


                    self.ksSetReportInfo(result);
                        self.renderPagesBody(result);
                        self.render();

                });
        }


        async ksLoadMoreRecords(e){

            var self = this;
            var ev = e.target;
            var ks_intial_count = e.target.parentElement.parentElement.prevOffset;
            var ks_offset = e.target.parentElement.dataset.next_offset;

            return await this.orm.call('ks.dynamic.financial.reports', 'ks_get_dynamic_fin_info', [this.props.action.context.id,
            this.ks_df_report_opt,{ks_intial_count: ks_intial_count,offset: ks_offset}],{context:this.props.action.context}).then(function (result) {
                      $('.ks_pager').find('.ks_value').text(result.offset_dict.offset + "-" + result.offset_dict.next_offset);
                      ev.parentElement.dataset.next_offset = result.offset_dict.next_offset;
                      ev.parentElement.dataset.prevOffset = result.offset_dict.offset;
                      $('.ks_pager').find('.ks_load_previous').removeClass('ks_event_offer_list');
                     if (result.offset_dict.next_offset >= result.offset_dict.limit){
                        $(e.target).addClass('ks_event_offer_list')
                    }
                        self.ksSetReportInfo(result);
                        self.renderPagesBody(result);
                        self.render();

                    });
        }


    async ksGetConsolidateLinesByPage(offset, ks_journal_id) {
            var self = this;
            var lines = await this.orm.call("ks.dynamic.financial.reports", 'ks_consolidate_journals_details', [this.props.action.context.id, offset, ks_journal_id, self.ks_df_report_opt])
            return Promise.resolve(lines);

        }

    async ksGetConsolidateInfo(event) {

            var ev = event.currentTarget
             $('.o_filter_menu').removeClass('ks_d_block')
            event.preventDefault();
            var self = this;
            var ks_journal_id = $(ev).data('bsJournalId');
            var offset = 0;
            var td = $(ev).next('tr').find('td');
            if (td.length == 1) {
                self.ksGetConsolidateLinesByPage(offset, ks_journal_id).then(function (datas) {
                    var offset = datas[0];
                    var account_data = datas[1];
                    Object.entries(account_data).forEach(([v, k]) => {
                        var ksFormatConfigurations = {
                            currency_id: k.company_currency_id,
                            noSymbol: true,
                        };
                        k.debit = self.ksFormatCurrencySign(k.debit, ksFormatConfigurations, k.debit < 0 ? '-' : '');
                        k.credit = self.ksFormatCurrencySign(k.credit, ksFormatConfigurations, k.credit < 0 ? '-' : '');
                        k.balance = self.ksFormatCurrencySign(k.balance, ksFormatConfigurations, k.balance < 0 ? '-' : '');
                        k.ldate = DateTime.fromISO(k.ldate, { zone: 'utc' });
                    });
                    $(ev).next('tr').find('td .ks_py-mline-table-div').remove();
                    const content = renderToElement('ks_df_cj_subsection', {
                            offset: offset,
                            self: self,
                            account_data: account_data,
                            lang: self.ks_df_context.lang
                        })
                    $(ev).next('tr').find('td ul').after(content)
                    $(ev).next('tr').find('td ul li:first a').css({
                        'background-color': '#00ede8',
                        'font-weight': 'bold',
                    });
                })
            }
        }




    async ksGetGlLineByPage(offset, account_id) {
            var self = this;
            var lines = await this.orm.call("ks.dynamic.financial.reports", 'ks_build_detailed_gen_move_lines', [this.props.action.context.id, offset, account_id, self.ks_df_report_opt])
            return Promise.resolve(lines);
        }


        async ksGetMoveLines(event) {

            var ev = event.currentTarget
            event.preventDefault();

            var offset = 0;

            if ($(event.currentTarget).hasClass('ks_load_previous_new')){
                var offset = parseInt($(event.currentTarget).parent().attr('offset'));
                offset = offset-1;

                if(offset >= 0){
                    $(event.currentTarget).parent().attr('offset', offset)
                }else{
                    var total_pages = parseInt($(event.currentTarget).parent().attr('total_pages'));
                    offset = total_pages-1;
                    $(event.currentTarget).parent().attr('offset', offset)
                }
                $(event.currentTarget).parent().parent().find(".ks_new_text")[0].innerText = offset+1;
            }
            else if ($(event.currentTarget).hasClass('ks_load_next_new')){
                var offset = parseInt($(event.currentTarget).parent().attr('offset'));
                offset = offset+1;
                var total_pages = parseInt($(event.currentTarget).parent().attr('total_pages'));

                if(offset < total_pages){
                    $(event.currentTarget).parent().attr('offset', offset)
                }else{
                    offset = 0;
                    $(event.currentTarget).parent().attr('offset', offset)
                }
                $(event.currentTarget).parent().parent().find(".ks_new_text")[0].innerText = offset+1;

            }

            $('.o_filter_menu').removeClass('ks_d_block')
            var self = this;
            var account_id = $(ev).data('bsAccountId');

            var td = $(ev).next('tr').find('td');
if (td.length == 1 || $(event.target).hasClass('ks_py-mline-page')) {
                self.ksGetGlLineByPage(offset, account_id).then(function (datas) {
                    Object.entries(datas[2]).forEach(([v, k]) => {
                        var ksFormatConfigurations = {
                            currency_id: k.company_currency_id,
                            noSymbol: true,
                        };
                        k.debit = self.ksFormatCurrencySign(k.debit, ksFormatConfigurations, k.debit < 0 ? '-' : '');
                        k.credit = self.ksFormatCurrencySign(k.credit, ksFormatConfigurations, k.credit < 0 ? '-' : '');
                        k.balance = self.ksFormatCurrencySign(k.balance, ksFormatConfigurations, k.balance < 0 ? '-' : '');
                        k.initial_balance = self.ksFormatCurrencySign(k.initial_balance, ksFormatConfigurations, k.initial_balance < 0 ? '-' : '');
                        if(k.lcode != 'Initial Balance'){
                            k.ldate = DateTime.fromISO(k.ldate, { zone: 'utc' }).toFormat('yyyy-MM-dd');
                        }
                    });

                    if ($(event.target).hasClass('ks_py-mline-page')) {
                        const content = renderToElement('ks_df_gl_subsection', {
                                count: datas[0],
                                self: self,
                                offset: datas[1],
                                account_data: datas[2],
                                ks_enable_ledger_in_bal: self.ks_enable_ledger_in_bal,
                            })
                        $('.ks_py-mline-page').removeClass('ks_high_light_page')
                        $(event.target).parent().parent().next('div').replaceWith(content)
                        $(event.target).addClass('ks_high_light_page')
                    }else {
                        $(ev).next('tr').find('td .ks_py-mline-table-div').remove();
                        const content = renderToElement('ks_df_gl_subsection', {
                                count: datas[0],
                                self: self,
                                offset: datas[1],
                                account_data: datas[2],
                                ks_enable_ledger_in_bal: self.ks_enable_ledger_in_bal,
                            })
                        $(ev).next('tr').find('td ul').after(content)
                        $(event.currentTarget).next('tr').find('td ul li:first a').addClass("ks_high_light_page")
                    }


                    $(ev).next('tr').find('td ul li:first a').css({
                        'background-color': '#00ede8',
                        'font-weight': 'bold',
                    });
                })
        }
        }




    async ksGetPlLinesByPage(offset, account_id) {
            var self = this;
            var lines = await this.orm.call("ks.dynamic.financial.reports", 'ks_build_detailed_move_lines', [this.props.action.context.id, offset, account_id, self.ks_df_report_opt, self.$ks_searchview_buttons.find('.ks_search_account_filter').length])
            return Promise.resolve(lines);

        }

    async ksGetPlMoveLines(event) {


            var ev = event.currentTarget
             $('.o_filter_menu').removeClass('ks_d_block')

             var offset = 0;
            if ($(event.target).hasClass('ks_load_previous_new')){
                var offset = parseInt($(event.currentTarget).parent().attr('offset'));
                offset = offset-1;
                if(offset >= 0){
                    $(event.currentTarget).parent().attr('offset', offset)
                }else{
                    var total_pages = parseInt($(event.currentTarget).parent().attr('total_pages'));
                    offset = total_pages-1;
                    $(event.currentTarget).parent().attr('offset', offset)
                }
                $(event.currentTarget).parent().parent().find(".ks_new_text")[0].innerText = offset+1;
            }
            else if ($(event.target).hasClass('ks_load_next_new')){
                var offset = parseInt($(event.currentTarget).parent().attr('offset'));
                offset = offset+1;
                var total_pages = parseInt($(event.currentTarget).parent().attr('total_pages'));
                if(offset < total_pages){
                    $(event.currentTarget).parent().attr('offset', offset)
                }else{
                    offset = 0;
                    $(event.currentTarget).parent().attr('offset', offset)
                }
                $(event.currentTarget).parent().parent().find(".ks_new_text")[0].innerText = offset+1;
            }

            event.preventDefault();
            var self = this;
            var account_id = $(ev).data('bsAccountId');
            var td = $(ev).next('tr').find('td');
            if (td.length == 1 || $(event.target).hasClass('ks_py-plline-page')) {
                self.ksGetPlLinesByPage(offset, account_id).then(function (datas) {
                     Object.entries(datas[2]).forEach(([v, k]) => {
                        var ksFormatConfigurations = {
                            currency_id: k.company_currency_id,
                            noSymbol: true,
                        };
                        k.debit = self.ksFormatCurrencySign(k.debit, ksFormatConfigurations, k.debit < 0 ? '-' : '');
                        k.credit = self.ksFormatCurrencySign(k.credit, ksFormatConfigurations, k.credit < 0 ? '-' : '');
                        k.balance = self.ksFormatCurrencySign(k.balance, ksFormatConfigurations, k.balance < 0 ? '-' : '');
                        k.initial_balance = self.ksFormatCurrencySign(k.initial_balance, ksFormatConfigurations, k.initial_balance < 0 ? '-' : '');
                        if(k.move_name!='Ending Balance' && k.lcode != 'Initial Balance'){
                            k.ldate = DateTime.fromISO(k.ldate, { zone: 'utc' }).toFormat('yyyy-MM-dd');
                        }
                    });


                    if ($(event.target).hasClass('ks_py-plline-page')) {
                        $(event.target).next('tr').find('td .ks_py-mline-table-div').remove();
                        const content = renderToElement('ks_df_sub_pl0', {
                                count: datas[0],
                                self: self,
                                offset: datas[1],
                                account_data: datas[2],
                                ks_enable_ledger_in_bal: self.ks_enable_ledger_in_bal,
                                lang: self.ks_df_context.lang
                            })
                        $(event.target).parent().parent().next('div').replaceWith(content)
                    }else {
                        $(event.currentTarget).next('tr').find('td .ks_py-mline-table-div').remove();
                        const content = renderToElement('ks_df_sub_pl0', {
                            count: datas[0],
                            self: self,
                            offset: datas[1],
                            account_data: datas[2],
                            ks_enable_ledger_in_bal: self.ks_enable_ledger_in_bal,
                            lang: self.ks_df_context.lang
                        })

                        $(ev).next('tr').find('td ul').after(content)

                    }
                    $(ev).next('tr').find('td ul li:first a').css({
                        'background-color': '#00ede8',
                        'font-weight': 'bold',
                    });
                })
        }
        }

        async OnClickDate(bsFilter) {

                var self=this
                var option_value = bsFilter;
                self.ks_df_report_opt.print_detailed_view = false;
                self.ks_df_context.ks_option_enable = false;
                self.ks_df_context.ks_journal_enable = false
                self.ks_df_context.ks_account_enable = false
                self.ks_df_context.ks_account_both_enable = false
                var ks_options_enable = false
                if (!$(event.currentTarget).hasClass('selected')){
                    var ks_options_enable = true
                    if(option_value == 'ks_report_with_lines' && !self.ks_df_context.print_detailed_view){
                    self.ks_df_report_opt.print_detailed_view = true;
                    }
                }
                var ks_temp_arr = []
                var ks_options = $(event.currentTarget)
                for (var i=0; i < ks_options.length; i++){
                    if (ks_options[i].dataset.filter !== option_value){
                        ks_temp_arr.push($(ks_options[i]).hasClass('selected'))
                    }
                }
                if (ks_temp_arr.indexOf(true) !== -1 || ks_options_enable){
                    self.ks_df_context.ks_option_enable = true;
                }else{
                    self.ks_df_context.ks_option_enable = false;
                }

                if(option_value=='ks_comparison_range'){
                    var ks_date_range_change = {}
                    ks_date_range_change['ks_comparison_range'] =!self.ks_df_report_opt[option_value]
                    return await this.orm.call("ks.dynamic.financial.reports", 'write', [this.props.action.context.id, ks_date_range_change], {
                        context: this.props.action.context
                }).then((data) => {
                    this.orm.call("ks.dynamic.financial.reports", 'ks_reload_page').then((data) => {
                        return self.action.doAction(data);
                    });
                });

                }
                else if(option_value!='ks_comparison_range'){
                    self.ks_df_report_opt[option_value]= !self.ks_df_report_opt[option_value]
                }
                if (option_value === 'unfold_all') {
                    self.unfold_all(self.ks_df_report_opt[option_value]);
                }

                const result = await this._ksRenderBody();
                $('.collapse').removeClass("show");
                $('.ks_py-mline-table-div').remove();
                this.setReportValues(result)
            }

        async OnChangeComp(bsFilter) {

                var self = this

                self.ks_df_context.ks_option_enable = false;
                self.ks_df_context.ks_journal_enable = false
                self.ks_df_context.ks_account_enable = false
                self.ks_df_context.ks_account_both_enable = false
                self.ks_df_report_opt.ks_differ.ks_differentiate_filter = bsFilter;
                if (self.ks_df_report_opt.ks_differ.ks_differentiate_filter == "no_differentiation") {
                    self.ks_df_report_opt.ks_diff_filter.ks_diff_filter_enablity = false
                    self.ks_df_report_opt.ks_diff_filter.ks_debit_credit_visibility = true
                }
                if (self.ks_df_report_opt.ks_differ.ks_differentiate_filter != "no_differentiation") {
                    self.ks_df_report_opt.ks_diff_filter.ks_diff_filter_enablity = true
                    self.ks_df_report_opt.ks_diff_filter.ks_debit_credit_visibility = false
                }
                var error = false;
                var number_period = $(event.currentTarget).parent().parent().find('input[name="periods_number"]')
                self.ks_df_report_opt.ks_differ.ks_no_of_interval = (number_period.length > 0) ? parseInt(number_period.val()) : 1;
                if(this.props.date_from_cmp.toISODate==''){
                    error = true;
                }
                if (bsFilter === 'custom') {
                    var ks_start_date = '';
                    var ks_end_date = '';
                    if (this.props.date_from_cmp != ''){
                        ks_start_date = this.props.date_from_cmp.toISODate('yyyy-M-d')
                    }
                    if (this.props.date_to_cmp != ''){
                        ks_end_date = this.props.date_to_cmp.toISODate('yyyy-M-d')
                    }

                    if (ks_start_date.length > 0) {
                        error = ks_start_date === "" || ks_end_date === "";
                        self.ks_df_report_opt.ks_differ.ks_start_date = ks_start_date;
                        self.ks_df_report_opt.ks_differ.ks_end_date = ks_end_date;
                    } else {
                        error = ks_end_date === "";
                        if (!error){
                        self.ks_df_report_opt.ks_differ.ks_end_date = ks_end_date;
                        }
                    }
                }
//                if (error) {
                if (error) {
                this.dialogService.add(AlertDialog, {
                title: _t('Odoo Warning'),
                body: _t("Date cannot be empty."),
                confirmLabel: _t('Ok'),
                 });
                 return
//                    new WarningDialog(self, {
//                        title: _t("Odoo Warning"),
//                    }, {
//                        message: _t("Date cannot be empty")
//                    }).open();
                } else {
                    const result = await self._ksRenderBody();
                    this.setReportValues(result)
                }
            }

        async js_account_report_group_choice_filter(bsFilter,bsMemberIds) {
                var option_value = bsFilter;
                var option_member_ids = bsMemberIds || [];
                var is_selected = $(this).hasClass('selected');
                Object.entries(self.ks_df_report_opt[option_value]).forEach((el) => {
                    // if group was selected, we want to uncheck all
                    el.selected = !is_selected && (option_member_ids.indexOf(Number(el.id)) > -1);
                });
                const result = await self._ksRenderBody();
                this.setReportValues(result)
            }

        onKsSearchFilter(){
            var ks_input = event.currentTarget.value;
            var ks_filter = ks_input.toUpperCase();
            var ks_accounts = $(event.currentTarget.parentElement).find('.js_account_report_choice_filter');
            for (var i = 0; i < ks_accounts.length; i++) {
                var txtValue = ks_accounts[i].textContent || ks_accounts[i].innerText;
                if (txtValue.toUpperCase().indexOf(ks_filter) > -1) {
                    $($(event.currentTarget.parentElement).find('.js_account_report_choice_filter')[i]).removeClass('ks_d_none')
                } else {
                    $($(event.currentTarget.parentElement).find('.js_account_report_choice_filter')[i]).addClass('ks_d_none')
                }
            }
        }

        async js_account_report_choice_filter(bsId,bsFilter) {
                var self = this
                self.ks_df_context.ks_journal_enable = false
                self.ks_df_context.ks_account_enable = false
                self.ks_df_context.ks_account_both_enable = false

                self.ks_df_context.ks_option_enable = false;

                var option_value = bsFilter;
                var option_id = bsId;

                if (!$(event.currentTarget).hasClass('selected')){
                    var ks_options_enable = true
                }
                var ks_temp_arr = []
                var ks_options = $(event.currentTarget).find('a')
                for (var i=0; i < ks_options.length; i++){
                    if (parseInt(ks_options[i].dataset.bsId) !== option_id){
                        ks_temp_arr.push($(ks_options[i]).hasClass('selected'))
                    }
                }
                if (option_value === 'account'){
                    if (ks_temp_arr.indexOf(true) !== -1 || ks_options_enable){
                        self.ks_df_context.ks_account_enable = true;
                    }
                }
                if (option_value === 'journals'){
                    if (ks_temp_arr.indexOf(true) !== -1 || ks_options_enable){
                        self.ks_df_context.ks_journal_enable = true;
                    }
                }
                if (option_value === 'account_type'){
                    if (ks_temp_arr.indexOf(true) !== -1 || ks_options_enable){
                        self.ks_df_context.ks_account_both_enable = true;
                    }
                }

//
                self.ks_df_report_opt[option_value].filter((el) => {
                if ('' + el.id == '' + option_id) {
                    if (el.selected === undefined || el.selected === null) {
                        el.selected = false;
                    }
                    el.selected = !el.selected;
                } else if (option_value === 'ir_filters') {
                    el.selected = false;
                }
                return el;
            });

                const result = await self._ksRenderBody();
                this.setReportValues(result)
            }


        async ksgetaction() {

            event.stopPropagation();
            var self = this;
            var action = $(event.target).attr('action');
            var id = $(event.target).parents('td').data('bsAccountId') || $(event.target).parents('td').data('bsMoveId');
            var params = $(event.target).data();
//            var context = new Context(this.ks_df_context, {}, {
//                active_id: id
//            });

//            params = _.omit(params, 'actionContext');
            if (action) {
                this.orm.call('ks.dynamic.financial.reports', action, [this.props.action.context.id,
        this.ks_df_report_opt,params],{context:this.props.action.context}).then((result) => {

        return self.action.doAction(result);

        });

            }
        }
        getMultiRecordSelectorProps(resModel, optionKey) {
        return {
            resModel,
            resIds:this.ks_df_report_opt.ks_partner_ids,
            update: (event) => {
                 this.ksPerformOnchange(event);
            },

        };
    }

    getMultiRecordSelectoraccount(resModel, optionKey) {
        return {
            resModel,
            resIds:this.ks_df_report_opt.analytic_accounts || [],
            update: (event) => {
                this.ksPerformOnchangeaccount(event);

            },

        };
    }
    async ksPerformOnchange(ev){
            await this._ksPerformOnchange(ev)
            this.render()
    }
    async _ksPerformOnchange(ev){
            var self = this;
            self.ks_df_report_opt.ks_partner_ids = ev;
//            self.ks_df_report_opt.analytic_accounts = ev.data.ks_analytic_ids;
//            self.ks_df_report_opt.analytic_tags = ev.data.ks_analytic_tag_ids;
            const result = await this._ksRenderBody();
            this.props
            this.setReportValues(result)
        }
    async ksPerformOnchangeaccount(ev){
            await this._ksPerformOnchangeaccount(ev)
            this.render()
    }
    async _ksPerformOnchangeaccount(ev){
            var self = this;
//            self.ks_df_report_opt.ks_partner_ids = ev;
            self.ks_df_report_opt.analytic_accounts = ev;
            const result = await this._ksRenderBody();
            this.setReportValues(result)


        }
}

ksDynamicReportsWidget.components = {
    ControlPanel,
    DropdownItem,
    Dropdown,
    DateTimeInput,MultiRecordSelector
};
ksDynamicReportsWidget.customizableComponents = {

};
ksDynamicReportsWidget.template = "ks_tax_report_lines";
actionRegistry.add('ks_dynamic_report', ksDynamicReportsWidget);

//});


$(document).ready(function() {
    $(document).on('click', 'header .o_main_navbar', function(evt) {
        $('.o_filter_menu').removeClass('ks_d_block')
    });
});
















