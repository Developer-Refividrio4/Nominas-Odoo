# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools.misc import xlsxwriter
from odoo.exceptions import UserError
import  requests
import json
import datetime
import io
from datetime import date
import logging
_logger = logging.getLogger(__name__)


class KsDynamicContabilidadCfdi(models.Model):
    _inherit = 'ks.dynamic.financial.base'

    def flatten_data(self, data):
        result = []

        def recursive_flatten(items):
            for item in items:
                result.append(item)
                children = item.get('children', [])
                if children:
                    recursive_flatten(children)

        recursive_flatten(data)
        return result

    def ks_get_xml_cfdi(self, ks_df_informations, selectedOption1, selectedOption2, selectedOption3, selectedOption4):
        ctx = dict(self._context or {})
        lang = self.env.user.lang
        lang_id = self.env['res.lang'].search([('code', '=', lang)])['date_format'].replace('/', '-')

        move_lines, retained, subtotal = self.ks_process_trial_balance(ks_df_informations)

        new_move_lines = self.get_trial_balance_hierarchy_data(move_lines, start=True)
        if new_move_lines:
            hierarchy_move_lines = self.flatten_data(new_move_lines['undefined'])
            #_logger.info('hierarchy_move_lines: %s', hierarchy_move_lines)
        else:
            hierarchy_move_lines = []
        ks_company_id = self.env['res.company'].sudo().browse(ks_df_informations.get('company_id'))

        ks_new_start_date = (datetime.datetime.strptime(
            ks_df_informations['date'].get('ks_start_date'), '%Y-%m-%d').date()).strftime(lang_id)
        for_new_end_date = ks_df_informations['date'].get('ks_end_date') if ks_df_informations['date'].get('ks_end_date') else date.today()
        ks_new_end_date = (datetime.datetime.strptime(str(for_new_end_date), '%Y-%m-%d').date()).strftime(lang_id)
        start_date = datetime.datetime.strptime(ks_df_informations['date'].get('ks_start_date'), '%Y-%m-%d').date()

        url=''
        company = self.env.company
        if company.proveedor_timbrado == 'servidor':
            url = '%s' % ('https://facturacion.itadmin.com.mx/api/contabilidad')
        elif company.proveedor_timbrado == 'servidor2':
            url = '%s' % ('https://facturacion2.itadmin.com.mx/api/contabilidad')
        else:
            raise UserError(_('Error, falta seleccionar el servidor de timbrado en la configuración de la compañía.'))
        
        values = self.to_json(hierarchy_move_lines, selectedOption1, selectedOption2, selectedOption3, start_date, selectedOption4)
        
        response = requests.post(url,auth=None,data=json.dumps(values),headers={"Content-type": "application/json"})

#        _logger.info('something ... %s', response.text)

        json_response = response.json()
        estado_factura = json_response.get('estado_conta','')
        if not estado_factura:
           estado_factura = json_response.get('estado_factura','')
        if estado_factura == 'problemas_contabilidad' or estado_factura == 'problemas_factura':
           raise UserError(_(json_response['problemas_message']))
        if json_response.get('conta_xml'):
            #_logger.info("xml %s", json_response['conta_xml'])
            #_logger.info("zip %s", json_response['conta_zip'])
            #return base64.b64decode(json_response['conta_xml'])
            try:
                form_id = self.env.ref('contabilidad_cfdi.reporte_conta_xml_zip_download_wizard_download_form_view_itadmin').id
            except ValueError:
                form_id = False
            ctx.update({'default_xml_data': json_response['conta_xml'], 'default_zip_data': json_response.get('conta_zip', None),'conta_name':json_response['conta_name']})    
            return {
                'name': 'Descarga documentos generados',   
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'conta.xml.zip.download',
                'views': [(form_id, 'form')],
                'view_id': form_id,
                'target': 'new',
                'context': ctx,
            }
        return True

    @api.model
    def to_json(self, hierarchy_move_lines, selectedOption1, selectedOption2, selectedOption3, ks_new_start_date, selectedOption4):
        company = self.env.company
        if not company.archivo_cer or not company.archivo_key:
           raise UserError("No tiene cargado el certificado correctamente.")
        archivo_cer = company.archivo_cer
        archivo_key = company.archivo_key
        request_params = { 
                'informacion': {
                      'api_key': company.proveedor_timbrado,
                      'modo_prueba': company.modo_prueba,
                      'proceso': '',
                      'RFC': company.vat,
                      'Mes': str(ks_new_start_date.month) if not selectedOption3 == 'ks_mes_13' else '13',
                      'Anio': str(ks_new_start_date.year),
                      'version': '2.0',
                },
                'certificados': {
                      'archivo_cer': archivo_cer.decode("utf-8"),
                      'archivo_key': archivo_key.decode("utf-8"),
                      'contrasena': company.contrasena,
                },}
        account_lines = []
        account_obj = self.env['account.account']

        if selectedOption1 == 'ks_catalog_cuentas':
            debit_tag = self.env.ref('l10n_mx.tag_debit_balance_account', raise_if_not_found=False)
            credit_tag = self.env.ref('l10n_mx.tag_credit_balance_account', raise_if_not_found=False)
            for line in hierarchy_move_lines:
                if len(line.get('code')) > 2:
                    count = 0
                    count = line.get('code').count('.') 
                    code_list = line.get('code').split('.')
                    subctade = ''
                    if len(code_list) > 1:
                        for elemen in code_list[:-1]:
                            subctade += elemen + '.'
                    if subctade.endswith('.'):
                        subctade = subctade[:-1]
                    codagrup = ''
                    if len(code_list) > 2:
                        for elemen in code_list[:-1]:
                            codagrup += elemen + '.'
                        if codagrup.endswith('.'):
                            codagrup = codagrup[:-1]
                    else:
                        codagrup = line.get('code')

                    natur = ''
                    if not line.get('natur'):
                        acc_acc = self.env['account.account'].search([('code', '=', line.get('code'))], limit=1)
                        if debit_tag in acc_acc.tag_ids:
                            natur = 'D'
                        if credit_tag in acc_acc.tag_ids:
                            natur = 'A'
                    else:
                        natur = line.get('natur')
                    account_lines.append({'SubCtaDe': subctade,
                                      'CodAgrup': codagrup,
                                      'NumCta': line.get('code'),
                                      'Desc': line.get('name'),
                                      'Nivel': count + 1,
                                      'Natur': natur,
                                      })
            request_params.update({'Catalogo':{
                         'RFC': company.vat,
                         'Mes': str(ks_new_start_date.month),
                         'Anio': str(ks_new_start_date.year),
                         'Ctas': account_lines
                       },})
            request_params['informacion'].update({'proceso': 'catalogo',})
        else:
            for line in hierarchy_move_lines:
                if len(line.get('code')) > 2:
                   account_lines.append({'NumCta': line.get('code'),
                                      'SaldoIni': round(float(line.get('initial_balance')),2),
                                      'Debe': line.get('debit'),
                                      'Haber': line.get('credit'),
                                      'SaldoFin': round(float(line.get('ending_balance')),2),
                                      })
            request_params.update({'Balanza':{
                         'RFC': company.vat,
                         'Mes': str(ks_new_start_date.month) if not selectedOption3 == 'ks_mes_13' else '13',
                         'Anio': str(ks_new_start_date.year),
                         'TipoEnvio': 'N' if selectedOption2 != 'ks_complenmentaria' else 'C',
                         'FechaModBal': selectedOption4 if selectedOption2 == 'ks_complenmentaria' else '',
                         'Ctas': account_lines
                       },})
            request_params['informacion'].update({'proceso': 'balanza',})

        #_logger.info('dump: ' + json.dumps(request_params))
        return request_params

class ContaXMLZIPDownload(models.TransientModel):
    _name = 'conta.xml.zip.download'
    
    xml_data = fields.Binary("XML File")
    zip_data = fields.Binary("Zip File")

    def download_xml_zip_file(self):
        if self._context.get('file_type','')=='zip':
            field_name = 'zip_data'
            filename = '%s.zip'%self._context.get('conta_name')
        else:
            field_name = 'xml_data'
            filename = '%s.xml'%self._context.get('conta_name')
        return {
                'type' : 'ir.actions.act_url',
                'url': "/web/content/?model="+self._name+"&id=" + str(self.id) + "&field="+field_name+"&download=true&filename="+filename,
                'target':'self',
                }   
