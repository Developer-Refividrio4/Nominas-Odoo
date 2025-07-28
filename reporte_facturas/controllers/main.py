# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.main import serialize_exception
from odoo.http import content_disposition

from xlsxwriter.workbook import Workbook
import csv
#from io import StringIO
import time
from datetime import datetime
from io import BytesIO

    
class BinaryFacturas(http.Controller):

    @http.route('/web/binary/download_xls', type='http', auth="public")
    @serialize_exception
    def download_xls(self,invoice_report_id, **kw):
        invoice_report = request.env['xls.invoice.report'].sudo().browse(int(invoice_report_id))
        invoice_ids = invoice_report.invoice_ids.split('-')
        invoice_ids = [int(s) for s in invoice_ids]
        Model = request.env['account.move']
        #cr, uid, context = request.cr, request.uid, request.context
        invoices = Model.browse(invoice_ids)
        timestamp = int(time.mktime(datetime.now().timetuple()))   
        csvfile = open('%s%s.csv' % ('/tmp/invoices_', timestamp), 'w')
        fieldnames = ['Fecha', 'Nombre', 'RFC', 'Factura CFDI', 'Estado CFDI', 'Estado Odoo', 'Vendedor', 'Documento Origen', 'Folio', 'Forma de pago', 'Metodo de Pago', 'Tipo de comprobante', 'Contado','Credito', 'Costo de ventas', 'Utilidad', '% Utilidad', 'Subtotal', 'Impuestos', 'Total']
        writer = csv.DictWriter(csvfile, quoting=csv.QUOTE_NONE, fieldnames=fieldnames)
        writer.writeheader()

        for inv in invoices:
            if inv.forma_pago == '01':
                pago_sin_acento = 'Efectivo'	
            elif inv.forma_pago == '02':
                pago_sin_acento = 'Cheque nominativo'
            elif inv.forma_pago == '03':
                pago_sin_acento = 'Transferencia electronica de fondos'
            elif inv.forma_pago == '04':
                pago_sin_acento = 'Tarjeta de Credito'
            elif inv.forma_pago == '05':
                pago_sin_acento = 'Monedero electronico'
            elif inv.forma_pago == '06':
                pago_sin_acento = 'Dinero electronico'
            elif inv.forma_pago == '08':
                pago_sin_acento = 'Vales de despensa'
            elif inv.forma_pago == '28':
                pago_sin_acento = 'Tarjeta de debito'
            elif inv.forma_pago == '29':
                pago_sin_acento = 'Tarjeta de servicios'
            elif inv.forma_pago == '30':
                pago_sin_acento = 'Aplicacion de anticipos'
            elif inv.forma_pago == '99':
                pago_sin_acento = 'Por definir'
            else:
                pago_sin_acento = 'NA'
            
            costo_de_ventas = sum(line.product_id.standard_price * line.quantity for line in inv.invoice_line_ids)
            utilidad = inv.amount_untaxed - costo_de_ventas
            writer.writerow({'Fecha': inv.invoice_date, 
                            'Nombre': inv.partner_id.name.replace(',','').replace('"','') or '', #.encode('ascii', 'ignore') or '',
                            'RFC': inv.partner_id.vat and inv.partner_id.vat or '', #.encode('ascii', 'ignore') or '',
                            'Factura CFDI': inv.factura_cfdi and 'Si' or 'No', 
                            'Estado CFDI': inv.estado_factura,
                            'Estado Odoo': inv.state,
                            'Vendedor': inv.user_id.name and inv.user_id.name.replace(',','') or '', #.encode('ascii', 'ignore') or '',
                            'Documento Origen': inv.invoice_origin and inv.invoice_origin.replace(',',''),
                            'Folio': inv.name.replace('INV','').replace('/','') or '',
                            'Forma de pago': pago_sin_acento,
                            'Metodo de Pago': inv.methodo_pago,
                            'Tipo de comprobante': inv.tipo_comprobante,
                            'Contado' : inv.methodo_pago == 'PUE' and inv.amount_untaxed or 0,
                            'Credito' : inv.methodo_pago == 'PPD' and inv.amount_untaxed or 0,
                            'Costo de ventas' : round(costo_de_ventas,2),
                            'Utilidad' : round(utilidad,2),
                            '% Utilidad' : inv.amount_untaxed > 0 and round(utilidad / inv.amount_untaxed,2) or 0,
                            'Subtotal' : round(inv.amount_untaxed,2),
                            'Impuestos' : round(inv.amount_tax,2),
                            'Total' : round(inv.amount_total,2),
                            })
               
        csvfile.close()   
        output = BytesIO() #StringIO()
        workbook = Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet()
        bold = workbook.add_format({'bold': True, 'border':   1,})
        border = workbook.add_format({'border':   1,})
        with open('%s%s.csv' % ('/tmp/invoices_', timestamp), 'rt') as f:
            reader = csv.reader(f)
            for r, row in enumerate(reader):
                for c, col in enumerate(row):
                    #print (r, c, col)
                    if r == 0:
                        worksheet.write(r, c, col, bold)
                    else:
                        worksheet.write(r, c, col, border)
                        # worksheet.set_column(c, c, len(col),formater)
        workbook.close()
        output.seek(0)	 
        binary = output.read()
            
        #res = Model.to_xml(cr, uid, context=context)
        if not binary:
            #print 'no binary'
            return request.not_found()
        else:
            filename = '%s%s.xls' % ('invoices_', timestamp)
            return request.make_response(binary,
                               [('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                                ('Pragma', 'public'), 
                                ('Expires', '0'),
                                ('Cache-Control', 'must-revalidate, post-check=0, pre-check=0'),
                                ('Cache-Control', 'private'),
                                ('Content-Length', len(binary)),
                                ('Content-Transfer-Encoding', 'binary'),
                                ('Content-Disposition', content_disposition(filename))])
        
