# -*- coding: utf-8 -*-
###################################################################################

###################################################################################
{
    'name': 'Open Datec Advance Salary',
    'version': '16.0.1.0.0',
    'summary': 'Advance Salary In HR',
    'description': """
        Le ayuda a gestionar las solicitudes de adelantos de salario del personal de su empresa.
        """,
    'category': 'Línea base Bolivia/Human Resources/Payroll',
    'live_test_url': '',
    'author': "Datec",
    'company': 'Datec',
    'maintainer': 'Datec',
    'website': "",
    'depends': [
        'l10n_bo_hr_payroll', 'hr', 'account', 'hr_contract', 'l10n_bo_loan',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/salary_structure.xml',
        'views/salary_advance.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}

