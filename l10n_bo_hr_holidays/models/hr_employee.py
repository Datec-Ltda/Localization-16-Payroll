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
    allowed_vacation_days = fields.Integer(string="Días de vacaciones permitidos anual", readonly=True, compute='_compute_allowed_vacation_days', store=True)
    date_hired = fields.Date(string='Fecha Contratación', help="Fecha de inicio del primer contrato", compute='_compute_date_hired', store=True)
    accumulated_leave_year = fields.Integer(string="Días de vacaciones",
                                            readonly=True, compute='_compute_accumulated_leave_year')
    remaining_leave_year = fields.Integer(string="Quedan", readonly=True, compute='_compute_accumulated_leave_year')
    accumulated_leave_month = fields.Integer(string="acumulados mensual",
                                             readonly=True, compute='_compute_accumulated_leave_month')
    accumulated_leave_day = fields.Float(string="acumulados dias",
                                           readonly=True, compute='_compute_accumulated_leave_day')
    total_vacation_day = fields.Float(string="Total de vacaciones",
                                           readonly=True, compute='_compute_total_vacation_day')

    @api.depends('contract_ids.date_start')
    def _compute_date_hired(self):
        for record in self:
            if record.contract_ids:
                date_hired = min(record.contract_ids.mapped('date_start'))
                record.date_hired = date_hired
            else:
                record.date_hired = 0

    def _compute_accumulated_leave_year(self):
        for record in self:
            allocations = self.env['hr.leave.allocation'].search([
                ('employee_id', 'in', self.ids),
                ('state', 'in', ['validate']),
                ('holiday_status_id', '=', 1),
            ])
            for allocation in allocations:
                self.accumulated_leave_year += allocation.number_of_days

            self.remaining_leave_year = self.accumulated_leave_year

            leaves = self.env['hr.leave'].search([
                ('employee_id', 'in', self.ids),
                ('state', 'in', ['validate', 'validate1']),
                ('holiday_status_id', '=', 1)])

            for leave in leaves:
                self.remaining_leave_year -= leave.number_of_days

    def _compute_accumulated_leave_month(self):
        for record in self:
            if record.date_hired:
                date_hired_this_year = date(date.today().year, record.date_hired.month, record.date_hired.day)
                db_today = datetime.now().date()
                diff = relativedelta(db_today, date_hired_this_year)
                diff_months = diff.months
                per_month = self.allowed_vacation_days/12
                record.accumulated_leave_month = diff_months * per_month
            else:
                record.accumulated_leave_month = 0

    def _compute_accumulated_leave_day(self):
        for record in self:
            if record.date_hired:
                date_hired_this_year = date(date.today().year, record.date_hired.month, record.date_hired.day)
                db_today = datetime.now().date()
                diff = relativedelta(db_today, date_hired_this_year)
                diff_days = diff.days
                per_day = self.allowed_vacation_days/30
                record.accumulated_leave_day = diff_days * per_day

            else:
                record.accumulated_leave_day = 0

    def _compute_total_vacation_day(self):
        for record in self:
            record.total_vacation_day = record.remaining_leave_year + \
                                        record.accumulated_leave_month + \
                                        record.accumulated_leave_day


    @api.depends('contract_ids.date_start')
    def _compute_years_of_service(self):
        for record in self:
            if record.contract_ids:
                date_hired = record.date_hired
                # date_hired = min(record.contract_ids.mapped('date_start'))
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
