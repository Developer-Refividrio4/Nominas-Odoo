# -*- coding: utf-8 -*-
##############################################################################
#                 @author IT Admin
#
##############################################################################

{
    'name': 'Contabildad Electronica Mexico',
    "version": "17.05",
    'description': ''' Contabilidad Electronica para Mexico (CFDI 1.3)
    ''',
    'category': 'Accounting',
    'author': 'IT Admin',
    'website': 'www.itadmin.com.mx',
    'depends': [
        'base',
        'account',
        'report_xlsx',
        'cdfi_invoice',
        'ks_dynamic_financial_report_customization',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/menu.xml',
        'data/res_currency_data.xml',
        'data/catalogos.pais_diot.csv',
        'data/sequence_data.xml',
        'views/res_partner_view.xml',
        'views/res_currency_views.xml',
        'views/account_move.xml',
        'views/account_payment.xml',
        'views/iva_pedimentos.xml',
        'views/diot_cfdi.xml',
        "wizard/polizas_report_view.xml",
        "wizard/reporte_diot.xml",
        'wizard/actualizar_polizas_view.xml',
        'wizard/cierre_anual_view.xml',
        'wizard/folios_report_view.xml',
        'wizard/generar_xml_zip.xml',
    ],
    'assets': {
    },
    'application': False,
    'installable': True,
    'price': 0.00,
    'currency': 'USD',
    'license': 'AGPL-3',
}
