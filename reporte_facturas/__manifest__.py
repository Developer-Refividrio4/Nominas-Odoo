# -*- coding: utf-8 -*-
##############################################################################
#                 @author IT Admin
#
##############################################################################

{
    'name': 'Reporte de Facturas',
    'version': '17.01',
    'description': ''' Reporte de facturas exportable a PDF o XLS
    ''',
    'category': 'Stock',
    'author': 'IT Admin',
    'website': 'http://www.itadmin.com.mx',
    'depends': [
        'base','stock', 'account', 'cdfi_invoice','report_xlsx',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/invoice_report_wizard.xml',
        'report/invoice_report.xml',
        'views/invoice_report_id.xml',
    ],
    'application': False,
    'installable': True,
}
