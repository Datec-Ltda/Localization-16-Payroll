# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class Partner(models.Model):
    _inherit = 'res.partner'

    l10n_bo_afp = fields.Boolean('Administradora de fondo de pensiones', default=False)
    l10n_bo_afp_code = fields.Char(string="Código")
    l10n_bo_health_box = fields.Boolean('Seguro de la caja de salud', default=False)
    l10n_bo_health_box_code = fields.Char(string="Código")
    l10n_bo_document_city_id = fields.Many2one(
        comodel_name='res.country.state',
        string='Ciudad de expedición',
        domain="[('country_id', '=', country_id)]"
    )
    l10n_bo_document_type = fields.Selection([
        ("nit", "NIT"),
        ("ci", "CI"),
        ("passport", "Pasaporte"),
        ("foreign_id", "ID Extranjero"),
        ("others", "Otros")
    ], string="Tipo de documento de identidad", default="nit")
    