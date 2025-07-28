# -*- coding: utf-8 -*-
from odoo.http import request, route
from odoo import http
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.point_of_sale.controllers.main import PosController

class WebsiteSaleExtend(WebsiteSale):

    def _get_mandatory_fields_billing(self, country_id=False):
        field_list = super(WebsiteSaleExtend, self)._get_mandatory_fields_billing(country_id)
        field_list.append('zip')
        return field_list

    def _get_mandatory_fields_shipping(self, country_id=False):
        field_list = super(WebsiteSaleExtend, self)._get_mandatory_fields_shipping(country_id)
        field_list.append('zip')
        return field_list

    def values_postprocess(self, order, mode, values, errors, error_msg):
        res = super(WebsiteSaleExtend, self).values_postprocess(order, mode, values, errors, error_msg)
        if values.get('uso_cfdi'):
            order.write({'uso_cfdi_id': http.request.env['catalogo.uso.cfdi'].sudo().search([('code','=',values.get('uso_cfdi'))], limit=1).id })
            res[0].update({'uso_cfdi_id': http.request.env['catalogo.uso.cfdi'].sudo().search([('code','=',values.get('uso_cfdi'))], limit=1).id })
        if values.get('vat'):
            order.partner_id.write({'vat':values.get('vat')})
            res[0].update({'vat': values.get('vat')})
        return res


class FacturaCliente(http.Controller):
    
    @http.route('/portal/facturacliente/', auth='public', website=True)
    def index(self, **kw):
        return http.request.render('website_self_cfdi_invoice.index',
            {
                'fields': ['RFC','Folio',],
            })

    @http.route('/portal/facturacliente/rfc',type="http", auth="public", csrf=False, website=True)
    def my_fact_portal_check(self, **kwargs):
        rfc_partner = kwargs.get('rfc_partner')
        order_number = kwargs['order_number'] or False
        monto_total = kwargs.get('monto_total',0)

        partner_obj = http.request.env['res.partner']
        sale_obj =  http.request.env['sale.order']

        partner_obj = partner_obj.sudo()
        partner_exist = partner_obj.search([('vat', '=', rfc_partner)],limit=1)

        enable_pos = False
        module = http.request.env['ir.module.module'].sudo().search([('name','=','custom_invoice')])
        if module and module.state == 'installed':
            enable_pos = True
            pos_obj =  http.request.env['pos.order']

        if partner_exist:
            sale_obj = sale_obj.sudo()
            sale_order_exist = sale_obj.search([('partner_id','in',partner_exist.ids), ('name', '=', order_number), ('amount_total','like', monto_total.replace(',',''))], limit=1)

            if sale_order_exist:
                return http.request.render('website_self_cfdi_invoice.facturacion', 
                                                                            {
                                                                            'partner_name': sale_order_exist.partner_id.name,
                                                                            'cp_post': sale_order_exist.partner_id.zip or False,
                                                                            'correo_electronico': sale_order_exist.partner_id.email or False,
                                                                            'uso_del_cfdi': sale_order_exist.partner_id.uso_cfdi_id.code or False,
                                                                            'regimen_fiscal': sale_order_exist.partner_id.regimen_fiscal_id.code or False
                                                                            })
            elif enable_pos:
                pos_obj = pos_obj.sudo()
                pos_order_exist = pos_obj.search([('pos_reference', '=', order_number), ('amount_total','=', monto_total.replace(',',''))],limit=1)
                if not pos_order_exist:
                   pos_order_exist = pos_obj.search([('ticket_code', '=', order_number), ('amount_total','=', monto_total.replace(',',''))],limit=1)
                if pos_order_exist:
                    return http.request.render('website_self_cfdi_invoice.facturacion',
                                                                            {
                                                                            'partner_name': partner_exist.name,
                                                                            'cp_post': partner_exist.zip or False,
                                                                            'correo_electronico': partner_exist.email or False,
                                                                            'uso_del_cfdi': partner_exist.uso_cfdi_id.code or False,
                                                                            'regimen_fiscal': partner_exist.regimen_fiscal_id.code or False
                                                                            })
                else:
                    return http.request.render('website_self_cfdi_invoice.html_result_error_inv', {'errores':['No se encontró el pedido o ticket de venta o el monto no coincide con el pedido.']})
            else:
                return http.request.render('website_self_cfdi_invoice.html_result_error_inv', {'errores':['No se encontró el pedido de venta. Debe revisar monto, RFC y número del pedido.']})
        else:
            if enable_pos:
                pos_obj = pos_obj.sudo()
                pos_order_exist = pos_obj.search([('pos_reference', '=', order_number), ('amount_total','like', monto_total.replace(',',''))],limit=1)
                if not pos_order_exist:
                   pos_order_exist = pos_obj.search([('ticket_code', '=', order_number), ('amount_total','like', monto_total.replace(',',''))],limit=1)
                if pos_order_exist:
                   return http.request.render('website_self_cfdi_invoice.facturacion', {})
                else:
                   return http.request.render('website_self_cfdi_invoice.html_result_error_inv', {'errores':['No se encontró el ticket de venta. Debe revisar monto y número del pedido.']})
            else:
               return http.request.render('website_self_cfdi_invoice.html_result_error_inv', {'errores':['No se encontró el pedido de venta. Debe revisar monto, RFC y número del pedido.']})


    @http.route('/portal/facturacliente/results/', type="http", auth="public", csrf=False, website=True)
    def my_fact_portal_insert(self, **kwargs):
        ### Esta linea implementa los Captcha en el Portal ####
        # if kwargs.has_key('g-recaptcha-response') and request.website.is_captcha_valid(kwargs['g-recaptcha-response']):
        partner = request.env.user.partner_id
        rfc_partner = kwargs['rfc_partner'] or (partner.vat and partner.vat.replace('MX', '')) or False
        order_number = kwargs['order_number'] or False
        mail_to = kwargs.get('mail_to', False)
        ticket_pos = kwargs.get('ticket_pos', False)
        monto_total = kwargs.get('monto_total', 0)

        partner_name = kwargs.get('partner_name', False)
        correo_electronico = kwargs.get('correo_electronico', False)
        cp_post = kwargs.get('cp_post', False)
        regimen_fiscal = kwargs.get('regimen_fiscal', False)
        uso_del_cfdi = kwargs.get('uso_del_cfdi', False)
        if 'ticket_pos' in kwargs:
            ticket_pos = kwargs['ticket_pos'] or True
        else:
            ticket_pos = False
        auto_invoice_obj = http.request.env['website.self.invoice.web'].sudo()
        partner_obj = http.request.env['res.partner']
        partner_obj = partner_obj.sudo()
        partner_exist = partner_obj.search([('vat', '=', rfc_partner.upper())], limit=1)
        partner_vals = {}
        #if partner_name:
        #    partner_vals.update({'name': partner_name})
        if rfc_partner and correo_electronico and monto_total and order_number:
            if partner_exist:
                if partner_exist.email != correo_electronico:
                    if partner_exist.email:
                        partner_vals.update({'email' : partner_exist.email + '; ' + correo_electronico})
                    else:
                        partner_vals.update({'email' : correo_electronico})
                partner_vals.update({'name' : partner_name})
                partner_vals.update({'uso_cfdi_id' : http.request.env['catalogo.uso.cfdi'].sudo().search([('code','=',uso_del_cfdi)], limit=1).id })
                partner_vals.update({'regimen_fiscal_id': http.request.env['catalogo.regimen.fiscal'].sudo().search([('code','=',regimen_fiscal)], limit=1).id })
                partner_vals.update({'zip' : cp_post})
                partner_exist.write(partner_vals)
            else:
                if partner_name:
                    partner_vals.update({'name' : partner_name})
                    partner_vals.update({"vat" : rfc_partner.upper()})
                    partner_vals.update({'uso_cfdi_id' : http.request.env['catalogo.uso.cfdi'].sudo().search([('code','=',uso_del_cfdi)], limit=1).id })
                    partner_vals.update({'email' : correo_electronico})
                    partner_vals.update({'regimen_fiscal_id' : http.request.env['catalogo.regimen.fiscal'].sudo().search([('code','=',regimen_fiscal)], limit=1).id })
                    partner_vals.update({'country_id' : http.request.env['res.country'].sudo().search([('code','=','MX')], limit=1).id })
                    partner_vals.update({'zip' : cp_post})
                    partner_exist = partner_obj.create(partner_vals)
                else:
                    return http.request.render('website_self_cfdi_invoice.html_result_error_inv', {'errores':['Es un usuario nuevo por lo que tiene que ingresar el nombre.']})
        else:
            return http.request.render('website_self_cfdi_invoice.html_result_error_inv', {'errores':['Es necesario llenar los campos obligatorios.']})

        #### Si tenemos datos de una consulta previa los retornamos
        request_preview = auto_invoice_obj.search([('rfc_partner','=',rfc_partner.upper()),('order_number','=',order_number),('state','=','done')])
        if request_preview:
            attachment_obj = http.request.env['website.self.invoice.web.attach'].sudo()
            attachments = attachment_obj.search([('website_auto_id', '=', request_preview[0].id)])
            return http.request.render('website_self_cfdi_invoice.html_result_thnks',
                                       {
                                           'attachments': attachments,
                                       })
        if not rfc_partner or not order_number: # or not mail_to:
            return http.request.render('website_self_cfdi_invoice.html_result_error_inv', {'errores':['Los campos marcados con un ( * ) son Obligatorios.']})
        auto_invoice_id = auto_invoice_obj.create({
            'rfc_partner': rfc_partner.upper(),
            'order_number': order_number,
            'monto_total': float(monto_total.replace(',','')),
            'uso_cfdi' : uso_del_cfdi,
            'ticket_pos': ticket_pos,
            'partner_id': partner_exist.id,
        })
        attachment_obj = http.request.env['website.self.invoice.web.attach']
        attachments = attachment_obj.search([('website_auto_id','=',auto_invoice_id.id)])
        if auto_invoice_id.error_message:
            return http.request.render('website_self_cfdi_invoice.html_result_error_inv', {'errores':[auto_invoice_id.error_message]})
        return http.request.render('website_self_cfdi_invoice.html_result_thnks', 
                                                                            {
                                                                            'attachments': attachments,
                                                                            })

    @http.route('/portal/consulta_factura/',type="http", auth="user", csrf=False, website=True)
    def request_invoice(self, **kwargs):
        if not kwargs:
            return http.request.render('website_self_cfdi_invoice.index',
                                       {
                                           'fields': ['RFC', 'Folio', ],
                                       })
        partner = request.env.user.partner_id.sudo()
        rfc_partner = kwargs['rfc_partner'] or (partner.vat and partner.vat.replace('MX', '')) or False
        order_number = kwargs['order_number'] or False
        monto_total = kwargs.get('monto_total', 0)

        auto_invoice_obj = http.request.env['website.self.invoice.web'].sudo()
        try:
            auto_invoice = auto_invoice_obj.search([('order_number', '=', order_number),
                                                    ('rfc_partner', '=', rfc_partner.upper())])
            if auto_invoice:
                attachment_obj = http.request.env['website.self.invoice.web.attach'].sudo()
                attachments = attachment_obj.search([('website_auto_id','=',auto_invoice[0].id)])
                return http.request.render('website_self_cfdi_invoice.html_result_thnks', 
                                                                                    {
                                                                                    'attachments': attachments,
                                                                                    })
            else:
                error_message = "Su solicitud no pudo ser procesada.\nNo existe informacion para el Pedido %s." % order_number
                return http.request.render('website_self_cfdi_invoice.html_result_error_inv', {'errores':[error_message]})

        except:
            error_message = "Su solicitud no pudo ser procesada.\nLa informacion introducida es incorrecta."
            return http.request.render('website_self_cfdi_invoice.html_result_error_inv', {'errores':[error_message]})

        return http.request.render('website_self_cfdi_invoice.index',
            {
                'fields': ['RFC','Folio',],
            })

class WebsiteAccount(CustomerPortal):

    OPTIONAL_BILLING_FIELDS = ["zipcode", "state_id", "vat", "company_name", "uso_cfdi_id", "regimen_fiscal_id"]

    @route(['/my/account'], type='http', auth='user', website=True)
    def account(self, redirect=None, **post):
        if post and request.httprequest.method == 'POST':
            if post.get('uso_cfdi', False):
                post.update({
                    'uso_cfdi_id': http.request.env['catalogo.uso.cfdi'].sudo().search([('code','=',post.get('uso_cfdi'))]).id,
                })
                post.pop('uso_cfdi')
            if post.get('regimen_fiscal_id', False):
                post.update({
                    'regimen_fiscal_id': http.request.env['catalogo.regimen.fiscal'].sudo().search(
                        [('code', '=', post.get('regimen_fiscal_id'))]).id,
                })
        return super(WebsiteAccount, self).account(redirect, **post)

class PosAccount(PosController):

    @http.route(['/pos/ticket/validate'], type='http', auth="public", website=True, sitemap=False)
    def show_ticket_validation_screen(self, access_token='', **kwargs):
        if kwargs and kwargs.get('uso_cfdi', False):
            kwargs.update({
                'uso_cfdi_id': http.request.env['catalogo.uso.cfdi'].sudo().search(
                    [('code', '=', kwargs.get('uso_cfdi'))]).id,
            })
            kwargs.pop('uso_cfdi')
        if kwargs and kwargs.get('regimen_fiscal_id', False):
            kwargs.update({
                'regimen_fiscal_id': http.request.env['catalogo.regimen.fiscal'].sudo().search(
                    [('code', '=', kwargs.get('regimen_fiscal_id'))]).id,
            })
        return super(PosAccount, self).show_ticket_validation_screen(access_token=access_token, **kwargs)

    def _get_invoice(self, partner_values, invoice_values, pos_order, additional_invoice_fields, kwargs):
        value = additional_invoice_fields.extend([request.env['ir.model.fields']._get('account.move', 'uso_cfdi_id'),request.env['ir.model.fields']._get('account.move', 'methodo_pago'),request.env['ir.model.fields']._get('account.move', 'tipo_comprobante'),request.env['ir.model.fields']._get('account.move', 'forma_pago_id')])
        invoice_values['uso_cfdi_id']=kwargs.get('uso_cfdi_id')
        invoice_values['methodo_pago'] = 'PUE'
        invoice_values['tipo_comprobante'] = 'I'
        invoice_values['forma_pago_id'] = pos_order.payment_ids[0].payment_method_id.forma_pago_id.id
        return super(PosAccount, self)._get_invoice(partner_values, invoice_values, pos_order, additional_invoice_fields, kwargs)
