# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from datetime import date
from datetime import datetime, timedelta
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

    @api.depends('contract_ids.date_start')
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

    @api.depends('contract_ids.date_start')
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

    @api.depends('contract_ids.date_start')
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

    @api.depends('contract_ids.date_start')
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

    def _create_contract_date_arrangement(self, contract):
        contract_dates_updated = []
        date_hired = contract.date_start
        while date_hired + relativedelta(years=1) <= fields.Date.today():
            date_hired += relativedelta(years=1)
            contract_dates_updated.append(date_hired)
        return contract_dates_updated

    def compute_years_until_date(self, contract, date_end):
        date_hired = contract.employee_id.date_hired
        current_date = date_end
        delta_years = relativedelta(current_date, date_hired).years
        years_of_service = delta_years
        domain = [('years_of_service_start', '<=', years_of_service),
                  ('years_of_service_end', '>=', years_of_service)]
        register = self.env['hr.vacation.quota.table'].search(domain, limit=1)
        allowed_vacation_days = 0
        if register:
            allowed_vacation_days = register.vacation_days
        return allowed_vacation_days

    def manage_vacation_assignment_requests(self):
        date_today = fields.Date.from_string(fields.Date.today())
        contracts = self.env['hr.contract'].search([
            ('state', '=', 'open'),
            '|',
            ('date_end', '=', False),
            ('date_end', '=', None),
        ])
        for contract in contracts:
            dates_update = self._create_contract_date_arrangement(contract)
            for date_init in dates_update:
                days_allocation = self.compute_years_until_date(contract, date_init)
                if days_allocation > 0:
                    value = {
                        'allocation_type': 'regular',
                        'can_approve': True,
                        'can_reset': True,
                        'create_uid': 1,
                        'date_from': date_init,
                        'date_to': False,
                        'display_name': 'Asignación de Vacaciones ' + str(days_allocation) + ' días de ' + contract.employee_id.name,
                        'duration_display': 15,
                        'employee_company_id': contract.company_id.id,
                        'employee_id': contract.employee_id.id,
                        # 'employee_ids': contract.employee_id,
                        'employee_overtime':  0.0,
                        'holiday_status_id': 1,
                        'holiday_type': 'employee',
                        'hr_attendance_overtime': True,
                        'max_leaves': days_allocation,
                        'number_of_days':  days_allocation,
                        'number_of_days_display': days_allocation,
                        'number_of_hours_display': days_allocation * 8,
                        'private_name': 'vacaciones',
                        'state': 'confirm',
                        'type_request_unit':'day',
                        'validation_type': 'officer',
                    }
                    leave_allocation = self.env['hr.leave.allocation']
                    leave_allocation_element = leave_allocation.search([('holiday_status_id', '=', 1),
                                                                      ('employee_id', '=', contract.employee_id.id),
                                                                      ('date_from', '=', date_init)])
                    if not leave_allocation_element:
                        move = leave_allocation.sudo().create(value)
                        # current_employee = self.env.user.employee_id
                        # move.write({
                        #     'state': 'validate',
                        #     'approver_id': current_employee.id
                        # })

