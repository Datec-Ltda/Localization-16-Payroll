# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class Company(models.Model):
    _inherit = 'res.company'
    hide_fields_legislation = fields.Boolean(string='Ocultar', default=True, help='Ocultar campos que no son utilizados por la legislación actualmente')

