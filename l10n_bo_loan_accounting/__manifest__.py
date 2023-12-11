# -*- coding: utf-8 -*-
###################################################################################

###################################################################################
{
    'name': 'Open Datec Loan Accounting',
    'version': '16.0.1.0.0',
    'summary': 'Open Datec Loan Accounting',
    'description': """
        Create accounting entries for loan requests.
        """,
    'category': 'Línea base Bolivia/Human Resources/Payroll',
    'author': "Datec",
    'company': 'Datec',
    'maintainer': 'Datec',
    'live_test_url': '',
    'website': "",
    'depends': [
        'base', 'l10n_bo_hr_payroll', 'hr', 'account', 'l10n_bo_loan',
    ],
    'data': [
        'views/hr_loan_config.xml',
        'views/hr_loan_acc.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
