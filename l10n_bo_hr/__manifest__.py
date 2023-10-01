{
    'name': "Datec: Nómina Bolivia",
    'version': '16.0.0.0.0',
    'depends': ['hr_bo_employee_lastnames'],
    'author': "Datec",
    'license': 'OPL-1',
    'category': 'Payroll Localization',
    'description': """
    Bolivia Payroll Localization
    """,
    "depends": ["mail"],
    'data': [
        # 'data/',
        'security/ir.model.access.csv',
        'views/hr_job_views.xml',
        'views/hr_employee_view.xml',
        'wizard/hr_departure_wizard_views.xml',
        'views/hr_payroll_area_view.xml',
        'views/hr_personnel_area_view.xml',
        'views/hr_personnel_group_view.xml',
        'views/hr_staff_division_view.xml',
        'views/hr_staffing_subdivision_view.xml',
        # 'report/hr_employee_payroll_report_views.xml',

    ],
}
