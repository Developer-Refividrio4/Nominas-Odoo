# -*- coding: utf-8 -*-
##############################################################################
#                 @author IT Admin
#
##############################################################################

{
    'name': 'Punto de Venta Factura Electronica Mexico CFDI',
    'version': '17.04',
    'description': ''' Punto de Venta Factura Electronica Mexico.
    ''',
    'category': 'Sales, Point Of Sale, Accounting',
    'author': 'IT Admin',
    'website': '',
    'depends': [
        'point_of_sale', 'sale', 'account', 'cdfi_invoice'
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'reports/invoice_report.xml',
        'views/point_of_sale_view.xml',
        'views/factura_global_view.xml',
        'views/res_config_settings_view.xml',
        'wizard/create_invoice_wizard.xml',
        'wizard/create_invoice_total_wizard.xml',
        'wizard/create_invoice_session_wizard.xml',
        'wizard/import_xml_info.xml',
        'data/factura_global.xml',
        'data/ir_sequence_data.xml',
        'data/mail_template_data.xml',
        'data/cron.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos':[
            "custom_invoice/static/src/js/CDFIDetailPopupWidget.js",
            "custom_invoice/static/src/js/paymentscreen.js",
            "custom_invoice/static/src/js/models.js",
            "custom_invoice/static/src/js/partner_editor.js",
            'custom_invoice/static/src/xml/CDFIDetailPopupWidget.xml',
            'custom_invoice/static/src/xml/pos_order_receipt.xml',
            'custom_invoice/static/src/xml/regimen_fiscal.xml',
        ],
    },
    'application': False,
    'installable': True,
    'price': 0.00,
    'currency': 'USD',
    'license': 'OPL-1',
}
