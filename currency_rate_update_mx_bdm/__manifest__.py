{
    'name': 'Tipo de cambio Banxico',
    'version': '17.01',
    'category': '',
    'summary': 'Agrega Banco de México como fuente para actualizar moneda',
    'author': 'IT Admin',
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'depends': [
        'currency_rate_update',
    ],
    'data': [
        "views/res_currency_rate_provider.xml",
     ],
}
