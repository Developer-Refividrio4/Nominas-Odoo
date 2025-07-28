/** @odoo-module */

import { PartnerDetailsEdit } from "@point_of_sale/app/screens/partner_list/partner_editor/partner_editor";
import { patch } from "@web/core/utils/patch";

patch(PartnerDetailsEdit.prototype, {
    setup(){
        super.setup(...arguments);
        this.changes.regimen_fiscal_id =
                this.props.partner.regimen_fiscal_id &&
                this.props.partner.regimen_fiscal_id[0];
        },
});