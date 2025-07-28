/** @odoo-module */

import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { _t } from "@web/core/l10n/translation";

export class CDFIDetailPopupWidget extends AbstractAwaitablePopup {
    static template = "CDFIDetailPopupWidget";
    static defaultProps = {
        confirmText: _t("Confirmar"),
        cancelText: _t("Cancelar"),
        body: "",
        list: [],
        confirmKey: false,
    };

     async confirm() {
        var order = this.env.services.pos.get_order()

       // var forma_pago  = document.getElementsByClassName("js_forma_pago")[0]
       // var methodo_pago = document.getElementsByClassName("js_methodo_pago")[0]
        var uso_cfdi = document.getElementsByClassName("js_uso_cfdi")[0]

        //order.forma_pago_id = forma_pago.value || undefined;
        //order.methodo_pago = methodo_pago.value || undefined;
        order.uso_cfdi_id = uso_cfdi.value || undefined;

        this.props.close({ confirmed: true, payload: null });
     }
     async cancel() {
        this.props.close({ confirmed: false, payload: null });
     }
}

