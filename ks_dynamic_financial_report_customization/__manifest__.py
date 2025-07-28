# -*- coding: utf-8 -*-
{
    'name': 'Reportes Contabilidad CFDI',

    'summary': 'Generación de Balanza de comprobación y Catálogo de cuentas',

    'description': """Generación de Balanza de comprobación y Catálogo de cuentas""",
    'author': 'IT Admin',
    'website': 'https://odoo.itadmin.com.mx/',
    'category': 'Accounting/Accounting',
    'version': '17.02',
    'license': 'OPL-1',
    'depends': ['base', 'ks_dynamic_financial_report'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_group_views.xml',
        'views/base_template.xml',
        "views/generar_xml_hirarchy.xml",
    ],
    'assets': {'web.assets_backend': [
        'ks_dynamic_financial_report_customization/static/src/xml/ks_dynamic_financial_report.xml',
        'ks_dynamic_financial_report_customization/static/src/js/ks_dynamic_financial_report.js',
    ]},

}
