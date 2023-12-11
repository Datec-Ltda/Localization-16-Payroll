# -*- coding: utf-8 -*-
###################################################################################

###################################################################################
{
    'name': 'Open Datec Loan Management',
    'version': '16.0.1.0.0',
    'summary': 'Manage Loan Requests',
    'description': """
        Le ayuda a gestionar las solicitudes de préstamo del personal de su empresa.
        """,
    'category': 'Línea base Bolivia/Human Resources/Payroll',
    'author': "Datec",
    'company': 'Datec',
    'maintainer': 'Datec',
    'live_test_url': '',
    'website': "",
    'depends': [
        'base', 'l10n_bo_hr_payroll', 'hr', 'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/hr_loan_seq.xml',
        'data/salary_rule_loan.xml',
        'views/hr_loan.xml',
        'views/hr_payroll.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
