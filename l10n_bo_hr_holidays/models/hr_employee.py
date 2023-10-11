# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from datetime import date
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    years_of_service = fields.Integer(string="Años de antigüedad", compute='_compute_years_of_service', store=True)
    allowed_vacation_days = fields.Integer(string="Días de vacaciones permitidos", readonly=True, compute='_compute_allowed_vacation_days', store=True)

    @api.depends('contract_ids.date_start')
    def _compute_years_of_service(self):
        for record in self:
            if record.contract_ids:
                date_hired = min(record.contract_ids.mapped('date_start'))
                current_date = fields.Date.today()
                delta_years = relativedelta(current_date, date_hired).years
                record.years_of_service = delta_years
            else:
                record.years_of_service = 0

    @api.depends('years_of_service')
    def _compute_allowed_vacation_days(self):
        for rec in self:
            allowed_vacation_days = 0
            if rec.years_of_service:
                domain = [('years_of_service_start', '<=', rec.years_of_service), ('years_of_service_end', '>=', rec.years_of_service)]
                register = self.env['hr.vacation.quota.table'].search(domain, limit=1)
                if register:
                    allowed_vacation_days = register.vacation_days
                rec.allowed_vacation_days = allowed_vacation_days
