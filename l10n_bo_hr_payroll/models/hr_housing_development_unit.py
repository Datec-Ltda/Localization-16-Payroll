# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from random import randint

from odoo import fields, models


class HrPayrollHousingDevelopmentUnit(models.Model):

    _name = "hr.payroll.housing.development.unit"
    _description = "Unidad de Fomento de Vivienda"

    date_month = fields.Date(string="Fecha", index=True, required=True)
    ufv_value = fields.Float(string="Valor UFV", required=True)


