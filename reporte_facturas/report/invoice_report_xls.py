# -*- coding: utf-8 -*-

import xlsxwriter
from odoo import models

class InvoiceReportXls(models.AbstractModel):
    _name = 'report.reporte_facturas.invoice_xlsx'
    _inherit = 'report.report_xlsx.abstract'


    def get_lines(self, obj):
        lines = []
        #customer = obj.customer_id
        domain = [
            ('invoice_date', '>=', obj.date_from),
            ('invoice_date', '<=', obj.date_to),
            ('move_type', '=', 'out_invoice'),
            ('state', '!=', 'draft'),
        ]
        #if customer:
        #    domain.append(('partner_id', '=', customer.id))
        
        invoice_ids = self.env['account.move'].search(domain)

        for value in invoice_ids:

            if value.state == 'posted':
                estado = 'Publicado'
            else:
                estado = 'NA'

            if value.forma_pago_id and value.forma_pago_id.code == '01':
                pago_sin_acento = 'Efectivo'    
            elif value.forma_pago_id and value.forma_pago_id.code == '02':
                pago_sin_acento = 'Cheque nominativo'
            elif value.forma_pago_id and value.forma_pago_id.code == '03':
                pago_sin_acento = 'Transferencia electronica de fondos'
            elif value.forma_pago_id and value.forma_pago_id.code == '04':
                pago_sin_acento = 'Tarjeta de Credito'
            elif value.forma_pago_id and value.forma_pago_id.code == '05':
                pago_sin_acento = 'Monedero electronico'
            elif value.forma_pago_id and value.forma_pago_id.code == '06':
                pago_sin_acento = 'Dinero electronico'
            elif value.forma_pago_id and value.forma_pago_id.code == '08':
                pago_sin_acento = 'Vales de despensa'
            elif value.forma_pago_id and value.forma_pago_id.code == '28':
                pago_sin_acento = 'Tarjeta de debito'
            elif value.forma_pago_id and value.forma_pago_id.code == '29':
                pago_sin_acento = 'Tarjeta de servicios'
            elif value.forma_pago_id and value.forma_pago_id.code == '30':
                pago_sin_acento = 'Aplicacion de anticipos'
            elif value.forma_pago_id and value.forma_pago_id.code == '99':
                pago_sin_acento = 'Por definir'
            else:
                pago_sin_acento = 'NA'

            vals = {
                'date': value.invoice_date.strftime("%d/%m/%Y") or '',
                'name': value.display_name,
                'rfc': value.partner_id.vat,
                'factura_cfdi': value.factura_cfdi and 'Si' or 'No',
                'estado_factura': estado,
                'vendedor': value.user_id.name,
                #'origen': value.origin,
                'folio': value.number_folio,
                'pago': value.methodo_pago,
                'forma_pago': pago_sin_acento,
                'contado': value.methodo_pago == 'PUE' and value.amount_untaxed or 0,
                'credito': value.methodo_pago == 'PPD' and value.amount_untaxed or 0,
                'costo_de_ventas': sum(line.product_id.standard_price * line.quantity for line in value.invoice_line_ids),
                'utilidad': value.amount_untaxed,
                'subtotal': value.amount_untaxed,
                'impuestos': value.amount_tax,
                'amount': value.amount_total,
            }
            lines.append(vals)
        return lines


    def generate_xlsx_report(self, workbook, data, wizard_obj):
        for obj in wizard_obj:
            lines = self.get_lines(obj)
            worksheet = workbook.add_worksheet('Reporte de facturas')
            bold = workbook.add_format({'bold': True, 'align': 'center'})
            text = workbook.add_format({'font_size': 12, 'align': 'center'})
           
            worksheet.set_column(0, 0, 25)
            worksheet.set_column(1, 2, 25)
            worksheet.set_column(3, 3, 25)
            worksheet.set_column(4, 4, 25)
            worksheet.set_column(5, 5, 25)
            worksheet.set_column(6, 6, 25)
            worksheet.set_column(7, 7, 25)
            worksheet.set_column(8, 8, 25)
            worksheet.set_column(9, 9, 25)
            worksheet.set_column(10, 10, 25)
            worksheet.set_column(11, 11, 25)
            worksheet.set_column(12, 12, 25)
            worksheet.set_column(13, 13, 25)
            worksheet.set_column(14, 14, 25)
            worksheet.set_column(15, 15, 25)
            #worksheet.set_column(16, 16, 25)

            worksheet.write('A1', 'Fecha', bold)
            worksheet.write('B1', 'Nombre', bold)
            worksheet.write('C1', 'RFC', bold)
            worksheet.write('D1', 'Factura CFDI', bold)
            worksheet.write('E1', 'Estado Odoo', bold)
            worksheet.write('F1', 'Vendedor', bold)
            #worksheet.write('G1', 'Documento Origen', bold)
            worksheet.write('G1', 'Folio', bold)
            worksheet.write('H1', 'Método de pago', bold)
            worksheet.write('I1', 'Tipo de comprobante', bold)
            worksheet.write('J1', 'Contado', bold)
            worksheet.write('K1', 'Crédito', bold)
            worksheet.write('L1', 'Costo de ventas', bold)
            worksheet.write('M1', '% Utilidad', bold)
            worksheet.write('N1', 'Subtotal', bold)
            worksheet.write('O1', 'Impuestos', bold)
            worksheet.write('P1', 'Total', bold)
            row = 1
            col = 0
            for res in lines:
                worksheet.write(row, col, res['date'], text)
                worksheet.write(row, col + 1, res['name'], text)
                worksheet.write(row, col + 2, res['rfc'], text)
                worksheet.write(row, col + 3, res['factura_cfdi'], text)
                worksheet.write(row, col + 4, res['estado_factura'], text)
                worksheet.write(row, col + 5, res['vendedor'], text)
                #worksheet.write(row, col + 6, res['origen'], text)
                worksheet.write(row, col + 6, res['folio'], text)
                worksheet.write(row, col + 7, res['pago'], text)
                worksheet.write(row, col + 8, res['forma_pago'], text)
                worksheet.write(row, col + 9, str(self.env.user.company_id.currency_id.symbol) + str(res['contado']), text)
                worksheet.write(row, col + 10, str(self.env.user.company_id.currency_id.symbol) + str(res['credito']), text)
                worksheet.write(row, col + 11, str(self.env.user.company_id.currency_id.symbol) + str(res['costo_de_ventas']), text)
                worksheet.write(row, col + 12, str(self.env.user.company_id.currency_id.symbol) + str((res['utilidad'] - res['costo_de_ventas'])), text)
                worksheet.write(row, col + 13, str(self.env.user.company_id.currency_id.symbol) + str(res['subtotal']), text)
                worksheet.write(row, col + 14, str(self.env.user.company_id.currency_id.symbol) + str(res['impuestos']), text)
                worksheet.write(row, col + 15, str(self.env.user.company_id.currency_id.symbol) + str(res['amount']), text)
                row = row + 1
