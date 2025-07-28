# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
import calendar
import json
import logging
import base64
_logger = logging.getLogger(__name__)

class TablasDiotTercero(models.Model):
    _name = 'tablas.diot.tercero'
    _description = 'TablasDiotTercero'

    form_id = fields.Many2one('diot.cfdi', string='DIOT', required=True)
    valor01 = fields.Selection(
        selection=[('04', _('04 - Proveedor nacional')),
                   ('05', _('05 - Proveedor extranjero')),
                   ('15', _('15 - Proveedor global')),],string=_('Tipo de tercero'),) #uno
    
    valor02 = fields.Selection(
        selection=[
                   ('02', _('02 - Enajenación de bienes')),
                   ('03', _('03 - Prestación de servicio profesionales')),
                   ('06', _('06 - Uso o goce temporal de bienes')),
                   ('07', _('07 - Importación de bienes o servicios')),
                   ('08', _('08 - Importación por transferencia virtual')),
                   ('85', _('85 - Otros')),
                   ('87', _('87 - Operaciones globales')),],
        string=_('Tipo de opreacion'),
    )
    valor03 = fields.Char("RFC") #tres
    valor04 = fields.Char(string='No. ID fiscal') #cuatro
    valor05 = fields.Char(string='Nombre') #cinco
    valor06 = fields.Char(string='Pais') # seis
    valor07 = fields.Char(string='Especificar lugar') # siete

    #### Valor de los actos o actividades #####
    valor08 = fields.Integer('Actos Pagados RFN') #ocho
    valor09 = fields.Integer('Dev. Desc. y Bon RFN') #nueve
    valor10 = fields.Integer('Actos Pagados RFS') #diez
    valor11 = fields.Integer('Dev. Desc. y Bon RFS') #once
    valor12 = fields.Integer('Base 16%') #doce
    valor13 = fields.Integer('Dev. Desc. y Bon 16%') #trece
    valor14 = fields.Integer('Importacion 16%') #catorce
    valor15 = fields.Integer('Dev. Desc. y Bon Import 16%') #quince
    valor16 = fields.Integer('Importacion intangibles 16%') #dieciseis
    valor17 = fields.Integer('Dev. Desc. y Bon Import Int. 16%') #diecisiete

    #### IVA Acreditable #####
    valor18 = fields.Integer('Actividades pagadas RFN') 
    valor19 = fields.Integer('Proporción de act pag RFN')
    valor20 = fields.Integer('Actividades pagadas RFS')
    valor21 = fields.Integer('Proporción de act pag RFS')
    valor22 = fields.Integer('Actividades pagadas 16%') 
    valor23 = fields.Integer('Proporción de act pag 16%') 
    valor24 = fields.Integer('Actividades pagadas Import. Tan.')
    valor25 = fields.Integer('Proporción de act pag Import Tan%')
    valor26 = fields.Integer('Actividades pagadas Import. Intan.')
    valor27 = fields.Integer('Proporción de act pag Import. Intan.')

    #### IVA No Acreditable #####
    valor28 = fields.Integer('Proporcion Act Pag RFN') 
    valor29 = fields.Integer('Actos no cumple RFN')
    valor30 = fields.Integer('Actos Exentas Pag RFN')
    valor31 = fields.Integer('Actos No obj. Pag RFN')

    valor32 = fields.Integer('Proporcion Act Pag RFS') 
    valor33 = fields.Integer('Actos no cumple RFS') 
    valor34 = fields.Integer('Actos Exentas Pag RFS')
    valor35 = fields.Integer('Actos No obj. Pag RFS')

    valor36 = fields.Integer('Proporcion Act Pag 16%')
    valor37 = fields.Integer('Actos no cumple 16%')
    valor38 = fields.Integer('Actos Exentas Pag 16%') 
    valor39 = fields.Integer('Actos No obj. Pag 16%')

    valor40 = fields.Integer('Proporcion Act Pag Imp')
    valor41 = fields.Integer('Actos no cumple Imp')
    valor42 = fields.Integer('Actos Exentas Pag Imp') 
    valor43 = fields.Integer('Actos No obj. Pag Imp') 

    valor44 = fields.Integer('Proporcion Act Pag Imp No Tan')
    valor45 = fields.Integer('Actos no cumple Imp No Tan')
    valor46 = fields.Integer('Actos Exentas Pag Imp No Tan')
    valor47 = fields.Integer('Actos No obj. Pag Imp No Tan')

    #### Datos adicionales #####
    valor48 = fields.Integer('IVA retenido') 
    valor49 = fields.Integer('Importacion Exento')
    valor50 = fields.Integer('Actividades Exentos')
    valor51 = fields.Integer('0% IVA')
    valor52 = fields.Integer('No obj en territorio Nac.') 
    valor53 = fields.Integer('No obj sin est en terr Nac') 
    valor54 = fields.Selection(
        selection=[('01', 'Sí'), 
                   ('02', 'No'), 
                   ],
        string=_('Manifiesto'),)

class DiotCfdi(models.Model):
    _name = 'diot.cfdi'
    _description = 'DiotCFDI'
    _rec_name = "name"

    name = fields.Char("Nombre", required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    month = fields.Selection([('01','Enero'),('02','Febrero'),('03','Marzo'),('04','Abril'),('05','Mayo'),('06','Junio'),('07','Julio'),('08','Agosto'),('09','Septiembre'),('10','Octubre'),('11', 'Noviembre'),('12','Diciembre')], string='Mes', required=1)
    year = fields.Char("Año", required=1)

    tabla_tercero = fields.One2many('tablas.diot.tercero', 'form_id', copy=True) 

    state = fields.Selection([('draft', 'Borrador'), ('done', 'Hecho')], string='Estado', default='draft')
    file_content = fields.Binary("Archivo")

    def action_validate(self):
        self.write({'state':'done'})

    @api.model
    def init(self):
        company_id = self.env['res.company'].search([])
        for company in company_id:
            diot_sequence = self.env['ir.sequence'].search([('code', '=', 'diot.cfdi'), ('company_id', '=', company.id)])
            if not diot_sequence:
                diot_sequence.create({
                        'name': 'DIOT 2025',
                        'code': 'diot.cfdi',
                        'padding': 4,
                        'company_id': company.id,
                    })

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
           if vals.get('name', _('New')) == _('New'):
               if 'company_id' in vals:
                   vals['name'] = self.env['ir.sequence'].with_company(vals['company_id']).next_by_code('diot.cfdi') or _('New')
               else:
                   vals['name'] = self.env['ir.sequence'].next_by_code('diot.cfdi') or _('New')
        result = super(DiotCfdi, self).create(vals_list)
        return result

    def action_compute(self):
        self.tabla_tercero.unlink()

        date_from = self.year+'-'+self.month+'-01'
        date_to = self.year+'-'+self.month+'-'+str(calendar.monthrange(int(self.year),int(self.month))[1])

        payment_ids = self.env['account.payment'].search([
                                                           ('payment_type','=', 'outbound'),
                                                           ('is_internal_transfer','=', False),
                                                           ('date', '>=',date_from), 
                                                           ('date', '<=',date_to),
                                                           ('diot','=', True),
                                                           ])

        line_vals = {}
        for payment in payment_ids:
            #_logger.info('factura %s', payment.name)
            partner = payment.partner_id
            partner_id = partner.id
            if partner_id not in line_vals and payment.reconciled_bill_ids:
                line_vals[partner_id] = {
                                         'valor01' : partner.tipo_proveedor, #uno
                                         'valor02' : partner.tipo_operacion, #dos
                                         'valor03' : partner.vat,  #tres
                                         'valor04' : partner.tipo_proveedor == '05' and partner.registro_tributario or '', #cuatro
                                         'valor05' : partner.name,   #cinco
                                         'valor06' : partner.tipo_proveedor == '05' and partner.pais_diot.c_pais or '', #seis
                                         'valor07' : partner.pais_diot.c_pais == 'ZZZ' and partner.pais_diot.descripcion or ''  #siete
                                         }
            if payment.reconciled_bill_ids:
                for invoice in payment.reconciled_bill_ids:
                    payment_dict = invoice.invoice_payments_widget
                    if not payment_dict:
                       continue
                    payment_content = payment_dict['content']
                    for invoice_payments in payment_content:
                        if invoice_payments['account_payment_id'] == payment.id:
                            paid_pct = invoice_payments['amount'] / invoice.amount_total
                            tax_lines={}
                            for invoice_line in invoice.invoice_line_ids:
                                price_reduce = invoice_line.price_unit * (1.0 - invoice_line.discount / 100.0)
                                if invoice_line.tax_ids:
                                    res = invoice_line.tax_ids.compute_all(price_reduce, quantity=invoice_line.quantity, product=invoice_line.product_id, partner=invoice.partner_id)
                                    taxes = res['taxes']
                                    for tax in taxes:
                                        if (tax['id'],tax['name']) not in tax_lines:
                                            tax_lines[(tax['id'],tax['name'])] = tax.get('base') 
                                        else:
                                            tax_lines[(tax['id'],tax['name'])] = tax_lines[(tax['id'],tax['name'])] + tax.get('base')

                            for tax_line, values in tax_lines.items():
                                if payment.payment_type == 'outbound':
                                    rate = 1
                                    if invoice.currency_id.name != 'MXN':
                                       vals = self.env['res.currency.rate'].search([('currency_id','=',invoice.currency_id.id),('name','<=',invoice_payments['date'])],order='name desc',limit=1)
                                       rate =  1  / vals.rate

                                    tax_used = self.env['account.tax'].search([('name','=', tax_line[1])], limit=1)
                                    if tax_used.amount == 16.0 and partner.vat != 'XEXX010101000' and not payment.diot_no_acreditable:      
                                        line_vals[partner_id].update({'valor12': values * paid_pct * rate + line_vals[partner_id].get('valor12',0)})  # 12
                                        line_vals[partner_id].update({'valor22': values * paid_pct * rate * tax_used.amount/100 + line_vals[partner_id].get('valor22',0)}) # 22

                                    elif tax_used.amount == 8.0 and partner.vat != 'XEXX010101000' and partner.tipo_frontera == '01' and not payment.diot_no_acreditable: 
                                        line_vals[partner_id].update({'valor08': values * paid_pct * rate + line_vals[partner_id].get('valor08',0)}) # 8
                                        line_vals[partner_id].update({'valor18': values * paid_pct * rate * tax_used.amount/100 + line_vals[partner_id].get('valor18',0)}) # 18

                                    elif tax_used.amount == 8.0 and partner.vat != 'XEXX010101000' and partner.tipo_frontera == '02' and not payment.diot_no_acreditable: 
                                        line_vals[partner_id].update({'valor10': values * paid_pct * rate + line_vals[partner_id].get('valor10',0)}) # 10
                                        line_vals[partner_id].update({'valor20': values * paid_pct * rate * tax_used.amount/100 + line_vals[partner_id].get('valor20',0)}) # 20

                                    #elif tax_used.amount == 15.0 and partner.vat != 'XEXX010101000' and not payment.diot_no_acreditable:
                                    #    line_vals[partner_id].update({'valor13': values * paid_pct * rate + line_vals[partner_id].get('valor13',0)})
                                    elif tax_used.amount == 16.0 and partner.vat != 'XEXX010101000' and payment.diot_no_acreditable:
                                        line_vals[partner_id].update({'valor36': values * paid_pct * rate + line_vals[partner_id].get('valor36',0)}) # 36

                                    elif tax_used.amount < 0.0 and partner.vat != 'XEXX010101000' and not payment.diot_no_acreditable and tax_used.impuesto == '002':
                                        line_vals[partner_id].update({'valor48': values * paid_pct * rate * abs(tax_used.amount)/100 + line_vals[partner_id].get('valor48',0)}) #48

                                    elif tax_used.amount == 0.0 and partner.vat == 'XEXX010101000' and tax_used.tipo_factor == 'Exento':
                                        line_vals[partner_id].update({'valor49': values * paid_pct * rate + line_vals[partner_id].get('valor49',0)}) # 49

                                    elif tax_used.amount == 0.0 and partner.vat != 'XEXX010101000' and tax_used.tipo_factor == 'Exento':
                                        line_vals[partner_id].update({'valor50': values * paid_pct * rate + line_vals[partner_id].get('valor50',0)}) # 50

                                    elif tax_used.amount == 0.0 and partner.vat != 'XEXX010101000' and tax_used.tipo_factor != 'Exento':
                                        line_vals[partner_id].update({'valor51': values * paid_pct * rate + line_vals[partner_id].get('valor51',0)}) # 51

        ########## agregar IVA de Pedimentos
        iva_pedimentos_ids = self.env['iva.pedimentos'].search([
                                                           ('fecha', '>=',date_from), 
                                                           ('fecha', '<=',date_to),
                                                           ])
        if iva_pedimentos_ids:
            for iva_pedimentos in iva_pedimentos_ids: 
                partner = iva_pedimentos.partner_id
                if partner.id not in line_vals:
                    line_vals[partner.id] = {
                                         'valor01' : partner.tipo_proveedor, #uno
                                         'valor02' : partner.tipo_operacion, #dos
                                         'valor03' : partner.vat,  #tres
                                         'valor04' : partner.tipo_proveedor == '05' and partner.registro_tributario or '', #cuatro
                                         'valor05' : partner.tipo_proveedor == '05' and partner.name or '',   #cinco
                                         'valor06' : partner.tipo_proveedor == '05' and partner.pais_diot.nacionalidad or '', #seis
                                         'valor07' : partner.tipo_proveedor == '05' and partner.pais_diot.c_pais or ''  #siete
                                         }
                line_vals[partner.id].update({'valor40': round(iva_pedimentos.monto_iva / 0.16,2) + line_vals[partner.id].get('valor40',0)})

        tabla_tercero_obj = self.env['tablas.diot.tercero']

        for partner_id, vals in line_vals.items():
            tabla_tercero_obj.create({
                  'valor01': vals['valor01'],
                  'valor02': vals['valor02'],
                  'valor03': vals['valor03'],
                  'valor04': vals['valor04'],
                  'valor05': vals['valor05'],
                  'valor06': vals['valor06'],
                  'valor07': vals['valor07'],
                  'valor08': round(vals['valor08']) if 'valor08' in vals else '',
                  'valor09': round(vals['valor09']) if 'valor09' in vals else '',
                  'valor10': round(vals['valor10']) if 'valor10' in vals else '',
                  'valor11': round(vals['valor11']) if 'valor11' in vals else '',
                  'valor12': round(vals['valor12']) if 'valor12' in vals else '',
                  'valor13': round(vals['valor13']) if 'valor13' in vals else '',
                  'valor14': round(vals['valor14']) if 'valor14' in vals else '',
                  'valor15': round(vals['valor15']) if 'valor15' in vals else '',
                  'valor16': round(vals['valor16']) if 'valor16' in vals else '',
                  'valor17': round(vals['valor17']) if 'valor17' in vals else '',
                  'valor18': round(vals['valor18']) if 'valor18' in vals else '',
                  'valor19': round(vals['valor19']) if 'valor19' in vals else '',
                  'valor20': round(vals['valor20']) if 'valor20' in vals else '',
                  'valor21': round(vals['valor21']) if 'valor21' in vals else '',
                  'valor22': round(vals['valor22']) if 'valor22' in vals else '',
                  'valor23': round(vals['valor23']) if 'valor23' in vals else '',
                  'valor24': round(vals['valor24']) if 'valor24' in vals else '',
                  'valor25': round(vals['valor25']) if 'valor25' in vals else '',
                  'valor26': round(vals['valor26']) if 'valor26' in vals else '',
                  'valor27': round(vals['valor27']) if 'valor27' in vals else '',
                  'valor28': round(vals['valor28']) if 'valor28' in vals else '',
                  'valor29': round(vals['valor29']) if 'valor29' in vals else '',
                  'valor30': round(vals['valor30']) if 'valor30' in vals else '',
                  'valor31': round(vals['valor31']) if 'valor31' in vals else '',
                  'valor32': round(vals['valor32']) if 'valor32' in vals else '',
                  'valor33': round(vals['valor33']) if 'valor33' in vals else '',
                  'valor34': round(vals['valor34']) if 'valor34' in vals else '',
                  'valor35': round(vals['valor35']) if 'valor35' in vals else '',
                  'valor36': round(vals['valor36']) if 'valor36' in vals else '',
                  'valor37': round(vals['valor37']) if 'valor37' in vals else '',
                  'valor38': round(vals['valor38']) if 'valor38' in vals else '',
                  'valor39': round(vals['valor39']) if 'valor39' in vals else '',
                  'valor40': round(vals['valor40']) if 'valor40' in vals else '',
                  'valor41': round(vals['valor41']) if 'valor41' in vals else '',
                  'valor42': round(vals['valor42']) if 'valor42' in vals else '',
                  'valor43': round(vals['valor43']) if 'valor43' in vals else '',
                  'valor44': round(vals['valor44']) if 'valor44' in vals else '',
                  'valor45': round(vals['valor45']) if 'valor45' in vals else '',
                  'valor46': round(vals['valor46']) if 'valor46' in vals else '',
                  'valor47': round(vals['valor47']) if 'valor47' in vals else '',
                  'valor48': round(vals['valor48']) if 'valor48' in vals else '',
                  'valor49': round(vals['valor49']) if 'valor49' in vals else '',
                  'valor50': round(vals['valor50']) if 'valor50' in vals else '',
                  'valor51': round(vals['valor51']) if 'valor51' in vals else '',
                  'valor52': round(vals['valor52']) if 'valor52' in vals else '',
                  'valor53': round(vals['valor53']) if 'valor53' in vals else '',
                  'form_id': self.id
            })

    def action_export(self):
        rows = []

        for line in self.tabla_tercero:
            if line.valor01 == '04':
                rfc = line.valor03
            elif line.valor01 == '05':
                rfc = ''
            else:
                rfc = 'XAXX010101000'

            if line.valor01 == '05' and line.valor04 == '':
                raise UserError(_("Falta número de identificación fiscal para tercero extranjero"))

            nombre = line.valor05
            if line.valor01 != '05':
                nombre = ''
        
            data = [line.valor01 or '',
                    line.valor02 or '',
                    rfc or '', 
                    line.valor04 or '', 
                    nombre or '',
                    line.valor06 or '',
                    line.valor07 or '',
                    line.valor08 or '',
                    line.valor09 or '',
                    line.valor10 or '',
                    line.valor11 or '',
                    line.valor12 or '',
                    line.valor13 or '',
                    line.valor14 or '',
                    line.valor15 or '',
                    line.valor16 or '',
                    line.valor17 or '',
                    line.valor18 or '',
                    line.valor19 or '',
                    line.valor20 or '',
                    line.valor21 or '',
                    line.valor22 or '',
                    line.valor23 or '',
                    line.valor24 or '',
                    line.valor25 or '',
                    line.valor26 or '',
                    line.valor27 or '',
                    line.valor28 or '',
                    line.valor29 or '',
                    line.valor30 or '',
                    line.valor31 or '',
                    line.valor32 or '',
                    line.valor33 or '',
                    line.valor34 or '',
                    line.valor35 or '',
                    line.valor36 or '',
                    line.valor37 or '',
                    line.valor38 or '',
                    line.valor39 or '',
                    line.valor40 or '',
                    line.valor41 or '',
                    line.valor42 or '',
                    line.valor43 or '',
                    line.valor44 or '',
                    line.valor45 or '',
                    line.valor46 or '',
                    line.valor47 or '',
                    line.valor48 or '',
                    line.valor49 or '',
                    line.valor50 or '',
                    line.valor51 or '',
                    line.valor52 or '',
                    line.valor53 or '',
                    line.valor54 or '',
                    ]
            rows.append('|'.join(str(v) for v in data))

        file_text = '\n'.join(rows)
        filename = 'DIOT_' + self.month + '_' + self.year +'.txt'
        file_text = file_text.encode()
        self.write({'file_content':base64.b64encode(file_text)})
        return {
                'type' : 'ir.actions.act_url',
                'url': "/web/content/?model="+self._name+"&id=" + str(self.id) + "&field=file_content&download=true&filename="+filename+'&mimetype=text/plain',
                'target':'self',
                }
        return

    def action_export_xls(self):
        rows = []

        line = ["Tipo de tercero", "Tipo de operacion","RFC", "No. ID fiscal", "Nombre", "Pais", "Especificar lugar", 
                'Actos Pagados RFN', 'Dev. Desc. y Bon RFN', 'Actos Pagados RFS', 'Dev. Desc. y Bon RFS','Base 16%', 'Dev. Desc. y Bon 16%', 'Importacion 16%',
                'Dev. Desc. y Bon Import 16%', 'Importacion intangibles 16%', 'Dev. Desc. y Bon Import Int. 16%', 'Actividades pagadas RFN', 'Proporción de act pag RFN', 
                'Actividades pagadas RFS', 'Proporción de act pag RFS', 'Actividades pagadas 16%', 'Proporción de act pag 16%', 'Actividades pagadas Import. Tan.', 
                'Proporción de act pag Import Tan%', 'Actividades pagadas Import. Intan.', 'Proporción de act pag Import. Intan.', 'Proporcion Act Pag RFN', 
                'Actos no cumple RFN', 'Actos Exentas Pag RFN', 'Actos No obj. Pag RFN', 'Proporcion Act Pag RFS', 'Actos no cumple RFS', 'Actos Exentas Pag RFS', 
                'Actos No obj. Pag RFS', 'Proporcion Act Pag 16%', 'Actos no cumple 16%', 'Actos Exentas Pag 16%', 'Actos No obj. Pag 16%', 'Proporcion Act Pag Imp',
                'Actos no cumple Imp', 'Actos Exentas Pag Imp', 'Actos No obj. Pag Imp', 'Proporcion Act Pag Imp No Tan', 'Actos no cumple Imp No Tan',
                'Actos Exentas Pag Imp No Tan', 'Actos No obj. Pag Imp No Tan', 'IVA retenido', 'Importacion Exento', 'Actividades Exentos', '0% IVA',
                'No obj en territorio Nac.', 'No obj sin est en terr Nac', 'Manifiesto', 
                ]
        rows.append(','.join(str(v) for v in line)+',')

        for line in self.tabla_tercero:
            if line.valor01 == '04':
                rfc = line.valor03
            elif line.valor01 == '05':
                rfc = ''
            else:
                rfc = 'XAXX010101000'

            if line.valor01 == '05' and line.valor04 == '':
                raise UserError(_("Falta número de identificación fiscal para tercero extranjero"))

            nombre = line.valor05
            if line.valor01 != '05':
                nombre = ''
        
            data = [line.valor01 or '',
                    line.valor02 or '',
                    rfc, 
                    line.valor04 or '', 
                    nombre or '',
                    line.valor06 or '',
                    line.valor07 or '',
                    line.valor08 or '',
                    line.valor09 or '',
                    line.valor10 or '',
                    line.valor11 or '',
                    line.valor12 or '',
                    line.valor13 or '',
                    line.valor14 or '',
                    line.valor15 or '',
                    line.valor16 or '',
                    line.valor17 or '',
                    line.valor18 or '',
                    line.valor19 or '',
                    line.valor20 or '',
                    line.valor21 or '',
                    line.valor22 or '',
                    line.valor23 or '',
                    line.valor24 or '',
                    line.valor25 or '',
                    line.valor26 or '',
                    line.valor27 or '',
                    line.valor28 or '',
                    line.valor29 or '',
                    line.valor30 or '',
                    line.valor31 or '',
                    line.valor32 or '',
                    line.valor33 or '',
                    line.valor34 or '',
                    line.valor35 or '',
                    line.valor36 or '',
                    line.valor37 or '',
                    line.valor38 or '',
                    line.valor39 or '',
                    line.valor40 or '',
                    line.valor41 or '',
                    line.valor42 or '',
                    line.valor43 or '',
                    line.valor44 or '',
                    line.valor45 or '',
                    line.valor46 or '',
                    line.valor47 or '',
                    line.valor48 or '',
                    line.valor49 or '',
                    line.valor50 or '',
                    line.valor51 or '',
                    line.valor52 or '',
                    line.valor53 or '',
                    line.valor54 or '',
                    ]
            rows.append(','.join(str(v) for v in data)+',')

        file_text = '\n'.join(rows)
        filename = 'DIOT_' + self.month + '_' + self.year +'.xls'
        file_text = file_text.encode()
        self.write({'file_content':base64.b64encode(file_text)})
        return {
                'type' : 'ir.actions.act_url',
                'url': "/web/content/?model="+self._name+"&id=" + str(self.id) + "&field=file_content&download=true&filename="+filename+'&mimetype=text/plain',
                'target':'self',
                }
        return

        return request.make_response(
            content,
            headers=[
                ('Content-Disposition', 'attachment; filename="%s"'
                 % filename),
                ('Content-Type', content_type)
            ],
            cookies={'fileToken': token}
        )


    def unlink(self):
        self.tabla_tercero.unlink()
        return super(DiotCfdi, self).unlink()
