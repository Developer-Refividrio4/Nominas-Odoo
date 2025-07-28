/** @odoo-module **/

import { registry } from "@web/core/registry";
const actionRegistry = registry.category("actions");
import { Component, onWillStart } from "@odoo/owl";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { ksDynamicReportsWidget } from "@ks_dynamic_financial_report/js/ks_dynamic_financial_report";
import { patch } from "@web/core/utils/patch";

patch(ksDynamicReportsWidget.prototype,{
    setup() {
    super.setup();
    this.selectedOption1 = null;
    this.selectedOption2 = null;
    this.selectedOption3 = null;
    this.selectedOption4 = null;
    this.isApplied = false;
    },

    onClickRowTrialBalance(event){
        var ev = event.currentTarget
        event.preventDefault();
        var child_tr = $(ev).next('tr');
        const clickedRow = event.target
        const rowIndex = Array.from(ev.parentElement.children).indexOf(ev);

        const clickedLevel = $(ev).data('level');
        const clickedLevelRows = $(ev).data('rows');
        var is_closed = ev.classList.contains('is_closed');
        var is_open = ev.classList.contains('is_open');
        const rows = Array.from(document.querySelectorAll("#trial_balance_table > tbody > tr"));

          for (let i = rowIndex + 1; i < rowIndex + clickedLevelRows; i++) {
            const row = rows[i];
            const levelValue = row.getAttribute('data-level');
            if(is_closed){
                if (levelValue == clickedLevel+1) {
                  if (row.classList.contains('d-none')) {
                    row.classList.remove('d-none');
                  }
                }
            }else{
                if (!row.classList.contains('d-none')) {
                    row.classList.add('d-none');
                  }
            }

          }
          if(is_closed){
                ev.classList.remove('is_closed');
                ev.classList.add('is_open');
            }else{
                ev.classList.add('is_closed');
                ev.classList.remove('is_open');
            }
    },

    onClickRow(event){
        var ev = event.currentTarget
            event.preventDefault();
            var child_tr = $(ev).next('tr');
          const clickedRow = event.target
          const rowIndex = Array.from(ev.parentElement.children).indexOf(ev);

          const clickedLevel = $(ev).data('level');
          const clickedLevelRows = $(ev).data('rows');
          var is_closed = ev.classList.contains('is_closed');
          var is_open = ev.classList.contains('is_open');
          const rows = Array.from(document.querySelectorAll("#general_ledger_table > tbody > tr"));

          for (let i = rowIndex + 1; i <= rowIndex + clickedLevelRows; i++) {
            const row = rows[i];
            const levelValue = row.getAttribute('data-level');
            if(is_closed){
                if (levelValue == clickedLevel+1) {
                  if (row.classList.contains('d-none')) {
                    row.classList.remove('d-none');
                  }
                }
            }else{
                if (!row.classList.contains('d-none')) {
                    row.classList.add('d-none');
                  }
            }

          }
          if(is_closed){
                ev.classList.remove('is_closed');
                ev.classList.add('is_open');
            }else{
                ev.classList.add('is_closed');
                ev.classList.remove('is_open');
            }
    },

    async ksGetMoveLines(event) {
        super.ksGetMoveLines(event);
        var ev = event.currentTarget
        event.preventDefault();

        if ($(ev).next('tr').hasClass('d-none')) {
            $(ev).next('tr').removeClass('d-none');
        }
    },

    async OnClickDate(bsFilter) {

        var self=this
        var option_value = bsFilter;
        self.ks_df_report_opt.print_detailed_view = false;
        if(option_value=='show_hierarchy'){
            this.ks_df_report_opt.show_hierarchy = !this.ks_df_report_opt.show_hierarchy;
        }
        if(option_value=='show_ce'){
            this.ks_df_report_opt.show_ce = !this.ks_df_report_opt.show_ce;
        }
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
        else if(option_value!='ks_comparison_range' && option_value!='show_hierarchy' && option_value!='show_ce'){
            self.ks_df_report_opt[option_value]= !self.ks_df_report_opt[option_value]
        }
        if (option_value === 'unfold_all') {
            self.unfold_all(self.ks_df_report_opt[option_value]);
        }

        const result = await this._ksRenderBody();
        this.setReportValues(result)
    },

    async openWizard() {

        var self = this;
        this.orm.call("ks.dynamic.financial.reports", 'ks_get_xml_cfdi', [this.props.action.context.id, this.ks_df_report_opt, this.selectedOption1, this.selectedOption2, this.selectedOption3, this.selectedOption4], {
            context: this.props.action.context
        }).then((data) => {
            return self.action.doAction(data);
        });

    },
    async OnNewFunction(optionValue, event) {
        const optionsMap = {
            'ks_catalog_cuentas': 'selectedOption1',
            'ks_balanza_comprobacion': 'selectedOption1',
            'ks_normal': 'selectedOption2',
            'ks_complenmentaria': 'selectedOption2',
            'ks_mes_13': 'selectedOption3',
        };

        const selectedOption = optionsMap[optionValue];
        if (selectedOption) {
             this[selectedOption] = this[selectedOption] === optionValue ? null : optionValue;
             this.isApplied = false;
        }

        const result = await this._ksRenderBody();
        this.setReportValues(result);
    },

    async OnNewDate(e){
        this.selectedOption4 = e;

        if(this.selectedOption4 != null){
            this.selectedOption4 = this.selectedOption4;
        }

        const result = await this._ksRenderBody();
        this.setReportValues(result);
    },

    async ksgetaction() {
    if (this.isApplied === true) {
        return;
    }
    return super.ksgetaction();
}

});
