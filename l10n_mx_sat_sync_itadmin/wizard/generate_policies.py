# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from lxml import etree
import base64
import json
import os
import xmltodict
from dateutil.parser import parse
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from ..models.special_dict import CaselessDictionary

def convert_to_special_dict(d):
    for k, v in d.items():
        if isinstance(v, dict):
            d.__setitem__(k, convert_to_special_dict(CaselessDictionary(v)))
        else:
            d.__setitem__(k, v)
    return d

import logging
_logger = logging.getLogger(__name__)

class GeneratePoliciesWizard(models.TransientModel):
    _name = 'generate.policies.wizard'
    _description = 'Generate Policies Wizard'

    diario = fields.Many2one('account.journal', string='Diario', required=True)
    cuenta_de_ingreso = fields.Many2one('account.account', string='Cuenta de Ingreso', required=True)
    group_entry = fields.Boolean('Agrupar en una sola poliza')

    def create_journal_entry(self):
        # Retrieve the attachment from the context
        ctx = self._context.copy()
        active_ids = ctx.get('active_ids')
        model = ctx.get('active_model', '')
        if model == 'ir.attachment' and active_ids:
            attachment_ids = self.env[model].browse(active_ids)

#        if self.group_entry:
#           Check of all attachment_ids have same cdfi_type
#           if not show error


        _logger.info('attachment_ids %s', attachment_ids)
        for attachment in attachment_ids:
           if attachment.cfdi_type == 'I':
              _logger.info('attachment %s', attachment)
              if not attachment or not attachment.datas:
                  raise UserError(_('No XML file uploaded.'))
              try:
                  # Decode the XML file data
                  file_coontent = base64.b64decode(attachment.datas)
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

                  xml_file = base64.b64decode(attachment.datas)
                  # Parse the XML file
                  xml_tree = etree.fromstring(xml_file)
                  # Define namespaces used in the XML
                  namespaces = {'cfdi': 'http://www.sat.gob.mx/cfd/4'}
                  # Extract necessary data from XML
                  invoice_line_data = data.get('Comprobante', {}).get('Conceptos', {}).get('Concepto', [])
                  if type(invoice_line_data) != list:
                      invoice_line_data = [invoice_line_data]
                  receptor_rfc =  data.get('Comprobante', {}).get('Receptor', {}).get('@Rfc')
                  total_amount = float(data.get('Comprobante', {}).get('@Total'))
                  # Initialize debit and credit totals
                  total_debit = 0.0
                  total_credit = 0.0
                  lines = []

                  # serach for partner exist or not
                  receptor = self.env['res.partner'].search([('vat', '=', receptor_rfc)], limit=1)
                  if receptor:
                      receivable_account = receptor.property_account_receivable_id
                  else:
                      raise UserError("No se encontró el socio. Configure primero el socio.")

                  # Create the journal entry
                  journal_entry = self.env['account.move'].create({
                      'journal_id': self.diario.id,
                      'date': attachment.date_cfdi, #fields.Date.context_today(self),
                      'ref': f'UUID: {attachment.name}',
                      'move_type': 'entry',
                      'line_ids': [],
                  })
                  _logger.info('UUID 02 %s', attachment.serie_folio)

                  # Create account lines for each Concepto
                  for concept in invoice_line_data:
                      label = concept.get('@Descripcion')
                      amount = float(concept.get('@Importe', '0.0'))
                      # Add line for each concepto
                      lines.append(
                          (0, 0, {
                               'account_id': self.cuenta_de_ingreso.id,
                               'name': label,
                               'credit': amount,
                               'debit': 0.0,
                           })
                      )

                      taxes = concept.get('Impuestos', {}).get('Traslados', {}).get('Traslado')
                      if taxes:
                          if type(taxes) != list:
                              taxes = [taxes]
                      else:
                          taxes = []
                      no_imp_tras = len(taxes)
                      if concept.get('Impuestos', {}).get('Retenciones', {}):
                          other_taxes = concept.get('Impuestos', {}).get('Retenciones', {}).get('Retencion')
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
                                  tax_amount = float(tax.get('@Importe', '0.00'))
                                  if tax.get('@TasaOCuota'):
                                      if k < no_imp_tras:
                                          amount_tasa = float(tax.get('@TasaOCuota')) * 100
                                      else:
                                          amount_tasa = float(tax.get('@TasaOCuota')) * -100
                                      tasa = str(amount_tasa)
                                  else:
                                      tasa = str(0)
                                  tax_exist = self.env['account.tax'].search(
                                              [('impuesto', '=', tax.get('@Impuesto')), ('type_tax_use', '=', 'sale'),
                                              ('tipo_factor', '=', tax.get('@TipoFactor')), ('amount', '=', tasa),
                                              ('company_id', '=', self.env.company.id)], limit=1)
                                  if not tax_exist:
                                      raise UserError("La factura contiene impuestos que no han sido configurados. Por favor configure primero los impuestos")
                                  if tax_exist.cash_basis_transition_account_id:
                                      cash_basis_account = tax_exist.cash_basis_transition_account_id

                                      lines.append(
                                          (0, 0, {
                                              'account_id': cash_basis_account.id,
                                              'name': f'{tax_exist.name}',
                                              'credit': tax_amount if float(amount_tasa) > 0 else 0.0,
                                              'debit': tax_amount if float(amount_tasa) < 0 else 0.0,
                                          })
                                      )
                                      if float(amount_tasa) > 0:
                                         total_credit += tax_amount
                                       #  _logger.info('float(amount_tasa) > 0 %s', float(amount_tasa))
                                       #  _logger.info('tax_amount %s', tax_amount)
                                       #  _logger.info('total_credit %s', total_credit)
                                      else:
                                         total_credit -= tax_amount
                                       #  _logger.info('float(amount_tasa) < 0 %s', float(amount_tasa))
                                       #  _logger.info('tax_amount %s', tax_amount)
                                       #  _logger.info('total_credit %s', total_credit)
                                  else:
                                      raise UserError( f"La factura contiene ({tax_exist.name}) impuestos que no se han configurado en una cuenta de transición de base de efectivo."
                                                       " Configure primero los impuestos")
                                  k = k + 1
                      total_credit += amount
                  if receivable_account:
                      lines.append((0, 0, {
                              'account_id': receivable_account.id,
                              'name': "Total Amount Entry",
                              'credit': 0.0,
                              'debit': total_credit,
                          }))
                  if lines:
                      journal_entry.write({'line_ids': lines})
                      # Post the journal entry
                      #journal_entry.action_post()
                     # return {
                     #     "effect": {
                     #         "type": "rainbow_man",
                     #         "message": _("¡Entrada de diario creada exitosamente...!")
                     #     }
                     # }

              except etree.XMLSyntaxError:
                  raise UserError(_('Invalid XML format. Please upload a valid XML file.'))
              except Exception as e:
                  raise UserError(_('Error processing XML file: %s') % str(e))
           if attachment.cfdi_type == 'SI':
              if not attachment or not attachment.datas:
                  raise UserError(_('No XML file uploaded.'))
              try:
                  # Decode the XML file data
                  file_coontent = base64.b64decode(attachment.datas)
                  file_coontent = file_coontent.replace(b'cfdi:', b'')
                  file_coontent = file_coontent.replace(b'tfd:', b'')
                  try:
                     data = json.dumps(xmltodict.parse(file_coontent))
                     data = json.loads(data)
                  except Exception as e:
                     data = {}
                     raise UserError(str(e))

                  data = CaselessDictionary(data)
                  data = convert_to_special_dict(data)

                  xml_file = base64.b64decode(attachment.datas)
                  # Parse the XML file
                  xml_tree = etree.fromstring(xml_file)
                  # Define namespaces used in the XML
                  namespaces = {'cfdi': 'http://www.sat.gob.mx/cfd/4'}
                  # Extract necessary data from XML
                  invoice_line_data = data.get('Comprobante', {}).get('Conceptos', {}).get('Concepto', [])
                  if type(invoice_line_data) != list:
                      invoice_line_data = [invoice_line_data]
                  receptor_rfc =  data.get('Comprobante', {}).get('Emisor', {}).get('@Rfc')
                  total_amount = float(data.get('Comprobante', {}).get('@Total'))
                  # Initialize debit and credit totals
                  total_debit = 0.0
                  total_credit = 0.0
                  lines = []

                  # serach for partner exist or not
                  receptor = self.env['res.partner'].search([('vat', '=', receptor_rfc)], limit=1)
                  if receptor:
                      receivable_account = receptor.property_account_payable_id
                  else:
                      raise UserError("No se encontró el socio. Configure primero el socio.")

                  # Create the journal entry
                  journal_entry = self.env['account.move'].create({
                      'journal_id': self.diario.id,
                      'date': attachment.date_cfdi, #fields.Date.context_today(self),
                      'ref': f'UUID: {attachment.name}',
                      'move_type': 'entry',
                      'line_ids': [],
                  })
                  _logger.info('UUID 02 SI %s', attachment.serie_folio)

                  # Create account lines for each Concepto
                  for concept in invoice_line_data:
                      label = concept.get('@Descripcion')
                      amount = float(concept.get('@Importe', '0.0'))
                      # Add line for each concepto
                      lines.append(
                          (0, 0, {
                               'account_id': self.cuenta_de_ingreso.id,
                               'name': label,
                               'credit': 0.0,
                               'debit': amount,
                           })
                      )

                      taxes = concept.get('Impuestos', {}).get('Traslados', {}).get('Traslado')
                      if taxes:
                          if type(taxes) != list:
                              taxes = [taxes]
                      else:
                          taxes = []
                      no_imp_tras = len(taxes)
                      if concept.get('Impuestos', {}).get('Retenciones', {}):
                          other_taxes = concept.get('Impuestos', {}).get('Retenciones', {}).get('Retencion')
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
                                  tax_amount = float(tax.get('@Importe', '0.00'))
                                  if tax.get('@TasaOCuota'):
                                      if k < no_imp_tras:
                                          amount_tasa = float(tax.get('@TasaOCuota')) * 100
                                      else:
                                          amount_tasa = float(tax.get('@TasaOCuota')) * -100
                                      tasa = str(amount_tasa)
                                  else:
                                      tasa = str(0)
                                  tax_exist = self.env['account.tax'].search(
                                              [('impuesto', '=', tax.get('@Impuesto')), ('type_tax_use', '=', 'purchase'),
                                              ('tipo_factor', '=', tax.get('@TipoFactor')), ('amount', '=', tasa),
                                              ('company_id', '=', self.env.company.id)], limit=1)
                                  if not tax_exist:
                                      raise UserError("La factura contiene impuestos que no han sido configurados. Por favor configure primero los impuestos")
                                  if tax_exist.cash_basis_transition_account_id:
                                      cash_basis_account = tax_exist.cash_basis_transition_account_id

                                      lines.append(
                                          (0, 0, {
                                              'account_id': cash_basis_account.id,
                                              'name': f'{tax_exist.name}',
                                              'credit': tax_amount if float(amount_tasa) < 0 else 0.0,
                                              'debit': tax_amount if float(amount_tasa) > 0 else 0.0,
                                          })
                                      )
                                      if float(amount_tasa) > 0:
                                         total_credit += tax_amount
                                        # _logger.info('float(amount_tasa) > 0 %s', float(amount_tasa))
                                        # _logger.info('tax_amount %s', tax_amount)
                                        # _logger.info('total_credita %s', total_credit)
                                      else:
                                         total_credit -= tax_amount
                                       #  _logger.info('float(amount_tasa) < 0 %s', float(amount_tasa))
                                       #  _logger.info('tax_amount %s', tax_amount)
                                       #  _logger.info('total_creditb %s', total_credit)
                                  else:
                                      raise UserError( f"La factura contiene ({tax_exist.name}) impuestos que no se han configurado en una cuenta de transición de base de efectivo."
                                                       " Configure primero los impuestos")
                                  k = k + 1
                      _logger.info('total_creditc %s', amount)
                      total_credit += amount
                  if receivable_account:
                      lines.append((0, 0, {
                              'account_id': receivable_account.id,
                              'name': "Total Amount Entry",
                              'credit': total_credit,
                              'debit': 0.0,
                          }))
                  if lines:
                      journal_entry.write({'line_ids': lines})
                      # Post the journal entry
                      #journal_entry.action_post()
                     # return {
                     #     "effect": {
                     #         "type": "rainbow_man",
                     #         "message": _("¡Entrada de diario creada exitosamente...!")
                     #     }
                     # }

              except etree.XMLSyntaxError:
                  raise UserError(_('Invalid XML format. Please upload a valid XML file.'))
              except Exception as e:
                  raise UserError(_('Error processing XML file: %s') % str(e))