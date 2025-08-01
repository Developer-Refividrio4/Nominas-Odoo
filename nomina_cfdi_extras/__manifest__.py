# -*- coding: utf-8 -*-

{
    'name': 'Nomina CFDI Extras',
    'summary': '',
    'description': '''
This new module will create 2 new models: incidencias and incapacidades, they will have a tree view and will be located on Employees view. For both create sequential numbers for each register. Will have only 2 states: draft and done.
    ''',
    'author': 'IT Admin',
    'version': '17.05',
    'category': 'Employees',
    'depends': [
        'web',
        'hr','nomina_cfdi',
        'report_xlsx', 'om_hr_payroll',
    ],
    'data': [
        'data/hr_data.xml',
        'data/ir_sequence_data.xml',
       # 'data/action_report_xls.xml',
        'security/ir.model.access.csv',
        'views/faltas_nomina_view.xml',
        'views/vacaciones_nomina_view.xml',
        'views/incapacidades_view.xml',
        'views/incidencias_view.xml',
        'views/retardos_view.xml',
        'views/res_config_settings_views.xml',
        'views/viaticos_nomina_view.xml',
        'wizard/crear_faltas_from_retardos.xml',
        'views/hr_payslip_view.xml',
        'security/security.xml',
        'views/hr_employee_view.xml',
        'views/hr_loan_view.xml',
        'views/ir_sequence_data.xml',
        'views/employee_loan_type_views.xml',
        'views/prima_dominical_view.xml',
       # 'edi/mail_template.xml',
       # 'edi/skip_installment_mail_template.xml',
        'views/pay_slip_view.xml',
        #'views/salary_structure.xml',
        'views/hr_contract_view.xml',
        'views/dias_feriados_view.xml',
        #'wizard/import_loan_views.xml',
        'wizard/import_logs_view.xml',
        'views/dev_skip_installment.xml',
        'report/report_paperformat.xml',
        'report/payslip_batches_report.xml',
        'views/employee_view.xml',
        'report/payslip_batches_pagos_report2.xml',
        'report/payslip_batches_pagos_report.xml',
        'report/payslip_batches_detail_report.xml',
        'report/listado_de_raya_report.xml',
        'wizard/wizard_reglas_salariales_view.xml',
        'wizard/calculo_isr_anual_view.xml',
        'wizard/listado_de_nomina_wizard_view.xml',
        'wizard/year_reparto_utilidades.xml',
        'report/calculo_isr_anual_report.xml',
        'wizard/importar_dias_wizard.xml',
        'report/reporte_isr_imss.xml',
        'report/reporte_de_control.xml',
        'report/report_payslip_nomina_x_3.xml',
        'wizard/altas_y_bajas_view.xml',
        'wizard/total_por_empleado_view.xml',
        'wizard/total_por_departamento_view.xml',
        'views/credito_infonavit_view.xml',
        'report/reporte_caja_ahorro.xml',
        'wizard/wizard_caja_ahorro_view.xml',
        'wizard/reporte_nominas.xml',
        'wizard/reporte_imss.xml',
        'wizard/wizard_isn.xml',
        'views/hr_leave_type.xml',
        'wizard/nomina_liquidaciones_view.xml',
        'report/liquidaciones_report.xml',
    ],
    'assets': {
        'web.assets_backend': [
#            'nomina_cfdi_extras/static/src/js/list_button.js',
#            'nomina_cfdi_extras/static/src/xml/list_buttons.xml',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
}
