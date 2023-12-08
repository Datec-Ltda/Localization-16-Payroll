# -*- coding: utf-8 -*-
{
    'name': "Datec: Bolivia web",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",
    'description': """
        Modificacion con respecto a todo lo que tiene que ver con los usuarios
    """,
    'license': 'OPL-1',
    'author': "Datec",
    'category': 'Línea base Bolivia/Sitio Web',
    'version': '0.1.0.0.0.3',
    'depends': ['base'],
    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        # 'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    "development_status": "Beta",
    "application": True,
    "installable": True,
}
