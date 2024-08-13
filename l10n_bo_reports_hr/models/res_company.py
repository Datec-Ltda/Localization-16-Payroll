from odoo import models, fields


class Company(models.Model):
    _inherit = "res.company"

    url_report_service = fields.Char("URL del servicio")