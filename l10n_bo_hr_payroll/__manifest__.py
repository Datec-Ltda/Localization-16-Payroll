{
    'name': "Datec: Nómina Bolivia nómina",
    'version': '16.0.0.0.2',
    'depends': ['hr_payroll', 'l10n_bo_hr', 'l10n_bo_hr_holidays', 'hr_bo_employee_lastnames'],
    'author': "Datec",
    'license': 'OPL-1',
    'category': 'Payroll Localization',
    'description': """
    Bolivia Payroll Localization
    """,
    'data': [
        'data/hr_salary_rule_parameter_data.xml',
        'data/hr_payroll_category_data.xml',
        'data/hr_payroll_structure_data.xml',
        'data/hr_salary_rule_month_data.xml',
        'data/hr_payslip_input_type.xml',
        'security/ir.model.access.csv',
        'views/hr_employee_view.xml',
        'views/hr_payroll_closing_table_view.xml',
        # 'report/hr_employee_payroll_report_views.xml',

    ],
    "development_status": "Beta",
    "application": True,
    "installable": True,
}
