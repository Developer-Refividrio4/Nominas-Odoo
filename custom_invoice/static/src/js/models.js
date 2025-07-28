/** @odoo-module */

import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";
import { Order } from "@point_of_sale/app/store/models";


patch(PosStore.prototype, {
    // @Override
    async _processData(loadedData) {
        await super._processData(...arguments);
        this.regimen_fiscal = loadedData['catalogo.regimen.fiscal'];
    },
});

patch(Order.prototype, {
       setup(_defaultObj, options) {
            super.setup(...arguments);
          //  this.forma_pago_id = this.forma_pago_id || undefined;
          //  this.methodo_pago = this.methodo_pago || undefined;
            this.uso_cfdi_id = this.uso_cfdi_id || undefined;
       },
       //set_forma_pago(forma_pago_id){
       //     this.forma_pago_id = forma_pago_id;
       //},
       //get_forma_pago(){
       //     return this.forma_pago_id;
       //},
       //set_methodo_pago(methodo_pago){
       //     this.methodo_pago = methodo_pago;
       //},
       //get_methodo_pago(){
       //     return this.methodo_pago;
       //},
       set_uso_cfdi(uso_cfdi_id){
            this.uso_cfdi_id = uso_cfdi_id;
       },
       get_uso_cfdio(){
            return this.uso_cfdi_id;
       },
       clean_empty_paymentlines() {
            var lines = this.paymentlines;
            this.clear_journal_amount_dict = {};
            for ( var i = 0; i < lines.length; i++) {
                if (!lines[i].get_amount()) {
                    this.clear_journal_amount_dict[lines[i].payment_method.id] = lines[i].get_amount();
                }
            }
            return super.clean_empty_paymentlines(...arguments);
        },
       export_as_JSON() {
            const json = super.export_as_JSON(...arguments);
                //json.forma_pago_id = this.forma_pago_id;
                //json.methodo_pago = this.methodo_pago;
                json.uso_cfdi_id = this.uso_cfdi_id;

                if (json.amount_return>0.0){
                    var journal_amount_dict = {};
                    var lines  = this.paymentlines;
                    for (var i = 0; i < lines.length; i++) {
                        journal_amount_dict[lines[i].payment_method.id] = lines[i].get_amount();
                    }
                    if (this.clear_journal_amount_dict){
                        journal_amount_dict = [this.clear_journal_amount_dict, journal_amount_dict].reduce(function (r, o) {
                            Object.keys(o).forEach(function (k) { r[k] = o[k]; });
                            return r;
                        }, {});
                    }

                    json.payment_line_journals= journal_amount_dict;
                }
            return json;
       },
       export_for_printing() {
            const json = super.export_for_printing(...arguments);
          	var order = this.pos.get_order();
            json.headerData.company.regimen_fiscal_id=this.pos.company.regimen_fiscal_id;
            json.headerData.company.zip=this.pos.company.zip;
            json.headerData.company.nombre_fiscal=this.pos.company.nombre_fiscal;
            json.headerData.company.street=this.pos.company.street;
            json.headerData.company.street2=this.pos.company.street2;
            json.headerData.company.city=this.pos.company.city;
            json.headerData.company.state_id=this.pos.company.state_id;
            if(order.invoice_information) {
                json.regimen_fiscal_id = order.invoice_information.regimen_fiscal_id;
                json.regimen_fiscal = order.partner.regimen_fiscal_id[1];
                json.tipo_comprobante = order.invoice_information.tipo_comprobante;
                json.folio_factura = order.invoice_information.folio_factura;
                json.client_name = order.invoice_information.client_name;
                json.client_rfc = order.invoice_information.client_rfc;
                json.uso_cfdi_id = order.invoice_information.uso_cfdi_id;
                json.methodo_pago = order.invoice_information.methodo_pago;
                json.forma_pago_id = order.invoice_information.forma_pago_id;
                json.numero_cetificado = order.invoice_information.numero_cetificado;
                json.moneda = order.invoice_information.moneda;
                json.cetificaso_sat = order.invoice_information.cetificaso_sat;
                json.tipocambio = order.invoice_information.tipocambio;
                json.folio_fiscal = order.invoice_information.folio_fiscal;
                json.fecha_certificacion = order.invoice_information.fecha_certificacion;
                json.cadena_origenal = order.invoice_information.cadena_origenal;
                json.selo_digital_cdfi = order.invoice_information.selo_digital_cdfi;
                json.selo_sat = order.invoice_information.selo_sat;
                json.invoice_id = order.invoice_information.invoice_id;
                json.nombre_fiscal = order.invoice_information.nombre_fiscal;
                json.expedicion = order.invoice_information.expedicion;
            }
            return json;
       },
       init_from_JSON(json) {
            super.init_from_JSON(...arguments);
          //  this.forma_pago_id = json.forma_pago_id;
          //  this.methodo_pago = json.methodo_pago;
            this.uso_cfdi_id = json.uso_cfdi_id;
       },


});
