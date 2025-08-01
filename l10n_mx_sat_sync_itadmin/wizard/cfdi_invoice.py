# -*- coding: utf-8 -*-

import base64
import json
import os
from lxml import etree

import xmltodict
from dateutil.parser import parse
from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError
from reportlab.graphics.barcode import createBarcodeDrawing
from reportlab.lib.units import mm

from ..models.special_dict import CaselessDictionary

def convert_to_special_dict(d):
    for k, v in d.items():
        if isinstance(v, dict):
            d.__setitem__(k, convert_to_special_dict(CaselessDictionary(v)))
        else:
            d.__setitem__(k, v)
    return d

class CfdiInvoiceAttachment(models.TransientModel):
    _name = 'cfdi.invoice.attachment'
    _description = 'CfdiInvoiceAttachment'

    @api.model
    def _default_journal(self):
        if self._context.get('default_journal_id', False):
            return self.env['account.journal'].browse(self._context.get('default_journal_id'))
        company_id = self._context.get('company_id', self.env.company.id)
        domain = [
            ('type', 'in', ['sale']),
            ('company_id', '=', company_id),
        ]
        return self.env['account.journal'].search(domain, limit=1)

    @api.model
    def _default_supplier_journal(self):
        if self._context.get('default_journal_id', False):
            return self.env['account.journal'].browse(self._context.get('default_journal_id'))
        company_id = self._context.get('company_id', self.env.company.id)
        domain = [
            ('type', 'in', ['purchase']),
            ('company_id', '=', company_id),
        ]
        return self.env['account.journal'].search(domain, limit=1)

    journal_id = fields.Many2one('account.journal', string='Diario de facturas venta',
                                 required=False,
                                 default=_default_journal,
                                 domain="[('type', 'in', ['sale'])]")

    supplier_journal_id = fields.Many2one('account.journal', string='Diario de facturas compras',
                                          required=False,
                                          default=_default_supplier_journal,
                                          domain="[('type', 'in', ['purchase'])]")

    credit_journal_id = fields.Many2one('account.journal', string='Diario de notas de crédito venta',
                                        required=False,
                                        default=_default_journal,
                                        domain="[('type', 'in', ['sale'])]")

    credit_supplier_journal_id = fields.Many2one('account.journal', string='Diario de notas de crédito compra',
                                                 required=False,
                                                 default=_default_supplier_journal,
                                                 domain="[('type', 'in', ['purchase'])]")

    company_id = fields.Many2one('res.company', string='Compañia',
                                 required=True, readonly=True,
                                 default=lambda self: self.env.company)
    si_producto_no_tiene_codigo = fields.Selection(
        [('Crear automatico', 'Crear automatico'), ('Buscar manual', 'Producto por defecto')],
        'Si producto no se encuentra')
    product_id = fields.Many2one("product.product", 'Producto por defecto',
                                 help='Si un producto del XML no se encuentra en la base de datos, utilizará el producto por defecto en vez de crear un nuevo producto.')

    @api.model
    def default_get(self, fields_list):
        res = super(CfdiInvoiceAttachment, self).default_get(fields_list)
        create_set = self.env['ir.config_parameter'].sudo().get_param(
            'l10n_mx_sat_sync_itadmin.si_producto_no_tiene_codigo')
        if create_set:
            res['si_producto_no_tiene_codigo'] = create_set
        return res

    def import_xml_file(self):
        ctx = self._context.copy()
        active_ids = ctx.get('active_ids')
        model = ctx.get('active_model', '')
        if model == 'ir.attachment' and active_ids:
            attachments = self.env[model].browse(active_ids)
            not_imported_attachment = {}
            imported_attachment = []
            existed_attachment = []
            create_invoice_ids = []

            invoice_obj = self.env['account.move']
            cfdi_uuids = attachments.mapped("cfdi_uuid")
            exist_invoices = invoice_obj.search([('l10n_mx_edi_cfdi_uuid', 'in', cfdi_uuids)])
            exist_invoice_uuids = exist_invoices.mapped('l10n_mx_edi_cfdi_uuid')

            create_so_po = ctx.get('create_so_po', False)

            for attachment in attachments:
                cfdi_uuid = attachment.cfdi_uuid
                if not cfdi_uuid:
                    not_imported_attachment.update({attachment.name: 'Archivo adjunto no válido'})
                    continue
                if cfdi_uuid in exist_invoice_uuids:
                    existed_attachment.append(attachment.name)
                    continue
                p, ext = os.path.splitext(attachment.name)

                if ext[1:].lower() != 'xml':
                    not_imported_attachment.update({attachment.name: _(
                        "Formato no soportado \"{}\", importa solo archivos XML").format(attachment.name)})
                    continue

                # file_content = base64.b64decode(attachment.datas)
                try:
                    res = None
                    if attachment.creado_en_odoo:
                        raise UserError("Documento creado previamente en Odoo %s" % (attachment.cfdi_uuid))
                    if create_so_po:
                        if attachment.cfdi_type == 'I':
                            res = self.import_sale_order(attachment.datas)
                        elif attachment.cfdi_type == 'SI':
                            res = self.import_purchase_order(attachment.datas)
                        else:
                            continue
                    else:
                        if attachment.cfdi_type == 'I':
                            res = self.import_customer_invoice(attachment.datas, self.journal_id)
                        elif attachment.cfdi_type == 'SI':
                            res = self.import_supplier_invoice(attachment.datas, self.supplier_journal_id)
                        elif attachment.cfdi_type == 'E':
                            res = self.import_credit_note(attachment.datas, self.credit_journal_id)
                        elif attachment.cfdi_type == 'SE':
                            res = self.import_supplier_credit_note(attachment.datas, self.credit_supplier_journal_id)

                    if res and type(res) == dict:
                        val = {'creado_en_odoo': True, }
                        if res.get('res_model') == 'account.move':
                            val.update({'invoice_ids': [(6, 0, [res.get('res_id')])], 'res_id': res.get('res_id'),
                                        'res_model': 'account.move'})
                            create_invoice_ids.append(res.get('res_id'))
                        attachment.write(val)

                except Exception as e:
                    if hasattr(e, 'name'):
                        not_imported_attachment.update({attachment: e.name})
                    elif hasattr(e, 'message'):
                        not_imported_attachment.update({attachment: e.message})
                    else:
                        not_imported_attachment.update({attachment: str(e)})
                    self.env.cr.rollback()
                    continue
                imported_attachment.append(attachment.name)

            ctx = {'create_invoice_ids': create_invoice_ids}
            if existed_attachment:
                ctx.update({'default_existed_attachment': '<p>' + '<p></p>'.join(existed_attachment) + '</p>'})
            if not_imported_attachment:
                content = ''
                for attachment, error in not_imported_attachment.items():
                    content += '<p>' + attachment.name + ':</p> <p><strong style="color:red;"> Error : </strong> %s </p>' % (
                        error)

                ctx.update({'default_not_imported_attachment': content})  # '<p>'+'<p></p>'.join(not_imported_attachment)+'</p>'

            if imported_attachment:
                ctx.update({'default_imported_attachment': '<p>' + '<p></p>'.join(imported_attachment) + '</p>'})
            return {
                'name': "Resultado de importación",
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'import.invoice.process.message',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': ctx,
            }
        return

    @api.model
    def create_update_partner(self, partner_data, is_customer=True, is_supplier=False):
        domain = []
        vendor_name = partner_data.get('@Nombre')
        rfc = partner_data.get('@Rfc')
        partner_obj = self.env['res.partner']
        vals = {}
        # if vendor_name:
        #    domain.append(('name','=',vendor_name))
        if rfc and hasattr(partner_obj, 'vat'):
            domain.append(('vat', '=', rfc))
            vals.update({'vat': rfc})
        if rfc == 'XAXX010101000' or rfc == 'XEXX010101000':
            domain.append(('name', '=', vendor_name))
        odoo_vendor = partner_obj.search(domain, limit=1)
        if not odoo_vendor:
            vals.update({'name': vendor_name, 'country_id': self.env['res.country'].search([('code','=','MX')],limit=1).id})
            odoo_vendor = partner_obj.create(vals)

        return odoo_vendor

    def import_customer_invoice(self, file_content, journal=False):
        file_coontent = base64.b64decode(file_content)
        file_coontent = file_coontent.replace(b'cfdi:', b'')
        file_coontent = file_coontent.replace(b'tfd:', b'')
        try:
            data = json.dumps(xmltodict.parse(file_coontent))  # force_list=('Concepto','Traslado',)
            data = json.loads(data)
        except Exception as e:
            data = {}
            raise UserError(str(e))

        data = CaselessDictionary(data)
        data = convert_to_special_dict(data)

        invoice_obj = self.env['account.move']
        invoice_line_obj = self.env['account.move.line']
        # product_obj = self.env['product.product']

        # buscar_producto_por_clave_sat = self.env['ir.config_parameter'].sudo().get_param('l10n_mx_sat_sync_itadmin.buscar_producto_por_clave_sat')

        # product_types = dict(product_obj._fields.get('type')._description_selection(product_obj.env))
        # product_type_default = self.env['ir.config_parameter'].sudo().get_param('l10n_mx_sat_sync_itadmin.product_type_default')
        tax_obj = self.env['account.tax']
        partner_data = data.get('Comprobante', {}).get('Receptor', {})
        invoice_line_data = data.get('Comprobante', {}).get('Conceptos', {}).get('Concepto', [])
        if type(invoice_line_data) != list:
            invoice_line_data = [invoice_line_data]

        invoice_date = data.get('Comprobante', {}).get('@Fecha')
        customer_reference = data.get('Comprobante', {}).get('@Serie', '') + data.get('Comprobante', {}).get('@Folio','')
        receptor_data = data.get('Comprobante', {}).get('Receptor', {})
        timbrado_data = data.get('Comprobante', {}).get('Complemento', {}).get('TimbreFiscalDigital', {})
        relacionado_data = data.get('Comprobante', {}).get('CfdiRelacionados', {})

        vendor_uuid = timbrado_data.get('@UUID')

        if vendor_uuid:
            vendor_order_exist = invoice_obj.search([('folio_fiscal', '=', vendor_uuid.lower())], limit=1)
            if not vendor_order_exist:
                vendor_order_exist = invoice_obj.search([('folio_fiscal', '=', vendor_uuid.upper())], limit=1)
            if vendor_order_exist:
                raise UserError("Factura ya existente con ese UUID %s" % (vendor_uuid))

        if customer_reference != '':
            invoice_exist = invoice_obj.search([('ref', '=', customer_reference), ('move_type', '=', 'out_invoice')],
                                               limit=1)
            if invoice_exist:
                customer_reference = ''
        #                raise UserError("Factura ya existente con la referencia del vendedor %s"%(customer_reference))

        ctx = self._context.copy()
        ctx.update({'default_type': 'out_invoice', 'move_type': 'out_invoice'})
        partner = self.create_update_partner(partner_data)
        if not journal:
            journal = invoice_obj.with_context(ctx)._default_journal()
        # journal = invoice_obj.with_context(ctx)._default_journal()

        amount_str = str(data.get('Comprobante', {}).get('@Total')).split('.')
        qr_value = 'https://verificacfdi.facturaelectronica.sat.gob.mx/default.aspx?&id=%s&re=%s&rr=%s&tt=%s.%s&fe=%s' % (timbrado_data.get('@UUID'),
                                                 data.get('Comprobante', {}).get('Emisor', {}).get('@Rfc'), 
                                                 data.get('Comprobante', {}).get('Receptor', {}).get('@Rfc'),
                                                 amount_str[0].zfill(10),
                                                 len(amount_str) == 2 and amount_str[1].ljust(6, '0') or '000000',
                                                 str(timbrado_data.get('@SelloCFD'))[-8:],
                                                 )
        options = {'width': 275 * mm, 'height': 275 * mm}
        ret_val = createBarcodeDrawing('QR', value=qr_value, **options)
        qrcode_image = base64.encodebytes(ret_val.asString('jpg'))

        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': partner.id,
            'ref': customer_reference,
            'folio_fiscal': timbrado_data.get('@UUID'),
            'forma_pago_id': self.env['catalogo.forma.pago'].sudo().search([('code','=',data.get('Comprobante', {}).get('@FormaPago', {}))]),
            'methodo_pago': data.get('Comprobante', {}).get('@MetodoPago', {}),
            'uso_cfdi_id': self.env['catalogo.uso.cfdi'].sudo().search([('code','=',receptor_data.get('@UsoCFDI'))]),
            'factura_cfdi': True,
            'number_folio': data.get('Comprobante', {}).get('@Folio'),
            'tipo_comprobante': data.get('Comprobante', {}).get('@TipoDeComprobante'),
            'estado_factura': 'factura_correcta',
            'tipocambio': data.get('Comprobante', {}).get('@TipoCambio', '1'),
            # 'currency_id.name': data.get('Comprobante',{}).get('@Moneda'),
            'moneda': data.get('Comprobante', {}).get('@Moneda'),
            'numero_cetificado': timbrado_data.get('@NoCertificadoSAT'),
            'fecha_certificacion': timbrado_data.get('@FechaTimbrado') and parse(
                timbrado_data.get('@FechaTimbrado')).strftime(DEFAULT_SERVER_DATETIME_FORMAT) or False,
            'fecha_factura': timbrado_data.get('@FechaTimbrado') and parse(
                timbrado_data.get('@FechaTimbrado')).strftime(DEFAULT_SERVER_DATETIME_FORMAT) or False,
            'selo_digital_cdfi': timbrado_data.get('@SelloCFD'),
            'selo_sat': timbrado_data.get('@SelloSAT'),
            'currency_id': journal.currency_id.id or journal.company_id.currency_id.id or self.env.company.currency_id.id,
            'company_id': self.env.company.id,
            'journal_id': journal.id,
            'total_factura': data.get('Comprobante', {}).get('@Total'),
            'cetificaso_sat' : timbrado_data.get('@NoCertificadoSAT'),
            'cadena_origenal' : '||%s|%s|%s|%s|%s||' % (timbrado_data.get('@Version'), timbrado_data.get('@UUID'), timbrado_data.get('@FechaTimbrado'),
                                                         timbrado_data.get('@SelloCFD'), timbrado_data.get('@NoCertificadoSAT')),
            #'qrcode_image': qrcode_image,
        }

        if relacionado_data:
           invoice_vals.update({})
           if type(relacionado_data) != list:
                relacionado_data = [relacionado_data]
           uuids_relacionados = ''
           tipo_relacion = ''
           for cfdirelacionado in relacionado_data:
               uuids_list = cfdirelacionado.get('CfdiRelacionado', {})
               tipo_relacion = cfdirelacionado.get('@TipoRelacion')
               if type(uuids_list) != list:
                   uuids_list = [uuids_list]
               for relacionado in uuids_list:
                   uuids_relacionados += relacionado.get('@UUID') + ', '
           invoice_vals.update({'tipo_relacion': tipo_relacion, 'uuid_relacionado': uuids_relacionados})

        currency_code = data.get('Comprobante', {}).get('@Moneda', 'MXN')
        currency = self.env['res.currency'].search([('name', '=', currency_code)], limit=1)
        if not currency:
            currency = self.env['res.currency'].with_context(active_test=False).search([('name', '=', currency_code)],
                                                                                       limit=1)
            if currency:
                currency.write({'active': True})
        if currency:
            invoice_vals.update({'currency_id': currency.id})

        customer_invoice = invoice_obj.with_context(ctx).new(invoice_vals)
        customer_invoice._onchange_partner_id()
        invoice_vals = customer_invoice._convert_to_write(
            {name: customer_invoice[name] for name in customer_invoice._cache})
        invoice_vals.update({'invoice_date': parse(invoice_date).strftime(DEFAULT_SERVER_DATE_FORMAT), 'journal_id': journal.id, })

        fields = invoice_line_obj._fields.keys()
        ctx.update({'journal': journal.id})
        move_lines = []
        for line in invoice_line_data:
            product_name = line.get('@Descripcion')
            discount_amount = safe_eval(line.get('@Descuento', '0.0'))
            unit_price = safe_eval(line.get('@ValorUnitario', '0.0'))
            default_code = line.get('@NoIdentificacion')
            qty = safe_eval(line.get('@Cantidad', '1.0'))
            clave_unidad = line.get('@ClaveUnidad')
            clave_producto = line.get('@ClaveProdServ')
            taxes = line.get('Impuestos', {}).get('Traslados', {}).get('Traslado')
            if taxes:
                if type(taxes) != list:
                    taxes = [taxes]
            else:
                taxes = []
            no_imp_tras = len(taxes)
            if line.get('Impuestos', {}).get('Retenciones', {}):
                other_taxes = line.get('Impuestos', {}).get('Retenciones', {}).get('Retencion')
                if type(other_taxes) != list:
                    other_taxes = [other_taxes]
                taxes.extend(other_taxes)
            if taxes:
                if type(taxes) != list:
                    taxes = [taxes]
                tax_ids = []
                if taxes:
                    k = 0
                    for tax in taxes:
                        if tax.get('@TasaOCuota'):
                            if k < no_imp_tras:
                                if tax.get('@TipoFactor') != 'Cuota':
                                   amount_tasa = float(tax.get('@TasaOCuota')) * 100
                                else:
                                   amount_tasa = float(tax.get('@TasaOCuota'))
                            else:
                                if tax.get('@TipoFactor') != 'Cuota':
                                   amount_tasa = float(tax.get('@TasaOCuota')) * -100
                                else:
                                   amount_tasa = float(tax.get('@TasaOCuota')) * -1
                            tasa = str(amount_tasa)
                        else:
                            tasa = str(0)
                        tax_exist = tax_obj.search(
                            [('impuesto', '=', tax.get('@Impuesto')), ('type_tax_use', '=', 'sale'),
                             ('tipo_factor', '=', tax.get('@TipoFactor')), ('amount', '=', tasa),
                             ('company_id', '=', self.env.company.id)], limit=1)
                        if not tax_exist:
                            raise UserError(
                                "La factura contiene impuestos que no han sido configurados. Por favor configure los impuestos primero")
                        tax_ids.append(tax_exist.id)
                        k = k + 1
            product_exist = self.get_or_create_product(default_code, product_name, clave_unidad, unit_price,
                                                       clave_producto, sale_ok=True, purchase_ok=False)

            if discount_amount:
                discount_percent = discount_amount * 100.0 / (unit_price * qty)
            else:
                discount_percent = 0.0

            line_data = invoice_line_obj.default_get(fields)
            line_data.update({
                # 'move_id': invoice_exist.id,
                'product_id': product_exist.id,
                'name': product_name,
                'product_uom_id': product_exist.uom_po_id.id,
                'price_unit': unit_price,
                'discount': discount_percent,
            })

            # invoice_line = invoice_line_obj.with_context(ctx).new(line_data)
            # invoice_line.with_context(ctx)._onchange_product_id()
            # line_data = invoice_line._convert_to_write({name: invoice_line[name] for name in invoice_line._cache})
            if taxes:
                line_data.update({
                    'tax_ids': [(6, 0, tax_ids)],
                    'quantity': qty or 1,
                    'price_unit': unit_price,
                })
            else:
                line_data.update({
                    'tax_ids': [],
                    'quantity': qty or 1,
                    'price_unit': unit_price,
                })
            move_lines.append((0, 0, line_data))
            # invoice_line_obj.create(line_data)

        if move_lines:
            invoice_vals.update({'invoice_line_ids': move_lines})
            if 'line_ids' in invoice_vals:
                invoice_vals.pop('line_ids')
        invoice_exist = invoice_obj.with_context(ctx).create(invoice_vals)


##################################################################################
        file_new = base64.b64decode(file_content)
        xml_data = etree.fromstring(file_new)
        if b'Version=\"4.0\"' in file_new:
           NSMAP = {
                 'xsi':'http://www.w3.org/2001/XMLSchema-instance',
                 'cfdi':'http://www.sat.gob.mx/cfd/4', 
                 'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital',
                 }
        else:
           NSMAP = {
                 'xsi':'http://www.w3.org/2001/XMLSchema-instance',
                 'cfdi':'http://www.sat.gob.mx/cfd/3', 
                 'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital',
                 }
        tax_grouped_tras = {}
        tax_grouped_ret = {}
        Conceptos = xml_data.find('cfdi:Conceptos', NSMAP)
        for concepto in Conceptos:
              imp_prod = concepto.find('cfdi:Impuestos', NSMAP)
              if imp_prod:
                 traslados = imp_prod.find('cfdi:Traslados', NSMAP)
                 if traslados:
                    for traslado in traslados:
                       if 'TasaOCuota' in traslado.attrib:
                          if traslado.attrib['TipoFactor'] == 'Cuota':
                             tasa = str(float(traslado.attrib['TasaOCuota']))
                          else:
                             tasa = str(float(traslado.attrib['TasaOCuota'])*100)
                       else:
                          tasa = str(0)
                       tax_exist = self.env['account.tax'].search([('impuesto','=',traslado.attrib['Impuesto']), ('type_tax_use','=','sale'), 
                                                   ('tipo_factor','=',traslado.attrib['TipoFactor']), ('amount', '=', tasa), 
                                                   ('company_id','=',self.env.company.id)],limit=1)
                       if not tax_exist:
                          raise UserError(_("Un impuesto en el XML no está configurado en el sistema"))

                       if 'Importe' in traslado.attrib:
                          importe = traslado.attrib['Importe']
                       else:
                          importe = 0
                       key = tax_exist.id
                       val = {'tax_id': tax_exist.id,
                              'base': float(traslado.attrib['Base']),
                              'amount': float(importe),}
                       if key not in tax_grouped_tras:
                           tax_grouped_tras[key] = val
                       else:
                           tax_grouped_tras[key]['base'] += float(traslado.attrib['Base'])
                           tax_grouped_tras[key]['amount'] += float(importe)

                 retenciones = imp_prod.find('cfdi:Retenciones', NSMAP)
                 if retenciones:
                    for retencion in retenciones:
                       if 'TasaOCuota' in retencion.attrib:
                          tasa = str(float(retencion.attrib['TasaOCuota'])*-100)
                       else:
                          tasa = str(0)
                       tax_exist = self.env['account.tax'].search([('impuesto','=',retencion.attrib['Impuesto']), ('type_tax_use','=','sale'), 
                                                   ('tipo_factor','=',retencion.attrib['TipoFactor']), ('amount', '=', tasa), 
                                                   ('company_id','=',self.env.company.id)],limit=1)
                       if not tax_exist:
                          raise UserError(_("Un impuesto en el XML no está configurado en el sistema"))

                       if 'Importe' in retencion.attrib:
                          importe = retencion.attrib['Importe']
                       else:
                          importe = 0
                       key = tax_exist.id
                       val = {'tax_id': tax_exist.id,
                              'base': float(retencion.attrib['Base']),
                              'amount': float(importe),}
                       if key not in tax_grouped_ret:
                           tax_grouped_ret[key] = val
                       else:
                           tax_grouped_ret[key]['base'] += float(retencion.attrib['Base'])
                           tax_grouped_ret[key]['amount'] += float(importe)

        impuestos = {}
        if tax_grouped_tras or tax_grouped_ret:
                retenciones = []
                traslados = []
                if tax_grouped_tras:
                   for line in tax_grouped_tras.values():
                       tax = self.env['account.tax'].browse(line['tax_id'])
                       if tax.tipo_factor == 'Exento':
                          tasa_tr = ''
                       elif tax.tipo_factor == 'Cuota':
                          tasa_tr = invoice_exist.set_decimals(tax.amount, 6)
                       else:
                          tasa_tr = invoice_exist.set_decimals(tax.amount / 100.0, 6)
                       traslados.append({'impuesto': tax.impuesto,
                                         'TipoFactor': tax.tipo_factor,
                                         'tasa': tasa_tr,
                                         'importe': invoice_exist.set_decimals(line['amount'], invoice_exist.currency_id.no_decimales) if tax.tipo_factor != 'Exento' else '',
                                         'base': invoice_exist.set_decimals(line['base'], invoice_exist.currency_id.no_decimales),
                                         'tax_id': line['tax_id'],
                                         })
                   impuestos.update({'translados': traslados,})
                if tax_grouped_ret:
                   for line in tax_grouped_ret.values():
                       tax = self.env['account.tax'].browse(line['tax_id'])
                       retenciones.append({'impuesto': tax.impuesto,
                                         'TipoFactor': tax.tipo_factor,
                                         'tasa': invoice_exist.set_decimals(float(tax.amount) / 100.0 * -1, 6),
                                         'importe': invoice_exist.set_decimals(line['amount'], invoice_exist.currency_id.no_decimales),
                                         'base': invoice_exist.set_decimals(line['base'], invoice_exist.currency_id.no_decimales),
                                         'tax_id': line['tax_id'],
                                         })
                   impuestos.update({'retenciones': retenciones,})
        invoice_exist.write({'tax_payment': json.dumps(impuestos)})
##################################################################################

        # invoice_exist.compute_taxes()
        action = self.env.ref('account.action_move_out_invoice_type')
        result = action.read()[0]
        res = self.env.ref('account.view_move_form', False)
        result['views'] = [(res and res.id or False, 'form')]
        result['res_id'] = invoice_exist.id
        return result

    def import_supplier_invoice(self, file_content, journal=False):
        file_content = base64.b64decode(file_content)
        file_content = file_content.replace(b'cfdi:', b'')
        file_content = file_content.replace(b'tfd:', b'')
        try:
            data = json.dumps(xmltodict.parse(file_content))  # ,force_list=('Concepto','Traslado',)
            data = json.loads(data)
        except Exception as e:
            data = {}
            raise UserError(str(e))

        data = CaselessDictionary(data)
        data = convert_to_special_dict(data)

        invoice_obj = self.env['account.move']
        invoice_line_obj = self.env['account.move.line']
        # product_obj = self.env['product.product']

        # buscar_producto_por_clave_sat = self.env['ir.config_parameter'].sudo().get_param('l10n_mx_sat_sync_itadmin.buscar_producto_por_clave_sat')

        # product_types = dict(product_obj._fields.get('type')._description_selection(product_obj.env))
        # product_type_default = self.env['ir.config_parameter'].sudo().get_param('l10n_mx_sat_sync_itadmin.product_type_default')

        tax_obj = self.env['account.tax']
        vendor_data = data.get('Comprobante', {}).get('Emisor', {})
        invoice_line_data = data.get('Comprobante', {}).get('Conceptos', {}).get('Concepto', [])
        if type(invoice_line_data) != list:
            invoice_line_data = [invoice_line_data]

        invoice_date = data.get('Comprobante', {}).get('@Fecha')
        vendor_reference = data.get('Comprobante', {}).get('@Serie', '') + data.get('Comprobante', {}).get('@Folio', '')
        receptor_data = data.get('Comprobante', {}).get('Receptor', {})
        timbrado_data = data.get('Comprobante', {}).get('Complemento', {}).get('TimbreFiscalDigital', {})
        relacionado_data = data.get('Comprobante', {}).get('CfdiRelacionados', {})
        local_taxes = data.get('Comprobante', {}).get('Complemento', {}).get('implocal:impuestoslocales', {})

        try:
           vendor_uuid = timbrado_data.get('@UUID')
        except Exception as e:
           vendor_uuid = timbrado_data[0].get('@UUID')

        if vendor_uuid != '':
            vendor_order_exist = invoice_obj.search([('folio_fiscal', '=', vendor_uuid.lower())], limit=1)
            if not vendor_order_exist:
                vendor_order_exist = invoice_obj.search([('folio_fiscal', '=', vendor_uuid.upper())], limit=1)
            if vendor_order_exist:
                raise UserError("Factura ya existente con ese UUID %s" % (vendor_uuid))

        if vendor_reference != '':
            invoice_exist = invoice_obj.search([('ref', '=', vendor_reference), ('move_type', '=', 'in_invoice')],
                                               limit=1)
            if invoice_exist:
                vendor_reference = ''
                # raise UserError("Factura ya existente con la referencia del vendedor %s"%(vendor_reference))

        vendor = self.create_update_partner(vendor_data, is_customer=False, is_supplier=True)

        ctx = self._context.copy()
        ctx.update({'default_type': 'in_invoice', 'move_type': 'in_invoice'})
        if not journal:
            journal = invoice_obj.with_context(ctx)._default_journal()

        invoice_vals = {
            'move_type': 'in_invoice',
            'partner_id': vendor.id,
            'ref': vendor_reference,
            'folio_fiscal': timbrado_data.get('@UUID'),
            'forma_pago_id': self.env['catalogo.forma.pago'].sudo().search([('code','=',data.get('Comprobante', {}).get('@FormaPago', {}))]),
            'methodo_pago': data.get('Comprobante', {}).get('@MetodoPago', {}),
            'uso_cfdi_id': self.env['catalogo.uso.cfdi'].sudo().search([('code','=',receptor_data.get('@UsoCFDI'))]),
            # 'factura_cfdi': True,
            'number_folio': data.get('Comprobante', {}).get('@Folio'),
            'tipo_comprobante': data.get('Comprobante', {}).get('@TipoDeComprobante'),
            'estado_factura': 'factura_correcta',
            'tipocambio': data.get('Comprobante', {}).get('@TipoCambio', '1'),
            # 'currency_id.name': data.get('Comprobante',{}).get('@Moneda'),
            'moneda': data.get('Comprobante', {}).get('@Moneda'),
            'numero_cetificado': timbrado_data.get('@NoCertificadoSAT'),
            'fecha_certificacion': timbrado_data.get('@FechaTimbrado') and parse(
                timbrado_data.get('@FechaTimbrado')).strftime(DEFAULT_SERVER_DATETIME_FORMAT) or False,
            'fecha_factura': timbrado_data.get('@FechaTimbrado') and parse(
                timbrado_data.get('@FechaTimbrado')).strftime(DEFAULT_SERVER_DATETIME_FORMAT) or False,
            'selo_digital_cdfi': timbrado_data.get('@SelloCFD'),
            'selo_sat': timbrado_data.get('@SelloSAT'),
            'currency_id': journal.currency_id.id or journal.company_id.currency_id.id or self.env.company.currency_id.id,
            'company_id': self.env.company.id,
            'journal_id': journal.id,
            'total_factura': data.get('Comprobante', {}).get('@Total'),
        }

        if relacionado_data:
           invoice_vals.update({})
           if type(relacionado_data) != list:
                relacionado_data = [relacionado_data]
           uuids_relacionados = ''
           tipo_relacion = ''
           for cfdirelacionado in relacionado_data:
               uuids_list = cfdirelacionado.get('CfdiRelacionado', {})
               tipo_relacion = cfdirelacionado.get('@TipoRelacion')
               if type(uuids_list) != list:
                   uuids_list = [uuids_list]
               for relacionado in uuids_list:
                   uuids_relacionados += relacionado.get('@UUID') + ', '
           invoice_vals.update({'tipo_relacion': tipo_relacion, 'uuid_relacionado': uuids_relacionados})

        currency_code = data.get('Comprobante', {}).get('@Moneda', 'MXN')
        currency = self.env['res.currency'].search([('name', '=', currency_code)], limit=1)
        if not currency:
            currency = self.env['res.currency'].with_context(active_test=False).search([('name', '=', currency_code)],
                                                                                       limit=1)
            if currency:
                currency.write({'active': True})
        if currency:
            invoice_vals.update({'currency_id': currency.id})

        vendor_invoice = invoice_obj.with_context(ctx).new(invoice_vals)
        vendor_invoice._onchange_partner_id()
        invoice_vals = vendor_invoice._convert_to_write({name: vendor_invoice[name] for name in vendor_invoice._cache})
        invoice_vals.update(
            {'invoice_date': parse(invoice_date).strftime(DEFAULT_SERVER_DATE_FORMAT), 
             'date': parse(invoice_date).strftime(DEFAULT_SERVER_DATE_FORMAT),
             'journal_id': journal.id, })

        fields = invoice_line_obj._fields.keys()
        ctx.update({'journal': journal.id})

        move_lines = []

        for line in invoice_line_data:
            product_name = line.get('@Descripcion')
            discount_amount = safe_eval(line.get('@Descuento', '0.0'))
            unit_price = safe_eval(line.get('@ValorUnitario', '0.0'))
            default_code = line.get('@NoIdentificacion')
            qty = safe_eval(line.get('@Cantidad', '1.0'))
            clave_unidad = line.get('@ClaveUnidad')
            clave_producto = line.get('@ClaveProdServ')
            taxes = line.get('Impuestos', {}).get('Traslados', {}).get('Traslado')
            if taxes:
                if type(taxes) != list:
                    taxes = [taxes]
            else:
                taxes = []
            no_imp_tras = len(taxes)
            if line.get('Impuestos', {}).get('Retenciones', {}):
                other_taxes = line.get('Impuestos', {}).get('Retenciones', {}).get('Retencion')
                if type(other_taxes) != list:
                    other_taxes = [other_taxes]

                taxes.extend(other_taxes)
            if taxes:
                if type(taxes) != list:
                    taxes = [taxes]
                tax_ids = []
                if taxes:
                    k = 0
                    for tax in taxes:
                        if tax.get('@TasaOCuota'):
                            if k < no_imp_tras:
                                if tax.get('@TipoFactor') != 'Cuota':
                                   amount_tasa = float(tax.get('@TasaOCuota')) * 100
                                else:
                                   amount_tasa = float(tax.get('@TasaOCuota'))
                            else:
                                if tax.get('@TipoFactor') != 'Cuota':
                                   amount_tasa = float(tax.get('@TasaOCuota')) * -100
                                else:
                                   amount_tasa = float(tax.get('@TasaOCuota')) * -1
                            tasa = str(amount_tasa)
                        else:
                            tasa = str(0)
                        tax_exist = tax_obj.search(
                            [('impuesto', '=', tax.get('@Impuesto')), ('type_tax_use', '=', 'purchase'),
                             ('tipo_factor', '=', tax.get('@TipoFactor')), ('amount', '=', tasa),
                             ('company_id', '=', self.env.company.id)], limit=1)
                        if not tax_exist:
                            raise UserError(
                                "La factura contiene impuestos que no han sido configurados. Por favor configure los impuestos primero")
                        tax_ids.append(tax_exist.id)
                        k = k + 1

            ## Impuestos locales
            if local_taxes:
                try:
                   found_taxes = local_taxes.get('implocal:TrasladosLocales')
                   if type(found_taxes) != list and found_taxes != None:
                       found_taxes = [found_taxes]
                except Exception as e:
                   found_taxes = []
            else:
                found_taxes = []
            if found_taxes:
                importe = float(line.get('@Importe'))
                for local_tax in found_taxes:
                    tasa = float(local_tax.get('@TasadeTraslado')) / 100
                    amount_tax = float(local_tax.get('@Importe'))
                    if round(importe * tasa,2) == round(amount_tax,2):
                        tax_exist = tax_obj.search(
                            [('impuesto', '=', '004'), ('type_tax_use', '=', 'purchase'),
                             ('amount', '=', local_tax.get('@TasadeTraslado')), ('company_id', '=', self.env.company.id)], limit=1)
                        if not tax_exist:
                            raise UserError(
                                "La factura contiene impuestos locales que no han sido configurados. Por favor configure los impuestos primero")
                        tax_ids.append(tax_exist.id)

            product_exist = self.get_or_create_product(default_code, product_name, clave_unidad, unit_price,
                                                       clave_producto, sale_ok=False, purchase_ok=True)

            if discount_amount:
                discount_percent = discount_amount * 100.0 / (unit_price * qty)
            else:
                discount_percent = 0.0

            line_data = invoice_line_obj.default_get(fields)
            line_data.update({
                # 'move_id': invoice_exist.id,
                'product_id': product_exist.id,
                'name': product_name,
                'product_uom_id': product_exist.uom_po_id.id,
                'price_unit': unit_price,
                'discount': discount_percent,
            })

            # invoice_line = invoice_line_obj.with_context(ctx).new(line_data)
            # invoice_line.with_context(ctx)._onchange_product_id()
            # line_data = invoice_line._convert_to_write({name: invoice_line[name] for name in invoice_line._cache})
            if taxes:
                line_data.update({
                    'tax_ids': [(6, 0, tax_ids)],
                    'quantity': qty or 1,
                    'price_unit': unit_price,
                })
            else:
                line_data.update({
                    'tax_ids': [],
                    'quantity': qty or 1,
                    'price_unit': unit_price,
                })
            move_lines.append((0, 0, line_data))
            # invoice_line_obj.create(line_data)

        if move_lines:
            invoice_vals.update({'invoice_line_ids': move_lines})
            if 'line_ids' in invoice_vals:
                invoice_vals.pop('line_ids')

        invoice_exist = invoice_obj.with_context(ctx).create(invoice_vals)
        # invoice_exist.compute_taxes()
        action = self.env.ref('account.action_move_in_invoice_type').sudo()
        result = action.read()[0]
        res = self.env.ref('account.view_move_form', False)
        result['views'] = [(res and res.id or False, 'form')]
        result['res_id'] = invoice_exist.id
        return result

    @api.model
    def import_credit_note(self, file_content, journal=False):
        file_content = base64.b64decode(file_content)
        file_content = file_content.replace(b'cfdi:', b'')
        file_content = file_content.replace(b'tfd:', b'')
        try:
            data = json.dumps(xmltodict.parse(file_content))  # ,force_list=('Concepto','Traslado',)
            data = json.loads(data)
        except Exception as e:
            data = {}
            raise UserError(str(e))

        data = CaselessDictionary(data)
        data = convert_to_special_dict(data)

        invoice_obj = self.env['account.move']
        invoice_line_obj = self.env['account.move.line']
        # product_obj = self.env['product.product']

        # buscar_producto_por_clave_sat = self.env['ir.config_parameter'].sudo().get_param('l10n_mx_sat_sync_itadmin.buscar_producto_por_clave_sat')
        # product_types = dict(product_obj._fields.get('type')._description_selection(product_obj.env))
        # product_type_default = self.env['ir.config_parameter'].sudo().get_param('l10n_mx_sat_sync_itadmin.product_type_default')

        tax_obj = self.env['account.tax']
        partner_data = data.get('Comprobante', {}).get('Receptor', {})
        invoice_line_data = data.get('Comprobante', {}).get('Conceptos', {}).get('Concepto', [])
        if type(invoice_line_data) != list:
            invoice_line_data = [invoice_line_data]

        invoice_date = data.get('Comprobante', {}).get('@Fecha')
        customer_reference = data.get('Comprobante', {}).get('@Serie', '') + data.get('Comprobante', {}).get('@Folio','')
        receptor_data = data.get('Comprobante', {}).get('Receptor', {})
        timbrado_data = data.get('Comprobante', {}).get('Complemento', {}).get('TimbreFiscalDigital', {})
        relacionado_data = data.get('Comprobante', {}).get('CfdiRelacionados', {})
        vendor_uuid = timbrado_data.get('@UUID')

        if vendor_uuid != '':
            vendor_order_exist = invoice_obj.search([('folio_fiscal', '=', vendor_uuid.lower())], limit=1)
            if not vendor_order_exist:
                vendor_order_exist = invoice_obj.search([('folio_fiscal', '=', vendor_uuid.upper())], limit=1)
            if vendor_order_exist:
                raise UserError("Factura ya existente con ese UUID %s" % (vendor_uuid))

        if customer_reference != '':
            invoice_exist = invoice_obj.search([('ref', '=', customer_reference), ('move_type', '=', 'out_refund')], limit=1)
            if invoice_exist:
                customer_reference = ''
        #                raise UserError("Factura ya existente con la referencia del vendedor %s"%(customer_reference))

        ctx = self._context.copy()
        ctx.update({'default_type': 'out_refund', 'move_type': 'out_refund'})

        partner = self.create_update_partner(partner_data)
        if not journal:
            journal = invoice_obj.with_context(ctx)._default_journal()
        # journal = invoice_obj.with_context(ctx)._default_journal()

        invoice_vals = {
            'move_type': 'out_refund',
            'partner_id': partner.id,
            'ref': customer_reference,
            'folio_fiscal': timbrado_data.get('@UUID'),
            'forma_pago_id': self.env['catalogo.forma.pago'].sudo().search([('code','=',data.get('Comprobante', {}).get('@FormaPago', {}))]),
            'methodo_pago': data.get('Comprobante', {}).get('@MetodoPago', {}),
            'uso_cfdi_id': self.env['catalogo.uso.cfdi'].sudo().search([('code','=',receptor_data.get('@UsoCFDI'))]),
            'factura_cfdi': True,
            'number_folio': data.get('Comprobante', {}).get('@Folio'),
            'tipo_comprobante': data.get('Comprobante', {}).get('@TipoDeComprobante'),
            'estado_factura': 'factura_correcta',
            'tipocambio': data.get('Comprobante', {}).get('@TipoCambio', '1'),
            'moneda': data.get('Comprobante', {}).get('@Moneda'),
            'numero_cetificado': timbrado_data.get('@NoCertificadoSAT'),
            'fecha_certificacion': timbrado_data.get('@FechaTimbrado') and parse(
                timbrado_data.get('@FechaTimbrado')).strftime(DEFAULT_SERVER_DATETIME_FORMAT) or False,
            'selo_digital_cdfi': timbrado_data.get('@SelloCFD'),
            'selo_sat': timbrado_data.get('@SelloSAT'),
            'currency_id': journal.currency_id.id or journal.company_id.currency_id.id or self.env.company.currency_id.id,
            'company_id': self.env.company.id,
            'journal_id': journal.id,
            'total_factura': data.get('Comprobante', {}).get('@Total'),
        }

        if relacionado_data:
           invoice_vals.update({})
           if type(relacionado_data) != list:
                relacionado_data = [relacionado_data]
           uuids_relacionados = ''
           tipo_relacion = ''
           for cfdirelacionado in relacionado_data:
               uuids_list = cfdirelacionado.get('CfdiRelacionado', {})
               tipo_relacion = cfdirelacionado.get('@TipoRelacion')
               if type(uuids_list) != list:
                   uuids_list = [uuids_list]
               for relacionado in uuids_list:
                   uuids_relacionados += relacionado.get('@UUID') + ', '
           invoice_vals.update({'tipo_relacion': tipo_relacion, 'uuid_relacionado': uuids_relacionados})

        currency_code = data.get('Comprobante', {}).get('@Moneda', 'MXN')
        currency = self.env['res.currency'].search([('name', '=', currency_code)], limit=1)
        if not currency:
            currency = self.env['res.currency'].with_context(active_test=False).search([('name', '=', currency_code)], limit=1)
            if currency:
                currency.write({'active': True})
        if currency:
            invoice_vals.update({'currency_id': currency.id})

        customer_invoice = invoice_obj.with_context(ctx).new(invoice_vals)
        customer_invoice._onchange_partner_id()
        invoice_vals = customer_invoice._convert_to_write(
            {name: customer_invoice[name] for name in customer_invoice._cache})
        invoice_vals.update(
            {'invoice_date': parse(invoice_date).strftime(DEFAULT_SERVER_DATE_FORMAT), 'journal_id': journal.id, })

        fields = invoice_line_obj._fields.keys()
        ctx.update({'journal': journal.id})

        move_lines = []
        for line in invoice_line_data:
            product_name = line.get('@Descripcion')
            discount_amount = safe_eval(line.get('@Descuento', '0.0'))
            unit_price = safe_eval(line.get('@ValorUnitario', '0.0'))
            default_code = line.get('@NoIdentificacion')
            qty = safe_eval(line.get('@Cantidad', '1.0'))
            clave_unidad = line.get('@ClaveUnidad')
            clave_producto = line.get('@ClaveProdServ')
            taxes = line.get('Impuestos', {}).get('Traslados', {}).get('Traslado')
            if taxes:
                if type(taxes) != list:
                    taxes = [taxes]
            else:
                taxes = []
            no_imp_tras = len(taxes)
            if line.get('Impuestos', {}).get('Retenciones', {}):
                other_taxes = line.get('Impuestos', {}).get('Retenciones', {}).get('Retencion')
                if type(other_taxes) != list:
                    other_taxes = [other_taxes]
                taxes.extend(other_taxes)
            if taxes:
                if type(taxes) != list:
                    taxes = [taxes]
                tax_ids = []
                if taxes:
                    k = 0
                    for tax in taxes:
                        if tax.get('@TasaOCuota'):
                            if k < no_imp_tras:
                                if tax.get('@TipoFactor') != 'Cuota':
                                   amount_tasa = float(tax.get('@TasaOCuota')) * 100
                                else:
                                   amount_tasa = float(tax.get('@TasaOCuota'))
                            else:
                                if tax.get('@TipoFactor') != 'Cuota':
                                   amount_tasa = float(tax.get('@TasaOCuota')) * -100
                                else:
                                   amount_tasa = float(tax.get('@TasaOCuota')) * -1
                            tasa = str(amount_tasa)
                        else:
                            tasa = str(0)
                        tax_exist = tax_obj.search(
                            [('impuesto', '=', tax.get('@Impuesto')), ('type_tax_use', '=', 'sale'),
                             ('tipo_factor', '=', tax.get('@TipoFactor')), ('amount', '=', tasa),
                             ('company_id', '=', self.env.company.id)], limit=1)
                        if not tax_exist:
                            raise UserError(
                                "La factura contiene impuestos que no han sido configurados. Por favor configure los impuestos primero")
                        tax_ids.append(tax_exist.id)
                        k = k + 1

            product_exist = self.get_or_create_product(default_code, product_name, clave_unidad, unit_price,
                                                       clave_producto, sale_ok=True, purchase_ok=False)

            if discount_amount:
                discount_percent = discount_amount * 100.0 / (unit_price * qty)
            else:
                discount_percent = 0.0

            line_data = invoice_line_obj.default_get(fields)
            line_data.update({
                # 'move_id': invoice_exist.id,
                'product_id': product_exist.id,
                'name': product_name,
                'product_uom_id': product_exist.uom_po_id.id,
                'price_unit': unit_price,
                'discount': discount_percent,
            })

            # invoice_line = invoice_line_obj.with_context(ctx).new(line_data)
            # invoice_line.with_context(ctx)._onchange_product_id()
            # line_data = invoice_line._convert_to_write({name: invoice_line[name] for name in invoice_line._cache})
            if taxes:
                line_data.update({
                    'tax_ids': [(6, 0, tax_ids)],
                    'quantity': qty or 1,
                    'price_unit': unit_price,
                })
            else:
                line_data.update({
                    'tax_ids': [],
                    'quantity': qty or 1,
                    'price_unit': unit_price,
                })
            move_lines.append((0, 0, line_data))
            # invoice_line_obj.create(line_data)

        if move_lines:
            invoice_vals.update({'invoice_line_ids': move_lines})
            if 'line_ids' in invoice_vals:
                invoice_vals.pop('line_ids')
        invoice_exist = invoice_obj.with_context(ctx).create(invoice_vals)

        # invoice_exist.compute_taxes()
        action = self.env.ref('account.action_move_out_refund_type')
        result = action.read()[0]
        res = self.env.ref('account.view_move_form', False)
        result['views'] = [(res and res.id or False, 'form')]
        result['res_id'] = invoice_exist.id
        return result

    @api.model
    def import_supplier_credit_note(self, file_content, journal=False):
        file_content = base64.b64decode(file_content)
        file_content = file_content.replace(b'cfdi:', b'')
        file_content = file_content.replace(b'tfd:', b'')
        try:
            data = json.dumps(xmltodict.parse(file_content))
            data = json.loads(data)
        except Exception as e:
            data = {}
            raise UserError(str(e))

        data = CaselessDictionary(data)
        data = convert_to_special_dict(data)

        invoice_obj = self.env['account.move']
        invoice_line_obj = self.env['account.move.line']
        # product_obj = self.env['product.product']
        tax_obj = self.env['account.tax']

        # buscar_producto_por_clave_sat = self.env['ir.config_parameter'].sudo().get_param('l10n_mx_sat_sync_itadmin.buscar_producto_por_clave_sat')

        # product_types = dict(product_obj._fields.get('type')._description_selection(product_obj.env))
        # product_type_default = self.env['ir.config_parameter'].sudo().get_param('l10n_mx_sat_sync_itadmin.product_type_default')

        vendor_data = data.get('Comprobante', {}).get('Emisor', {})
        invoice_line_data = data.get('Comprobante', {}).get('Conceptos', {}).get('Concepto', [])
        if type(invoice_line_data) != list:
            invoice_line_data = [invoice_line_data]

        invoice_date = data.get('Comprobante', {}).get('@Fecha')
        vendor_reference = data.get('Comprobante', {}).get('@Serie', '') + data.get('Comprobante', {}).get('@Folio', '')
        receptor_data = data.get('Comprobante', {}).get('Receptor', {})
        timbrado_data = data.get('Comprobante', {}).get('Complemento', {}).get('TimbreFiscalDigital', {})
        relacionado_data = data.get('Comprobante', {}).get('CfdiRelacionados', {})
        purchase_uuid = timbrado_data.get('@UUID')

        if purchase_uuid != '':
            purchase_order_exist = invoice_obj.search([('folio_fiscal', '=', purchase_uuid.lower())], limit=1)
            if not purchase_order_exist:
                purchase_order_exist = invoice_obj.search([('folio_fiscal', '=', purchase_uuid.upper())], limit=1)
            if purchase_order_exist:
                raise UserError("Factura ya existente con ese UUID %s" % (purchase_uuid))

        if vendor_reference != '':
            invoice_exist = invoice_obj.search([('ref', '=', vendor_reference), ('move_type', '=', 'in_refund')], limit=1)
            if invoice_exist:
                vendor_reference = ''
                # raise UserError("Factura ya existente con la referencia del vendedor %s"%(vendor_reference))

        # vendor = self.env['import.purchase.order.from.xml'].create_update_vendor(vendor_data)
        vendor = self.create_update_partner(vendor_data, is_customer=False, is_supplier=True)

        ctx = self._context.copy()
        ctx.update({'default_type': 'in_refund', 'move_type': 'in_refund', })

        invoice_fields = invoice_obj._fields.keys()
        invoice_vals = invoice_obj.default_get(invoice_fields)
        if not journal:
            journal = invoice_obj.with_context(ctx)._default_journal()
        # journal = invoice_obj.with_context(ctx)._default_journal()

        invoice_vals.update({
            'move_type': 'in_refund',
            'partner_id': vendor.id,
            'ref': vendor_reference,
            'folio_fiscal': timbrado_data.get('@UUID'),
            'forma_pago_id': self.env['catalogo.forma.pago'].sudo().search([('code','=',data.get('Comprobante', {}).get('@FormaPago', {}))]),
            'methodo_pago': data.get('Comprobante', {}).get('@MetodoPago', {}),
            'uso_cfdi_id': self.env['catalogo.uso.cfdi'].sudo().search([('code','=',receptor_data.get('@UsoCFDI'))]),
            # 'factura_cfdi': True,
            'number_folio': data.get('Comprobante', {}).get('@Folio'),
            'tipo_comprobante': data.get('Comprobante', {}).get('@TipoDeComprobante'),
            'estado_factura': 'factura_correcta',
            'tipocambio': data.get('Comprobante', {}).get('@TipoCambio', '1'),
            # 'currency_id.name': data.get('Comprobante',{}).get('@Moneda'),
            'moneda': data.get('Comprobante', {}).get('@Moneda'),
            'numero_cetificado': timbrado_data.get('@NoCertificadoSAT'),
            'fecha_certificacion': timbrado_data.get('@FechaTimbrado') and parse(
                timbrado_data.get('@FechaTimbrado')).strftime(DEFAULT_SERVER_DATETIME_FORMAT) or False,
            'selo_digital_cdfi': timbrado_data.get('@SelloCFD'),
            'selo_sat': timbrado_data.get('@SelloSAT'),
            'currency_id': journal.currency_id.id or journal.company_id.currency_id.id or self.env.company.currency_id.id,
            'company_id': self.env.company.id,
            'journal_id': journal.id,
            'total_factura': data.get('Comprobante', {}).get('@Total'),
        })

        if relacionado_data:
           invoice_vals.update({})
           if type(relacionado_data) != list:
                relacionado_data = [relacionado_data]
           uuids_relacionados = ''
           tipo_relacion = ''
           for cfdirelacionado in relacionado_data:
               uuids_list = cfdirelacionado.get('CfdiRelacionado', {})
               tipo_relacion = cfdirelacionado.get('@TipoRelacion')
               if type(uuids_list) != list:
                   uuids_list = [uuids_list]
               for relacionado in uuids_list:
                   uuids_relacionados += relacionado.get('@UUID') + ', '
           invoice_vals.update({'tipo_relacion': tipo_relacion, 'uuid_relacionado': uuids_relacionados})

        currency_code = data.get('Comprobante', {}).get('@Moneda', 'MXN')
        currency = self.env['res.currency'].search([('name', '=', currency_code)], limit=1)
        if not currency:
            currency = self.env['res.currency'].with_context(active_test=False).search([('name', '=', currency_code)],
                                                                                       limit=1)
            if currency:
                currency.write({'active': True})
        if currency:
            invoice_vals.update({'currency_id': currency.id})

        vendor_invoice = invoice_obj.with_context(ctx).new(invoice_vals)
        vendor_invoice._onchange_partner_id()
        invoice_vals = vendor_invoice._convert_to_write({name: vendor_invoice[name] for name in vendor_invoice._cache})
        invoice_vals.update(
            {'invoice_date': parse(invoice_date).strftime(DEFAULT_SERVER_DATE_FORMAT),
             'date': parse(invoice_date).strftime(DEFAULT_SERVER_DATE_FORMAT),
             'journal_id': journal.id, })

        fields = invoice_line_obj._fields.keys()
        ctx.update({'journal': journal.id})

        move_lines = []

        for line in invoice_line_data:
            product_name = line.get('@Descripcion')
            discount_amount = safe_eval(line.get('@Descuento', '0.0'))
            unit_price = safe_eval(line.get('@ValorUnitario', '0.0'))
            default_code = line.get('@NoIdentificacion')
            qty = safe_eval(line.get('@Cantidad', '1.0'))
            clave_unidad = line.get('@ClaveUnidad')
            clave_producto = line.get('@ClaveProdServ')
            taxes = line.get('Impuestos', {}).get('Traslados', {}).get('Traslado')
            if taxes:
                if type(taxes) != list:
                    taxes = [taxes]
            else:
                taxes = []
            no_imp_tras = len(taxes)
            if line.get('Impuestos', {}).get('Retenciones', {}):
                other_taxes = line.get('Impuestos', {}).get('Retenciones', {}).get('Retencion')
                if type(other_taxes) != list:
                    other_taxes = [other_taxes]
                taxes.extend(other_taxes)
            if type(taxes) != list:
                taxes = [taxes]
            tax_ids = []
            if taxes:
                k = 0
                for tax in taxes:
                    if tax.get('@TasaOCuota'):
                        if k < no_imp_tras:
                           if tax.get('@TipoFactor') != 'Cuota':
                               amount_tasa = float(tax.get('@TasaOCuota')) * 100
                           else:
                               amount_tasa = float(tax.get('@TasaOCuota'))
                        else:
                           if tax.get('@TipoFactor') != 'Cuota':
                               amount_tasa = float(tax.get('@TasaOCuota')) * -100
                           else:
                               amount_tasa = float(tax.get('@TasaOCuota')) * -1
                        tasa = str(amount_tasa)
                    else:
                        tasa = str(0)
                    tax_exist = tax_obj.search(
                        [('impuesto', '=', tax.get('@Impuesto')), ('type_tax_use', '=', 'purchase'),
                         ('tipo_factor', '=', tax.get('@TipoFactor')), ('amount', '=', tasa),
                         ('company_id', '=', self.env.company.id)], limit=1)
                    if not tax_exist:
                        raise UserError(
                            "La factura contiene impuestos que no han sido configurados. Por favor configure los impuestos primero")
                    tax_ids.append(tax_exist.id)
                    k = k + 1

            product_exist = self.get_or_create_product(default_code, product_name, clave_unidad, unit_price,
                                                       clave_producto, sale_ok=False, purchase_ok=True)

            if discount_amount:
                discount_percent = discount_amount * 100.0 / (unit_price * qty)
            else:
                discount_percent = 0.0

            line_data = invoice_line_obj.default_get(fields)
            line_data.update({
                # 'move_id': invoice_exist.id,
                'product_id': product_exist.id,
                'name': product_name,
                'product_uom_id': product_exist.uom_po_id.id,
                'price_unit': unit_price,
                'discount': discount_percent,
            })

            # invoice_line = invoice_line_obj.with_context(ctx).new(line_data)
            # invoice_line.with_context(ctx)._onchange_product_id()
            # line_data = invoice_line._convert_to_write({name: invoice_line[name] for name in invoice_line._cache})
            line_data.update({
                'tax_ids': [(6, 0, tax_ids)],
                'quantity': qty or 1,
                'price_unit': unit_price,
            })
            move_lines.append((0, 0, line_data))
            # invoice_line_obj.create(line_data)

        if move_lines:
            invoice_vals.update({'invoice_line_ids': move_lines})
            if 'line_ids' in invoice_vals:
                invoice_vals.pop('line_ids')
        invoice_exist = invoice_obj.with_context(ctx).create(invoice_vals)
        # invoice_exist.compute_taxes()
        action = self.env.ref('account.action_move_in_refund_type')
        result = action.read()[0]
        res = self.env.ref('account.view_move_form', False)
        result['views'] = [(res and res.id or False, 'form')]
        result['res_id'] = invoice_exist.id
        return result

    @api.model
    def get_or_create_product(self, default_code, product_name, clave_unidad, unit_price, clave_producto, sale_ok=True, purchase_ok=False):
        product_exist = False
        product_obj = self.env['product.product']
        param_obj = self.env['ir.config_parameter'].sudo()
        buscar_producto_por_clave_sat = self.env['ir.config_parameter'].sudo().get_param('l10n_mx_sat_sync_itadmin.buscar_producto_por_clave_sat')
        product_types = dict(product_obj._fields.get('type')._description_selection(product_obj.env))
        product_type_default = self.env['ir.config_parameter'].sudo().get_param('l10n_mx_sat_sync_itadmin.product_type_default')
        p_supplierinfo = self.env['product.supplierinfo']

        if default_code:
            product_exist = product_obj.search([('default_code', '=', default_code)], limit=1)
            if not product_exist:
                supplierinfo_exist = p_supplierinfo.search([('product_code', '=', default_code)], limit=1)
                if supplierinfo_exist.product_tmpl_id:
                    product_exist = supplierinfo_exist.product_tmpl_id.product_variant_id
        if not product_exist:
            product_exist = product_obj.search([('name', '=', product_name)], limit=1)
        if buscar_producto_por_clave_sat and not product_exist:
            product_exist = product_obj.search([('clave_producto', '=', clave_producto)], limit=1)
        if not product_exist and self.si_producto_no_tiene_codigo == 'Buscar manual':
            product_exist = self.product_id
        if not product_exist:
            um_descripcion = self.env['catalogo.unidad.medida'].search([('clave', '=', clave_unidad)], limit=1)
            if not um_descripcion:
                raise UserError(
                    "No tiene configurada la unidad de medida %s. Por favor configure la unidad de medida primero"%(clave_unidad))
            product_vals = {'default_code': default_code, 'name': product_name, 'standard_price': unit_price,
                            'cat_unidad_medida': um_descripcion.id, 'clave_producto': clave_producto, }
            if product_type_default:
                product_vals.update({'type': product_type_default})
            elif 'product' in product_types:
                product_vals.update({'type': 'product'})
            product_vals.update({'sale_ok': sale_ok, 'purchase_ok': purchase_ok})
            product_exist = product_obj.create(product_vals)

        return product_exist

    def import_sale_order(self, file_content):
        file_content = base64.b64decode(file_content)
        file_content = file_content.replace(b'cfdi:', b'')
        file_content = file_content.replace(b'tfd:', b'')
        try:
            data = json.dumps(xmltodict.parse(file_content))
            data = json.loads(data)
        except Exception as e:
            data = {}
            raise UserError(str(e))

        data = CaselessDictionary(data)
        data = convert_to_special_dict(data)

        sale_obj = self.env['sale.order']
        sale_line_obj = self.env['sale.order.line']
        # product_obj = self.env['product.product']

        tax_obj = self.env['account.tax']
        # vendor_data = data.get('Comprobante',{}).get('Emisor',{})
        partner_data = data.get('Comprobante', {}).get('Receptor', {})
        order_line_data = data.get('Comprobante', {}).get('Conceptos', {}).get('Concepto', [])
        if type(order_line_data) != list:
            order_line_data = [order_line_data]
        date_order = data.get('Comprobante', {}).get('@Fecha')
        receptor_data = data.get('Comprobante', {}).get('Receptor', {})

        partner = self.create_update_partner(partner_data)
        order_vals = {
            'partner_id': partner.id,
            'forma_pago_id': self.env['catalogo.forma.pago'].sudo().search([('code','=',data.get('Comprobante', {}).get('@FormaPago', {}))]),
            'methodo_pago': data.get('Comprobante', {}).get('@MetodoPago', {}),
            'uso_cfdi_id': self.env['catalogo.uso.cfdi'].sudo().search([('code','=',receptor_data.get('@UsoCFDI'))]),
            'company_id': self.env.company.id,
        }
        sale_order = sale_obj.new(order_vals)
        #sale_order.onchange_partner_id()
        order_vals = sale_order._convert_to_write({name: sale_order[name] for name in sale_order._cache})
        order_vals.update({'date_order': parse(date_order).strftime(DEFAULT_SERVER_DATETIME_FORMAT), })

        currency_code = data.get('Comprobante', {}).get('@Moneda', 'MXN')
        currency = self.env['res.currency'].search([('name', '=', currency_code)], limit=1)
        if not currency:
            currency = self.env['res.currency'].with_context(active_test=False).search([('name', '=', currency_code)],limit=1)
            if currency:
                currency.write({'active': True})
        if currency:
            pricelist = self.env['product.pricelist'].search([('currency_id', '=', currency.id)], limit=1)
            if not pricelist:
                pricelist = self.env['product.pricelist'].create(
                    {'name': 'Public Pricelist : ' + currency.name, 'currency_id': currency.id})
            order_vals.update({'pricelist_id': pricelist.id})

        sale_order_exist = sale_obj.create(order_vals)

        for line in order_line_data:
            product_name = line.get('@Descripcion')
            discount_amount = safe_eval(line.get('@Descuento', '0.0'))
            unit_price = safe_eval(line.get('@ValorUnitario', '0.0'))
            default_code = line.get('@NoIdentificacion')
            qty = safe_eval(line.get('@Cantidad', '1.0'))
            clave_unidad = line.get('@ClaveUnidad')
            clave_producto = line.get('@ClaveProdServ')
            taxes = line.get('Impuestos', {}).get('Traslados', {}).get('Traslado')
            if taxes:
                if type(taxes) != list:
                    taxes = [taxes]
            else:
                taxes = []
            no_imp_tras = len(taxes)
            if line.get('Impuestos', {}).get('Retenciones', {}):
                other_taxes = line.get('Impuestos', {}).get('Retenciones', {}).get('Retencion')
                if type(other_taxes) != list:
                    other_taxes = [other_taxes]
                taxes.extend(other_taxes)
            if taxes:
                if type(taxes) != list:
                    taxes = [taxes]
                tax_ids = []
                if taxes:
                    k = 0
                    for tax in taxes:
                        if tax.get('@TasaOCuota'):
                           if k < no_imp_tras:
                              if tax.get('@TipoFactor') != 'Cuota':
                                  amount_tasa = float(tax.get('@TasaOCuota')) * 100
                              else:
                                  amount_tasa = float(tax.get('@TasaOCuota'))
                           else:
                              if tax.get('@TipoFactor') != 'Cuota':
                                  amount_tasa = float(tax.get('@TasaOCuota')) * -100
                              else:
                                  amount_tasa = float(tax.get('@TasaOCuota')) * -1
                           tasa = str(amount_tasa)
                        else:
                            tasa = str(0)
                        tax_exist = tax_obj.search(
                            [('impuesto', '=', tax.get('@Impuesto')), ('type_tax_use', '=', 'sale'),
                             ('tipo_factor', '=', tax.get('@TipoFactor')), ('amount', '=', tasa),
                             ('company_id', '=', self.env.company.id)], limit=1)
                        if not tax_exist:
                            raise UserError(
                                "La factura contiene impuestos que no han sido configurados. Por favor configure los impuestos primero")
                        tax_ids.append(tax_exist.id)
                        k = k + 1

            product_exist = self.get_or_create_product(default_code, product_name, clave_unidad, unit_price,
                                                       clave_producto, sale_ok=True, purchase_ok=False)

            if discount_amount:
                discount_percent = discount_amount * 100.0 / (unit_price * qty)
            else:
                discount_percent = 0.0

            line_data = {
                'order_id': sale_order_exist.id,
                'product_id': product_exist.id,
                'name': product_name,
                'product_uom': product_exist.uom_id.id,
                'price_unit': unit_price,
                'discount': discount_percent,
            }
            sale_line = sale_line_obj.new(line_data)
            #sale_line.product_id_change()
            line_data = sale_line._convert_to_write({name: sale_line[name] for name in sale_line._cache})
            if taxes:
                line_data.update({
                    'tax_id': [(6, 0, tax_ids)],
                    'product_uom_qty': qty or 1,
                    'price_unit': unit_price,
                })
            else:
                line_data.update({
                    'tax_id': [],
                    'product_uom_qty': qty or 1,
                    'price_unit': unit_price,
                })
            sale_line_obj.create(line_data)

        if sale_order_exist.state == 'draft':
            action = self.env.ref('sale.action_quotations')
        else:
            action = self.env.ref('sale.action_orders')
        result = action.read()[0]

        res = self.env.ref('sale.view_order_form', False)
        result['views'] = [(res and res.id or False, 'form')]
        result['res_id'] = sale_order_exist.id
        return result

    def import_purchase_order(self, file_content):
        file_content = base64.b64decode(file_content)
        file_content = file_content.replace(b'cfdi:', b'')
        file_content = file_content.replace(b'tfd:', b'')
        try:
            data = json.dumps(xmltodict.parse(file_content))  # ,force_list=('Concepto','Traslado',)
            data = json.loads(data)
        except Exception as e:
            data = {}
            raise UserError(str(e))

        data = CaselessDictionary(data)
        data = convert_to_special_dict(data)

        purchase_obj = self.env['purchase.order']
        purchase_line_obj = self.env['purchase.order.line']

        tax_obj = self.env['account.tax']
        vendor_data = data.get('Comprobante', {}).get('Emisor', {})
        order_line_data = data.get('Comprobante', {}).get('Conceptos', {}).get('Concepto', [])
        if type(order_line_data) != list:
            order_line_data = [order_line_data]
        date_order = data.get('Comprobante', {}).get('@Fecha')
        vendor_reference = data.get('Comprobante', {}).get('@Serie', '') + data.get('Comprobante', {}).get('@Folio', '')
        receptor_data = data.get('Comprobante', {}).get('Receptor', {})
        timbrado_data = data.get('Comprobante', {}).get('Complemento', {}).get('TimbreFiscalDigital', {})

        purchase_uuid = timbrado_data.get('@UUID')
        if purchase_uuid != '':
            purchase_order_exist = purchase_obj.search([('folio_fiscal', '=', purchase_uuid.lower())], limit=1)
            if not purchase_order_exist:
                purchase_order_exist = purchase_obj.search([('folio_fiscal', '=', purchase_uuid.upper())], limit=1)
            if purchase_order_exist:
                raise UserError("Factura ya existente con ese UUID %s" % (purchase_uuid))

        if vendor_reference != '':
            purchase_order_exist = purchase_obj.search([('partner_ref', '=', vendor_reference)], limit=1)
            if purchase_order_exist:
                vendor_reference = ''

        vendor = self.create_update_partner(vendor_data, is_customer=False, is_supplier=True)
        order_vals = {
            'partner_id': vendor.id,
            'partner_ref': vendor_reference,
            'folio_fiscal': timbrado_data.get('@UUID'),
            'forma_pago_id': self.env['catalogo.forma.pago'].sudo().search([('code','=',data.get('Comprobante', {}).get('@FormaPago', {}))]),
            'methodo_pago': data.get('Comprobante', {}).get('@MetodoPago', {}),
            'uso_cfdi_id': self.env['catalogo.uso.cfdi'].sudo().search([('code','=',receptor_data.get('@UsoCFDI'))]),
            'tipo_comprobante': data.get('Comprobante', {}).get('@TipoDeComprobante'),
            'estado_factura': 'factura_correcta',
            'tipocambio': data.get('Comprobante', {}).get('@TipoCambio', '1'),
            # 'currency_id.name': data.get('Comprobante',{}).get('@Moneda'),
            'moneda': data.get('Comprobante', {}).get('@Moneda'),
            'numero_cetificado': timbrado_data.get('@NoCertificadoSAT'),
            'fecha_certificacion': timbrado_data.get('@FechaTimbrado') and parse(
                timbrado_data.get('@FechaTimbrado')).strftime(DEFAULT_SERVER_DATETIME_FORMAT) or False,
            'selo_digital_cdfi': timbrado_data.get('@SelloCFD'),
            'selo_sat': timbrado_data.get('@SelloSAT'),
            'company_id': self.env.company.id,
        }
        purchase_order = purchase_obj.new(order_vals)
        #purchase_order.onchange_partner_id()
        order_vals = purchase_order._convert_to_write({name: purchase_order[name] for name in purchase_order._cache})
        order_vals.update({'date_order': parse(date_order).strftime(DEFAULT_SERVER_DATETIME_FORMAT), })
        currency_code = data.get('Comprobante', {}).get('@Moneda', 'MXN')
        currency = self.env['res.currency'].search([('name', '=', currency_code)], limit=1)
        if currency:
            order_vals.update({'currency_id': currency.id})
        purchase_order_exist = purchase_obj.create(order_vals)

        for line in order_line_data:
            product_name = line.get('@Descripcion')
            discount_amount = safe_eval(line.get('@Descuento', '0.0'))
            unit_price = safe_eval(line.get('@ValorUnitario', '0.0'))
            default_code = line.get('@NoIdentificacion')
            qty = safe_eval(line.get('@Cantidad', '1.0'))
            clave_unidad = line.get('@ClaveUnidad')
            clave_producto = line.get('@ClaveProdServ')
            taxes = line.get('Impuestos', {}).get('Traslados', {}).get('Traslado')
            if taxes:
                if type(taxes) != list:
                    taxes = [taxes]
            else:
                taxes = []
            no_imp_tras = len(taxes)
            if line.get('Impuestos', {}).get('Retenciones', {}):
                other_taxes = line.get('Impuestos', {}).get('Retenciones', {}).get('Retencion')
                if type(other_taxes) != list:
                    other_taxes = [other_taxes]

                taxes.extend(other_taxes)
            if taxes:
                if type(taxes) != list:
                    taxes = [taxes]
                tax_ids = []
                if taxes:
                    k = 0
                    for tax in taxes:
                        if tax.get('@TasaOCuota'):
                           if k < no_imp_tras:
                              if tax.get('@TipoFactor') != 'Cuota':
                                  amount_tasa = float(tax.get('@TasaOCuota')) * 100
                              else:
                                  amount_tasa = float(tax.get('@TasaOCuota'))
                           else:
                              if tax.get('@TipoFactor') != 'Cuota':
                                  amount_tasa = float(tax.get('@TasaOCuota')) * -100
                              else:
                                  amount_tasa = float(tax.get('@TasaOCuota')) * -1
                           tasa = str(amount_tasa)
                        else:
                            tasa = str(0)
                        tax_exist = tax_obj.search(
                            [('impuesto', '=', tax.get('@Impuesto')), ('type_tax_use', '=', 'purchase'),
                             ('tipo_factor', '=', tax.get('@TipoFactor')), ('amount', '=', tasa),
                             ('company_id', '=', self.env.company.id)], limit=1)
                        if not tax_exist:
                            raise UserError(
                                "La factura contiene impuestos que no han sido configurados. Por favor configure los impuestos primero")
                        tax_ids.append(tax_exist.id)
                        k = k + 1

            product_exist = self.get_or_create_product(default_code, product_name, clave_unidad, unit_price,
                                                       clave_producto, sale_ok=False, purchase_ok=True)

            if discount_amount:
                discount_percent = discount_amount * 100.0 / (unit_price * qty)
            else:
                discount_percent = 0.0

            line_data = {
                'order_id': purchase_order_exist.id,
                'product_id': product_exist.id,
                'name': product_name,
                'product_uom': product_exist.uom_po_id.id,
                'price_unit': unit_price,
                # 'discount':discount_percent,
            }
            purchase_line = purchase_line_obj.new(line_data)
            purchase_line.onchange_product_id()
            line_data = purchase_line._convert_to_write({name: purchase_line[name] for name in purchase_line._cache})
            if taxes:
                line_data.update({
                    'taxes_id': [(6, 0, tax_ids)],
                    'product_qty': qty or 1,
                    'price_unit': unit_price,
                })
            else:
                line_data.update({
                    'taxes_id': [],
                    'product_qty': qty or 1,
                    'price_unit': unit_price,
                })
            purchase_line_obj.create(line_data)

        if purchase_order_exist.state == 'draft':
            action = self.env.ref('purchase.purchase_rfq')
        else:
            action = self.env.ref('purchase.purchase_form_action')
        result = action.read()[0]

        res = self.env.ref('purchase.purchase_order_form', False)
        result['views'] = [(res and res.id or False, 'form')]
        result['res_id'] = purchase_order_exist.id
        return result

