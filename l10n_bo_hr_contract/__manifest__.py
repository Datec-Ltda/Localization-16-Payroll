{
    'name': "Datec: Nómina Bolivia contrato",
    'version': '16.0.0.0.5',
    'depends': ['l10n_bo_hr', 'hr_contract'],
    'author': "Datec",
    'license': 'OPL-1',
    'category': 'Línea base Bolivia/Human Resources/Contracts',
    'description': """
    Bolivia Payroll Localization
    """,
    'data': [
        'data/hr_contract_reason_measurement.xml',
        'security/ir.model.access.csv',
        'views/contract_view.xml',
        'views/contract_reason_measurement_view.xml',
        'views/bi_organizational_structure_reports_view.xml',
        # 'report/hr_employee_payroll_report_views.xml',

    ],
    "development_status": "Beta",
    "application": True,
    "installable": True,
}
