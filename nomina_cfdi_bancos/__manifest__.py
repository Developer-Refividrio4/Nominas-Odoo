# -*- coding: utf-8 -*-
{
    "name": "Nomina CFDI bancos",
    "author": "IT Admin",
    "version": "17.01",
    "category": "Other",
    "description":"Genera dispersion de bancos para la nómina.",
    "depends": ["nomina_cfdi",'om_hr_payroll','hr'],
    "data": [
        'security/ir.model.access.csv',
        "wizard/generar_pagos_banco.xml",
        "views/hr_employee_view.xml",
    ],
    "license": 'AGPL-3',
    'installable': True,
    'images': [''],
}
