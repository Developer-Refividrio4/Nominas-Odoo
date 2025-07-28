# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from lxml import etree
import base64


class GenerarGastoWizard(models.TransientModel):
    _name = 'generar.gasto.wizard'
    _description = 'Generar Gasto Wizard'

    product_id = fields.Many2one(
        comodel_name='product.product',
        string="Producto",
        check_company=True,
        required=True,
        #domain=[('can_be_expensed', '=', True)]
    )
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string="Empleado",
        required=True,
        check_company=True,
        #domain=[('filter_for_expense', '=', True)]
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string="Compañia",
        readonly=True,
        default=lambda self: self.env.company,
    )
    payment_mode = fields.Selection(
        selection=[
            ('own_account', "Empleado (reembolso)"),
            ('company_account', "Compañía")
        ],
        required=True,
        string="Pagado por",
        default='own_account'
    )

    def create_expense_entry(self):
        module = self.env['ir.module.module'].sudo().search([('name','=','hr_expense')])
        if module and not module.state == 'installed':
            raise UserError(_('Debe tener el módulo de Gastos instalado para utilizar esta función.'))

        # Retrieve the attachment from the context
        attachment = self.env['ir.attachment'].browse(self.env.context.get('active_id'))
        if not attachment or not attachment.datas:
            raise UserError(_('No XML file uploaded.'))
        try:
            # Decode the XML file data
            xml_file = base64.b64decode(attachment.datas)
            # Parse the XML file
            xml_tree = etree.fromstring(xml_file)
            namespaces = {'cfdi': 'http://www.sat.gob.mx/cfd/4'}
            # Extract necessary data from XML
            concepts = xml_tree.xpath('//cfdi:Conceptos/cfdi:Concepto', namespaces=namespaces)
            expense_lines = []

            # Create Expence for each Concepto
            for concept in concepts:
                total_credit = 0.0
                label = concept.get('Descripcion', 'No Description')
                amount = float(concept.get('Importe', '0.00'))
                expence_data = {
                    'name': label,
                    'employee_id': self.employee_id.id,
                    'product_id': self.product_id.id,
                    'payment_mode': self.payment_mode,
                    'quantity': 1,
                    'date': fields.Date.today()
                }
                tax_ids = []
                traslados = concept.xpath('//cfdi:Impuestos/cfdi:Traslados/cfdi:Traslado', namespaces=namespaces)
                for traslado in traslados:
                    if traslado.get('Base') == concept.get('Importe', '0.00'):
                        tax_amount = float(traslado.get('Importe', '0.00'))
                        # Find the appropriate tax and account
                        tax_exist = self.env['account.tax'].search(
                            [('impuesto', '=', traslado.get('Impuesto')), ('type_tax_use', '=', 'purchase'),
                             ('tipo_factor', '=', traslado.get('TipoFactor')),
                             ('amount', '=', float(traslado.get('TasaOCuota', '0')) * 100),
                             ('company_id', '=', self.env.company.id)], limit=1)
                        if not tax_exist:
                            raise UserError("La factura contiene impuestos que no han sido configurados."
                                            "Por favor configure los impuestos primero")
                        total_credit += tax_amount
                        tax_ids.append(tax_exist.id)
                retenciones = concept.xpath('//cfdi:Impuestos/cfdi:Retenciones/cfdi:Retencion', namespaces=namespaces)
                for retencion in retenciones:
                    if retencion.get('Base') == concept.get('Importe', '0.00'):
                        tax_amount = float(retencion.get('Importe', '0.00'))
                        # Find the appropriate tax and account
                        tax_exist = self.env['account.tax'].search(
                            [('impuesto', '=', retencion.get('Impuesto')), ('type_tax_use', '=', 'purchase'),
                             ('tipo_factor', '=', retencion.get('TipoFactor')),
                             ('amount', '=', float(retencion.get('TasaOCuota', '0')) * -100),
                             ('company_id', '=', self.env.company.id)], limit=1)
                        if not tax_exist:
                            raise UserError("La factura contiene impuestos que no han sido configurados."
                                            "Por favor configure los impuestos primero")
                        total_credit -= tax_amount
                        tax_ids.append(tax_exist.id)
                total_credit += amount
                expence_data['tax_ids'] = [(6, 0, tax_ids)]
                expence_data['total_amount_currency'] = total_credit
                expence_id = self.env['hr.expense'].create(expence_data)
                expense_lines.append(expence_id)

            # Create the expense sheet (hr.expense.sheet)
            if expense_lines:
                self.env['hr.expense.sheet'].create({
                    'name': expense_lines[0].name,
                    'employee_id': self.employee_id.id,
                    'expense_line_ids': [(6, 0, [line.id for line in expense_lines])]
                })
                return {
                    "effect": {
                        "type": "rainbow_man",
                        "message": _("¡Entrada de gasto creada exitosamente...!")
                    }
                }
        except etree.XMLSyntaxError:
            raise UserError(_('Invalid XML format. Please upload a valid XML file.'))
        except Exception as e:
            raise UserError(_('Error processing XML file: %s') % str(e))
