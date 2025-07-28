# -*- coding: utf-8 -*-

import base64
import json
import requests
import datetime
from lxml import etree

from odoo import fields, models, api,_
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from reportlab.graphics.barcode import createBarcodeDrawing
from reportlab.lib.units import mm
from . import amount_to_text_es_MX
import pytz
from odoo import tools
import ast
import logging
_logger = logging.getLogger(__name__)

class CfdiRetencionLine(models.Model):
    _name = "cfdi.retencion.line"
    
    cfdi_retencion_id= fields.Many2one('cfdi.retencion',string="CFDI Retencion")
    impuesto = fields.Selection(
        selection=[('001', _('ISR')),
                   ('002', _('IVA')),
                   ('003', _('IEPS')),],
        string=_('Impuesto'), 
    )
    tipo_pago = fields.Selection(
        selection=[('01', _('Pago definitivo IVA')),
                   ('02', _('Pago definitivo IEPS')),
                   ('03', _('Pago definitivo ISR ')),
                   ('04', _('Pago provisional ISR ')),],
        string=_('Tipo de pago'), 
    )

    monto_base = fields.Float(string='Monto operacion', digits=dp.get_precision('Product Price'), required=True, default=1)
    monto_retenido = fields.Float(string='Monto retenido', digits=dp.get_precision('Product Price'), required=True, default=1)
    monto_exento = fields.Float(string='Monto exento', digits=dp.get_precision('Product Price'), required=True, default=1)
    monto_gravado = fields.Float(string='Monto gravado', digits=dp.get_precision('Product Price'), required=True, default=1)

class CfdiRetencion(models.Model):
    _name = "cfdi.retencion"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _rec_name = "number"

    factura_cfdi = fields.Boolean('Factura CFDI')
    number = fields.Char(string="Numero", store=True, readonly=True, copy=False,
                         default=lambda self: _('Factura borrador'))
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('valid', 'Validada'),
        ('cancel', 'Cancelada'),
    ], string='Status', index=True, readonly=True, default='draft', )

    partner_id = fields.Many2one('res.partner', string="Cliente", required=True, default=lambda self: self.env['res.company']._company_default_get('cfdi.retencion'))
    fecha_factura = fields.Datetime(string=_('Fecha Factura'))
    retencion = fields.Selection(
        selection=[('01', 'Servicios profesionales'), 
                   ('02', 'Regalías por derechos de autor'), 
                   ('03', 'Autotransporte terrestre de carga'),
                   ('04', 'Servicios prestados por comisionistas'), 
                   ('05', 'Arrendamiento'),
                   ('06', 'Enajenación de acciones'), 
                   ('07', 'Enajenación de bienes objeto de la LIEPS'), 
                   ('08', 'Enajenación de bienes inmuebles consignada en escritura pública'), 
                   ('09', 'Enajenación de otros bienes, no consignada en escritura pública.'), 
                   ('10', 'Adquisición de desperdicios industriales.'), 
                   ('11', 'Adquisición de bienes consignada en escritura pública.'), 
                   ('12', 'Adquisición de otros bienes, no consignada en escritura pública.'), 
                   ('13', 'Otros retiros de AFORE.'), 
                   ('14', 'Dividendos o utilidades distribuidas.'), 
                   ('15', 'Remanente distribuible.'), 
                   ('16', 'Intereses.'), 
                   ('17', 'Arrendamiento en fideicomiso.'), 
                   ('18', 'Pagos realizados a favor de residentes en el extranjero.'), 
                   ('19', 'Enajenación de acciones u operaciones en bolsa de valores.'), 
                   ('20', 'Obtención de premios.'), 
                   ('21', 'Fideicomisos que no realizan actividades empresariales.'), 
                   ('22', 'Planes personales de retiro.'),
                   ('23', 'Intereses reales deducibles por créditos hipotecarios.'), 
                   ('24', 'Intereses reales deducibles por créditos hipotecarios.'), 
                   ('25', 'Otro tipo de retenciones.'),
                   ('26', 'Servicios mediante Plataformas Tecnológicas '), 
                   ('27', 'Sector Financiero'),
                   ('28', 'Pagos y retenciones a Contribuyentes del RIF'),],
        string=_('Retención')
    )
    periodo_inicio = fields.Selection(
        selection=[('01', 'Enero'),
                   ('02', 'Febrero'),
                   ('03', 'Marzo'),
                   ('04', 'Abril'),
                   ('05', 'Mayo'),
                   ('06', 'Junio'),
                   ('07', 'Julio'),
                   ('08', 'Agosto'),
                   ('09', 'Septiembre'),
                   ('10', 'Octubre'),
                   ('11', 'Noviembre'),
                   ('12', 'Diciembre'), ],
        string=_('Mes inicio'),
    )
    periodo_final = fields.Selection(
        selection=[('01', 'Enero'),
                   ('02', 'Febrero'),
                   ('03', 'Marzo'),
                   ('04', 'Abril'),
                   ('05', 'Mayo'),
                   ('06', 'Junio'),
                   ('07', 'Julio'),
                   ('08', 'Agosto'),
                   ('09', 'Septiembre'),
                   ('10', 'Octubre'),
                   ('11', 'Noviembre'),
                   ('12', 'Diciembre'), ],
        string=_('Mes final'),
    )
    ejercicio = fields.Selection(
        selection=[('2022', '2022'),
                   ('2023', '2023'),
                   ('2024', '2024'),
                   ('2025', '2025'),
                   ('2026', '2026'), ],
        string=_('Ejercicio'),
    )

    complemento_a = fields.Boolean('Arrendamiento fideicomiso')
    complemento_b = fields.Boolean('Enajenación de acciones')
    complemento_c = fields.Boolean('Dividendos')
    complemento_d = fields.Boolean('Fideicomiso no empresarial')
    complemento_e = fields.Boolean('Intereses hipotecarios')
    complemento_f = fields.Boolean('Operaciones con derivados')
    complemento_g = fields.Boolean('Pagos a extanjeros')
    complemento_h = fields.Boolean('Planes de retiros')
    complemento_i = fields.Boolean('Premios')
    complemento_j = fields.Boolean('Sector financiero')

    estado_factura = fields.Selection(
        selection=[('factura_no_generada', 'Factura no generada'), ('factura_correcta', 'Factura correcta'),
                   ('solicitud_cancelar', 'Cancelación en proceso'), ('factura_cancelada', 'Factura cancelada'),
                   ('solicitud_rechazada', 'Cancelación rechazada'), ],
        string=_('Estado de factura'),
        default='factura_no_generada',
        readonly=True
    )

    qr_value = fields.Char(string=_('QR Code Value'))
    qrcode_image = fields.Binary("QRCode")

    invoice_date = fields.Datetime(string="Fecha de factura")
    retencion_line_ids = fields.One2many('cfdi.retencion.line', 'cfdi_retencion_id', string='CFDI Retencion Line', copy=True)
    currency_id = fields.Many2one('res.currency',string='Moneda',default=lambda self: self.env['res.company']._company_default_get('cfdi.retencion').currency_id, required=True)
    amount_operation = fields.Float(string='Monto operación', store=True, readonly=True, compute='_compute_amount',
                                   currency_field='currency_id')
    amount_exento = fields.Float(string='Exento', store=True, readonly=True, compute='_compute_amount',
                                   currency_field='currency_id')
    amount_gravado = fields.Float(string='Gravado', store=True, readonly=True, compute='_compute_amount',
                                   currency_field='currency_id')
    amount_retenido = fields.Float(string='Total retenido', store=True, readonly=True, compute='_compute_amount',
                                   currency_field='currency_id')

    numero_cetificado = fields.Char(string=_('Numero de cetificado'))
    cetificaso_sat = fields.Char(string=_('Cetificao SAT'))
    folio_fiscal = fields.Char(string=_('Folio Fiscal'), readonly=True)
    fecha_certificacion = fields.Char(string=_('Fecha y Hora Certificación'))
    cadena_origenal = fields.Char(string=_('Cadena Origenal del Complemento digital de SAT'))
    selo_digital_cdfi = fields.Char(string=_('Selo Digital del CDFI'))
    selo_sat = fields.Char(string=_('Selo del SAT'))
    moneda = fields.Char(string=_('Moneda'))
    tipocambio = fields.Char(string=_('TipoCambio'))
    number_folio = fields.Char(string=_('Folio'), compute='_get_number_folio')
    amount_to_text = fields.Char('Amount to Text', compute='_get_amount_to_text',
                                 size=256, 
                                 help='Amount of the invoice in letter')
    qr_value = fields.Char(string=_('QR Code Value'))
    invoice_datetime = fields.Char(string=_('11/12/17 12:34:12'))
    proceso_timbrado = fields.Boolean(string=_('Proceso de timbrado'))

    company_id = fields.Many2one('res.company', 'Compañia',
                                 default=lambda self: self.env['res.company']._company_default_get('cfdi.retencion'))

    tipo_relacion = fields.Selection(
        selection=[('01', 'Nota de crédito de los documentos relacionados'),
                   ('02', 'Nota de débito de los documentos relacionados'),
                   ('03', 'Devolución de mercancía sobre facturas o traslados previos'),
                   ('04', 'Sustitución de los CFDI previos'),
                   ('05', 'Traslados de mercancías facturados previamente'),
                   ('06', 'Factura generada por los traslados previos'),
                   ('07', 'CFDI por aplicación de anticipo')],
        string=_('Tipo relación')
    )

    uuid_relacionado = fields.Char(string=_('CFDI Relacionado'))

    ####### Campos para complemento dividendos    #################
    tipo_diviendo = fields.Selection(
        selection=[('01', 'Proviene de CUFIN'),
                   ('02', 'No proviene de CUFIN'),
                   ('03', 'Reembolso o reducción de capital'),
                   ('04', 'Liquidación de la persona moral'),
                   ('05', 'CUFINRE'),
                   ('06', 'Proviene de CUFIN al 31 de diciembre 2013.'), ],
        string=_('Tipo dividendo o utilidad distribuida'),
    )
    montisracredmx = fields.Float(string='Monto ISR acreditado Mexico')
    montisracredex = fields.Float(string='Monto ISR acreditado Extranjero')
    montretex = fields.Float(string='Monto ISR retenido Extranjero')
    tiposocdistr = fields.Selection(
        selection=[('Sociedad Nacional', 'Sociedad Nacional'),
                   ('Sociedad Extranjera', 'Sociedad Extranjera'), ],
        string=_('Tipo de sociedad'),
    )
    montisracrednal = fields.Float(string='Monto ISR acreditable nacional')
    montdivacumnal = fields.Float(string='Monto dividendo acumulable nacional')
    montdivacumnex = fields.Float(string='Monto dividendo acumulable extranjero')
    div_remanente = fields.Float(string='Remanente')

    ############### Campos complemento pagos a extranjeros ###########################
    benefefectdelcobro = fields.Selection(
        selection=[('SI', 'SI'),
                   ('NO', 'NO'), ],
        string=_('Beneficiario Efectivo del Cobro'), default='SI'
    )
    pais_residencia = fields.Many2one('res.country', string='Pais de residencia del extrajero')
    concepto_pago = fields.Selection(
        selection=[('1', 'Artistas, deportistas y espectáculos públicos'),
                   ('2', 'Otras personas físicas'),
                   ('3', 'Persona moral'),
                   ('4', 'Fideicomiso'),
                   ('5', 'Asociación en participación'),
                   ('6', 'Organizaciones Internacionales o de gobierno'),
                   ('7', 'Organizaciones exentas'),
                   ('8', 'Agentes pagadores'),
                   ('9', 'Otros'),],
        string=_('Concepto de pago'),
    )
    descripcion_concepto = fields.Char(string="Descripcion / Concepto")
    rfc_beneficiario = fields.Char(string="RFC Representante legal")
    curp_beneficiario = fields.Char(string="CURP Representante legal")
    razon_social_beneficiario = fields.Char(string="Razón social del beneficiario")
    ###########################################################################

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = dict(default or {})
        if self.estado_factura == 'factura_correcta' or self.estado_factura == 'factura_cancelada':
            default['estado_factura'] = 'factura_no_generada'
            default['folio_fiscal'] = ''
            default['fecha_factura'] = None
            default['factura_cfdi'] = False
        return super(CfdiRetencion, self).copy(default=default)

    @api.depends('number')
    def _get_number_folio(self):
        if self.number:
            self.number_folio = self.number.replace('RET','').replace('/', '')

    @api.model
    def _get_amount_2_text(self, amount_total):
        return amount_to_text_es_MX.get_amount_to_text(self, amount_total, 'es_cheque', self.currency_id.name)

    @api.model
    def _default_journal(self):
        if not self.journal_id:
            company_id = self._context.get('default_company_id', self.env.company.id)
            return self.env['account.journal'].search([('type','=','sale'),('company_id', '=', company_id)],limit=1)

    journal_id = fields.Many2one('account.journal', 'Diario', default=_default_journal)

    @api.model
    def create(self, vals):
        if vals.get('number', _('Draft Invoice')) == _('Draft Invoice'):
            if 'company_id' in vals:
                vals['number'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('cfdi.retencion') or _('Draft Invoice')
            else:
                vals['number'] = self.env['ir.sequence'].next_by_code('cfdi.retencion') or _('Draft Invoice')
        result = super(CfdiRetencion, self).create(vals)
        return result

    def action_valid(self):
        self.write({'state': 'valid'})
        self.invoice_date = datetime.datetime.now()
        
    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_draft(self):
        self.write({'state': 'draft'})

    @api.depends('retencion_line_ids')
    def _compute_amount(self):
        round_curr = self.currency_id.round
        self.amount_operation = sum(line.monto_base for line in self.retencion_line_ids)
        self.amount_exento = sum(round_curr(line.monto_exento) for line in self.retencion_line_ids)
        self.amount_gravado = sum(line.monto_gravado for line in self.retencion_line_ids)
        self.amount_retenido = sum(round_curr(line.monto_retenido) for line in self.retencion_line_ids)

    @api.model
    def to_json(self):
        self.check_cfdi_values()

        nombre = self.partner_id.name.upper()
        zipreceptor = self.partner_id.zip

        #corregir hora
        timezone = self._context.get('tz')
        if not timezone:
            timezone = self.journal_id.tz or self.env.user.partner_id.tz or 'America/Mexico_City'
        # timezone = tools.ustr(timezone).encode('utf-8')

        local = pytz.timezone(timezone)
        if not self.fecha_factura:
           naive_from = datetime.datetime.now()
        else:
           naive_from = self.fecha_factura
        local_dt_from = naive_from.replace(tzinfo=pytz.UTC).astimezone(local)
        date_from = local_dt_from.strftime ("%Y-%m-%dT%H:%M:%S")
        if not self.fecha_factura:
           self.fecha_factura = datetime.datetime.now()

        request_params = {
                'factura': {
                      'FolioInt': self.number.replace('RET','').replace('/',''),
                      'FechaExp': date_from,
                      'CveRetenc': self.retencion,
                      'LugarExpRetenc': self.journal_id.codigo_postal or self.company_id.zip,
                      'DescRetenc': '0',
                      'serie': 'R',
                      'folio': self.number.replace('RET','').replace('/',''),
                },
                'emisor': {
                      'RfcE': self.company_id.vat.upper(),
                      'rfc': self.company_id.vat.upper(),
                      'NomDenRazSocE': self.company_id.nombre_fiscal.upper(),
                      'RegimenFiscalE': self.company_id.regimen_fiscal_id.code,
                },
                'receptor': {
                      'NacionalidadR': 'Nacional' if self.partner_id.vat.upper() != 'XEXX010101000' else 'Extranjero',
                      'NomDenRazSocR': nombre,
                      'RfcR': self.partner_id.vat.upper() if self.partner_id.vat.upper() != 'XEXX010101000' else '',
                      'CurpR': '', #revisar este!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                      'DomicilioFiscalR': self.partner_id.zip,
                      'NumRegIdTribR': self.partner_id.registro_tributario if self.partner_id.vat.upper() == 'XEXX010101000' else '',
                },
                'periodo': {
                      'MesIni': self.periodo_inicio,
                      'MesFin': self.periodo_final,
                      'Ejercicio': self.ejercicio,
                },
                'totales': {
                      'MontoTotOperacion': self.amount_operation,
                      'MontoTotaGrav': self.amount_gravado,
                      'MontoTotExent': self.amount_exento,
                      'MontoTotRet': self.amount_retenido,
                  #    'UtilidadBimestral': self.periodo_final, #opcional
                  #    'ISRCorrespondiente': self.ejercicio,  #opcional
                },
                'retencion': {
                      'tipo': 'Retencion',
                      'cfdi': '4.0',
                      'odoo': '17',
                      'version': '1',
                      'rfc': self.company_id.vat.upper(),
                      'modo_prueba': self.company_id.modo_prueba,
                },
        }

        items = {'numerodepartidas': len(self.retencion_line_ids)}
        retencion_lines = []
        for line in self.retencion_line_ids:
                retencion_lines.append({'BaseRet': line.monto_base,
                                      'ImpuestoRet': line.impuesto,
                                      'MontoRet': line.monto_retenido,
                                      'TipoPagoRet': line.tipo_pago,})

        request_params.update({'ImpRetenidos': retencion_lines})

        if self.uuid_relacionado:
            cfdi_relacionado = []
            uuids = self.uuid_relacionado.replace(' ', '').split(',')
            for uuid in uuids:
                cfdi_relacionado.append({
                    'uuid': uuid,
                })
            request_params.update({'CfdisRelacionados': {'UUID': cfdi_relacionado, 'TipoRelacion': self.tipo_relacion}})

        #######     Agrega complemento dividendos    #################
        if self.complemento_c:
            request_params.update({
                    'DividOUtil': {
                         'CveTipDivOUtil': self.tipo_diviendo,
                         'MontISRAcredRetMexico': self.montisracredmx,
                         'MontISRAcredRetExtranjero': self.montisracredex,
                         'MontRetExtDivExt': self.montretex,
                         'TipoSocDistrDiv': self.tiposocdistr,
                         'MontISRAcredNal': self.montisracrednal,
                         'MontDivAcumNal': self.montdivacumnal,
                         'MontDivAcumExt': self.montdivacumnex,
                    },
                    'Remanente': {
                         'ProporcionRem': self.div_remanente
                    }
            })
        #######     Agrega complemento pagos a extranjeros    #################
        if self.complemento_g:
            if self.benefefectdelcobro == 'NO':
               request_params.update({
                    'Pagosaextranjeros': {
                         'EsBenefEfectDelCobro': self.benefefectdelcobro,
                         'PaisDeResidParaEfecFisc': self.pais_residencia.code,
                         'ConceptoPago': self.concepto_pago,
                         'DescripcionConcepto': self.descripcion_concepto,
                    },
               })
            elif self.benefefectdelcobro == 'SI':
               request_params.update({
                    'Pagosaextranjeros': {
                         'EsBenefEfectDelCobro': self.benefefectdelcobro,
                         'ConceptoPago': self.concepto_pago,
                         'DescripcionConcepto': self.descripcion_concepto,
                         'RFC': self.rfc_beneficiario,
                         'CURP': self.curp_beneficiario,
                         'NomDenRazSocB': self.razon_social_beneficiario,
                    },
               })

        return request_params

    def clean_text(self, text):
        clean_text = text.replace('\n', ' ').replace('\\', ' ').replace('-', ' ').replace('/', ' ').replace('|', ' ')
        clean_text = clean_text.replace(',', ' ').replace(';', ' ').replace('>', ' ').replace('<', ' ')
        return clean_text[:1000]

    def check_cfdi_values(self):
        if not self.company_id.vat:
            self.write({'proceso_timbrado': False})
            self.env.cr.commit()
            raise UserError(_('El emisor no tiene RFC configurado.'))
        if not self.company_id.name:
            self.write({'proceso_timbrado': False})
            self.env.cr.commit()
            raise UserError(_('El emisor no tiene nombre configurado.'))
        if not self.partner_id.vat:
            self.write({'proceso_timbrado': False})
            self.env.cr.commit()
            raise UserError(_('El receptor no tiene RFC configurado.'))
        if not self.company_id.regimen_fiscal_id:
            self.write({'proceso_timbrado': False})
            self.env.cr.commit()
            raise UserError(_('El emisor no régimen fiscal configurado.'))
        if not self.journal_id.codigo_postal and not self.company_id.zip:
            self.write({'proceso_timbrado': False})
            self.env.cr.commit()
            raise UserError(_('El emisor no tiene código postal configurado.'))

    def _set_data_from_xml(self, xml_invoice):
        if not xml_invoice:
            return None
        NSMAP = {
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'retenciones': 'http://www.sat.gob.mx/esquemas/retencionpago/2',
            'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital',
        }

        xml_data = etree.fromstring(xml_invoice)
        Complemento = xml_data.find('retenciones:Complemento', NSMAP)
        TimbreFiscalDigital = Complemento.find('tfd:TimbreFiscalDigital', NSMAP)

        #self.tipocambio = xml_data.attrib['TipoCambio']
    #    self.moneda = xml_data.attrib['Moneda']
        self.numero_cetificado = xml_data.attrib['NoCertificado']
        self.cetificaso_sat = TimbreFiscalDigital.attrib['NoCertificadoSAT']
        self.fecha_certificacion = TimbreFiscalDigital.attrib['FechaTimbrado']
        self.selo_digital_cdfi = TimbreFiscalDigital.attrib['SelloCFD']
        self.selo_sat = TimbreFiscalDigital.attrib['SelloSAT']
        self.folio_fiscal = TimbreFiscalDigital.attrib['UUID']
        self.invoice_datetime = xml_data.attrib['FechaExp']
        version = TimbreFiscalDigital.attrib['Version']
        self.cadena_origenal = '||%s|%s|%s|%s|%s||' % (version, self.folio_fiscal, self.fecha_certificacion,
                                                       self.selo_digital_cdfi, self.cetificaso_sat)

        options = {'width': 275 * mm, 'height': 275 * mm}
        amount_str = str(self.amount_operation).split('.')
        qr_value = 'https://verificacfdi.facturaelectronica.sat.gob.mx/default.aspx?&id=%s&re=%s&rr=%s&tt=%s.%s&fe=%s' % (
            self.folio_fiscal,
            self.company_id.vat,
            self.partner_id.vat,
            amount_str[0].zfill(10),
            amount_str[1].ljust(6, '0'),
            self.selo_digital_cdfi[-8:],
        )
        self.qr_value = qr_value
        ret_val = createBarcodeDrawing('QR', value=qr_value, **options)
        self.qrcode_image = base64.encodebytes(ret_val.asString('jpg'))

    def action_cfdi_generate(self):
        # after validate, send invoice data to external system via http post
        for invoice in self:
            if invoice.proceso_timbrado:
                return True
            else:
                invoice.write({'proceso_timbrado': True})
                self.env.cr.commit()
            if invoice.estado_factura == 'factura_correcta':
                if invoice.folio_fiscal:
                    invoice.write({'factura_cfdi': True})
                    return True
                else:
                    invoice.write({'proceso_timbrado': False})
                    self.env.cr.commit()
                    raise UserError(_('Error para timbrar factura, Factura ya generada.'))
            if invoice.estado_factura == 'factura_cancelada':
                invoice.write({'proceso_timbrado': False})
                self.env.cr.commit()
                raise UserError(_('Error para timbrar factura, Factura ya generada y cancelada.'))

            values = invoice.to_json()
            #_logger.info('Envia: %s', values)

            if invoice.company_id.proveedor_timbrado == 'servidor':
                url = '%s' % ('https://facturacion.itadmin.com.mx/api/invoice')
            elif invoice.company_id.proveedor_timbrado == 'servidor2':
                url = '%s' % ('https://facturacion2.itadmin.com.mx/api/invoice')
            else:
                invoice.write({'proceso_timbrado': False})
                self.env.cr.commit()
                raise UserError(_('Error, falta seleccionar el servidor de timbrado en la configuración de la compañía.'))

            try:
                response = requests.post(url,
                                         auth=None, data=json.dumps(values),
                                         headers={"Content-type": "application/json"})
            except Exception as e:
                error = str(e)
                invoice.write({'proceso_timbrado': False})
                self.env.cr.commit()
                if "Name or service not known" in error or "Failed to establish a new connection" in error:
                    raise UserError("No se pudo conectar con el servidor.")
                else:
                    raise UserError(error)

            if "Whoops, looks like something went wrong." in response.text:
                invoice.write({'proceso_timbrado': False})
                self.env.cr.commit()
                raise UserError("Error en el proceso de timbrado, espere un minuto y vuelva a intentar timbrar nuevamente. \nSi el error aparece varias veces reportarlo con la persona de sistemas.")
            else:
                json_response = response.json()
            estado_factura = json_response['estado_factura']
            if estado_factura == 'problemas_factura':
                invoice.write({'proceso_timbrado': False})
                self.env.cr.commit()
                raise UserError(_(json_response['problemas_message']))
            # Receive and stroe XML invoice
            if json_response.get('factura_xml'):
                invoice._set_data_from_xml(base64.b64decode(json_response['factura_xml']))
                file_name = invoice.number.replace('/', '_') + '.xml'
                self.env['ir.attachment'].sudo().create(
                    {
                        'name': file_name,
                        'datas': json_response['factura_xml'],
                        # 'datas_fname': file_name,
                        'res_model': self._name,
                        'res_id': invoice.id,
                        'type': 'binary'
                    })

            invoice.write({'estado_factura': estado_factura,
                           'factura_cfdi': True,
                           'proceso_timbrado': False})
            invoice.message_post(body="CFDI emitido")
        return True

    def action_cfdi_cancel(self):
        for invoice in self:
            if invoice.factura_cfdi:
                if invoice.estado_factura == 'factura_cancelada':
                    pass
                    # raise UserError(_('La factura ya fue cancelada, no puede volver a cancelarse.'))
                if not invoice.company_id.contrasena:
                  raise UserError(_('El campo de contraseña de los certificados está vacío.'))
                domain = [
                    ('res_id', '=', invoice.id),
                    ('res_model', '=', invoice._name),
                    ('name', '=', invoice.number.replace('/', '_') + '.xml')]
                xml_file = self.env['ir.attachment'].search(domain)
                if not xml_file:
                  raise UserError(_('No se encontró el archivo XML para enviar a cancelar.'))
                values = {
                    'rfc': invoice.company_id.vat,
                    'api_key': invoice.company_id.proveedor_timbrado,
                    'uuid': invoice.folio_fiscal,
                    'folio': invoice.number.replace('RET','').replace('/',''),
                    'serie_factura': invoice.journal_id.serie_diario or invoice.company_id.serie_factura,
                    'modo_prueba': invoice.company_id.modo_prueba,
                    'certificados': {
                    #    'archivo_cer': archivo_cer.decode("utf-8"),
                    #    'archivo_key': archivo_key.decode("utf-8"),
                        'contrasena': invoice.company_id.contrasena,
                    },
                    'xml': xml_file[0].datas.decode("utf-8"),
                    'motivo': self.env.context.get('motivo_cancelacion','02'),
                    'foliosustitucion': self.env.context.get('foliosustitucion',''),
                }
                if self.company_id.proveedor_timbrado == 'servidor':
                    url = '%s' % ('https://facturacion.itadmin.com.mx/api/refund')
                elif invoice.company_id.proveedor_timbrado == 'servidor2':
                    url = '%s' % ('https://facturacion2.itadmin.com.mx/api/refund')
                else:
                    raise UserError(_('Error, falta seleccionar el servidor de timbrado en la configuración de la compañía.'))

                try:
                    response = requests.post(url,
                                             auth=None, data=json.dumps(values),
                                             headers={"Content-type": "application/json"})
                except Exception as e:
                    error = str(e)
                    if "Name or service not known" in error or "Failed to establish a new connection" in error:
                        raise UserError("No se pudo conectar con el servidor.")
                    else:
                        raise UserError(error)

                if "Whoops, looks like something went wrong." in response.text:
                    raise UserError("Error en el proceso de timbrado, espere un minuto y vuelva a intentar timbrar nuevamente. \nSi el error aparece varias veces reportarlo con la persona de sistemas.")

                json_response = response.json()

                log_msg = ''
                if json_response['estado_factura'] == 'problemas_factura':
                    raise UserError(_(json_response['problemas_message']))
                elif json_response['estado_factura'] == 'solicitud_cancelar':
                    # invoice.write({'estado_factura': json_response['estado_factura']})
                    log_msg = "Se solicitó cancelación de CFDI"
                elif json_response.get('factura_xml', False):
                    file_name = 'CANCEL_' + invoice.number.replace('/', '_') + '.xml'
                    self.env['ir.attachment'].sudo().create(
                        {
                            'name': file_name,
                            'datas': json_response['factura_xml'],
                            # 'datas_fname': file_name,
                            'res_model': self._name,
                            'res_id': invoice.id,
                            'type': 'binary'
                        })
                    log_msg = "CFDI Cancelado"
                invoice.write({'estado_factura': json_response['estado_factura']})
                # invoice.message_post(body=log_msg)
   
    def send_factura_mail(self):
        self.ensure_one()
        template = self.env.ref('cfdi_retenciones.email_template_factura_retencion', False)
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
            
        ctx = dict()
        ctx.update({
            'default_model': 'cfdi.retencion',
            'default_res_ids': self.ids,
            'default_use_template': bool(template),
            'default_template_id': template.id,
            'default_composition_mode': 'comment',
        })
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

    def unlink(self):
        raise UserError("Los registros no se pueden borrar, solo cancelar.")

class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    def _compute_attachment_ids(self):
        res = super(MailComposeMessage, self)._compute_attachment_ids()
        for rec in self:
            if self.model == 'cfdi.retencion':
                attachment_ids=[]
                template_id = self.env.ref('cfdi_retenciones.email_template_factura_retencion')
                if self.template_id.id == template_id.id:
                    res_ids = ast.literal_eval(self.res_ids)
                    for res_id in res_ids:
                        retencion = self.env[self.model].browse(res_id)
                        domain = [
                            ('res_id', '=', retencion.id),
                            ('res_model', '=', retencion._name),
                            ('name', '=', retencion.number.replace('/', '_') + '.xml')]
                        xml_file = self.env['ir.attachment'].search(domain, limit=1)
                        if xml_file:
                            attachment_ids.extend(rec.attachment_ids.ids)
                            attachment_ids.append(xml_file.id)
                    if attachment_ids:
                        rec.attachment_ids = [(6, 0, attachment_ids)]
        return res

