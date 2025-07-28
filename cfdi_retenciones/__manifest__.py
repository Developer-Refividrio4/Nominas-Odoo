# -*- coding: utf-8 -*-
##############################################################################
#                 @author IT Admin
#
##############################################################################

{
    'name': 'CFDI Retenciones',
    'version': '17.01',
    'description': ''' Agrega campos para generar CFDI de Retenciones e Información de Pagos
    ''',
    'category': 'Accounting',
    'author': 'IT Admin',
    'website': 'www.itadmin.com.mx',
    'depends': [
        'account', 'cdfi_invoice',
    ],
    'data': [
        'security/ir.model.access.csv',
        'reports/invoice_report.xml',
        'views/factura_retencion_view.xml',
        'data/ir_sequence_data.xml',
        'data/mail_template_data.xml',
	],
    'application': False,
    'installable': True,
}
