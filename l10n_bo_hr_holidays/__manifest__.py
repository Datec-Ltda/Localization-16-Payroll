{
    'name': "Datec: Nómina Bolivia ausencia",
    'version': '16.0.0.0.5',
    'depends': ['l10n_bo_hr_contract', 'hr_holidays'],
    'author': "Datec",
    'license': 'OPL-1',
    'category': 'Payroll Localization',
    'description': """
    Bolivia Payroll Localization
    """,
    'data': [
        'data/hr_work_entry_type.xml',
        'data/hr_holidays_data.xml',
        'data/hr_vacation_quota_table_data.xml',
        'data/hr_antiquity_bonus_table_data.xml',
        'security/ir.model.access.csv',
        'views/hr_employee_view.xml',
        'views/res_company_bo_config_view.xml',


    ],
    "development_status": "Beta",
    "application": True,
    "installable": True,
}
