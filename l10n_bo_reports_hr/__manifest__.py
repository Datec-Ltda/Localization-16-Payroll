# -*- coding: utf-8 -*-
{
    'name': "l10n_bo_reports_hr",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base','hr','l10n_bo_hr','l10n_bo_hr_holidays','l10n_bo_hr_payroll'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/res_company.xml',
        'views/finiquito.xml',
        'views/sso.xml',
        'views/reportes.xml',
        'views/reportes_menu.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
