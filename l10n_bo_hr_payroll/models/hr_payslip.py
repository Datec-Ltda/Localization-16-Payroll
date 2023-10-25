# -*- coding:utf-8 -*-

from odoo import api, fields, models, tools, _
from datetime import date
import calendar
from datetime import datetime
from dateutil.relativedelta import relativedelta

# This will generate 16th of days
ROUNDING_FACTOR = 16


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def _get_base_local_dict(self):
        res = super()._get_base_local_dict()
        res.update({
            'leave_antiquity_bonus': leave_antiquity_bonus,
            'credit_balance_previous_month': credit_balance_previous_month,
            'amount_total_gained_average': amount_total_gained_average,
            'days_total_worked': days_total_worked,
            'special_round': special_round,
            'total_average_earned': total_average_earned,
        })
        return res

    def _get_antiquity_bonus(self, employee):
        percent = 0
        years_of_service = employee.years_of_service
        domain = [('years_of_antiquity_bonus_start', '<', years_of_service)]
        leave_antiquity = self.env['hr.antiquity.bonus.table'].search(domain, limit=1, order="years_of_antiquity_bonus_start desc")
        if leave_antiquity:
            percent = leave_antiquity.percentage
        return percent

    def get_day_month_past(self, date_now):
        month_past = date_now.month - 1  # Obtener el mes anterior
        # Manejar el caso especial de enero, donde el mes anterior es diciembre del año anterior
        if month_past == 0:
            month_past = 12
            year_past = date_now.year - 1
        else:
            year_past = date_now.year
        _, last_day_now = calendar.monthrange(date_now.year, date_now.month)
        if last_day_now == date_now.day:
            _, day_past_moth = calendar.monthrange(year_past, month_past)
        else:
            day_past_moth = date_now.day

        # Crear una nueva fecha con el mismo día que la fecha original pero en el mes y año anterior
        date_past = date(year_past, month_past, day_past_moth)
        return date_past

    def _get_credit_balance_previous_month(self, employee):
        credit = 0
        date_from = self.get_day_month_past(self.date_from)
        date_to = self.get_day_month_past(self.date_to)

        domain = [('date_from', '=', date_from),
                  ('date_to', '=', date_to),
                  ('employee_id', '=', employee.id)]
        closing_table = self.env['hr.payroll.closing.table'].search(domain, limit=1)
        if closing_table:
            credit = closing_table.credit_next_month
        return credit

    def _get_amount_total_gained(self, employee,  date_start_cal, date_to_ca, ruler):
        amount = 0
        domain = [('date_from', '>=', date_start_cal),
                  ('date_to', '<=', date_to_ca),
                  ('employee_id', '=', employee.id)]
        closing_table = self.env['hr.payroll.closing.table'].search(domain)
        for record in closing_table:
            if ruler == 'BASIC':
                amount += record.basic
            if ruler == 'BONO_ANT':
                amount += record.antiquity_bonus
            if ruler == 'BONO_PROD':
                amount += record.production_bonus
            if ruler == 'SUBS_FRONTERA':
                amount += record.frontier_subsidy
            if ruler == 'EXTRAS':
                amount += record.overtime_amount
            if ruler == 'DOMINGO':
                amount += record.sunday_overtime_amount
            if ruler == 'RECARGO':
                amount += record.night_overtime_hours_amount
            if ruler == 'NET':
                amount += record.net_salary

        return amount

    def _get_total_average_earned(self, date_to, employee, ruler, months):
        domain = [('date_to', '<=', date_to), ('employee_id', '=', employee.id)]
        closing_table = self.env['hr.payroll.closing.table'].search(domain, order='date_to desc', limit=months)
        if not closing_table:
            return 0
        else:
            amount = 0
            for record in closing_table:
                if ruler == 'BASIC':
                    amount += record.basic
                if ruler == 'BONO_ANT':
                    amount += record.antiquity_bonus
                if ruler == 'BONO_PROD':
                    amount += record.production_bonus
                if ruler == 'SUBS_FRONTERA':
                    amount += record.frontier_subsidy
                if ruler == 'EXTRAS':
                    amount += record.overtime_amount
                if ruler == 'DOMINGO':
                    amount += record.sunday_overtime_amount
                if ruler == 'RECARGO':
                    amount += record.night_overtime_hours_amount
                if ruler == 'NET':
                    amount += record.net_salary
        return amount/months

    def _get_worked_day_lines_values(self, domain=None):
        self.ensure_one()
        res = []
        if self.struct_id.country_id.code != 'CO':
            super()._get_worked_day_lines_values(domain=domain)

        hours_per_day = self._get_worked_day_lines_hours_per_day()
        date_from = datetime.combine(self.date_from, datetime.min.time())
        date_to = datetime.combine(self.date_to, datetime.max.time())
        work_hours = self.contract_id._get_work_hours(date_from, date_to, domain=domain)
        work_hours_ordered = sorted(work_hours.items(), key=lambda x: x[1])
        biggest_work = work_hours_ordered[-1][0] if work_hours_ordered else 0
        add_days_rounding = 0
        overtime_hours = self.env['hr.payroll.overtime.hours.list'].search([('employee_id', '=', self.employee_id.id),
                                                                    ('contract_id', '=', self.contract_id.id),
                                                                    ('date_from', '>=', self.date_from),
                                                                    ('date_to', '<=', self.date_to),
                                                                    ('state', '=', 'open')], limit=1)
        for work_entry_type_id, hours in work_hours_ordered:
            work_entry_type = self.env['hr.work.entry.type'].browse(work_entry_type_id)
            if work_entry_type.code == 'WORK100':
                we_type = self.env.ref('hr_work_entry.work_entry_type_attendance')
                valor = 30
                attendance_line = {
                    'sequence': we_type.sequence,
                    'work_entry_type_id': we_type.id,
                    'number_of_days': valor,
                    'number_of_hours': valor * hours_per_day,
                }
                res.append(attendance_line)
            else:
                work_entry_type = self.env['hr.work.entry.type'].browse(work_entry_type_id)
                days = round(hours / hours_per_day, 5) if hours_per_day else 0
                if work_entry_type_id == biggest_work:
                    days += add_days_rounding
                day_rounded = self._round_days(work_entry_type, days)
                add_days_rounding += (days - day_rounded)
                attendance_line = {
                    'sequence': work_entry_type.sequence,
                    'work_entry_type_id': work_entry_type_id,
                    'number_of_days': day_rounded,
                    'number_of_hours': hours,
                }
                res.append(attendance_line)

        # obtener el tiempo de trabajo horas extras

        if overtime_hours:
            # overtime
            we_type = self.env.ref('l10n_bo_hr_payroll.hr_work_entry_type_overtime')
            if overtime_hours.overtime != 0:
                res.append({
                    'sequence': we_type.sequence,
                    'work_entry_type_id': we_type.id,
                    'number_of_days': overtime_hours.overtime / hours_per_day,
                    'number_of_hours': overtime_hours.overtime,
                })
            # hours_night_overtime
            we_type = self.env.ref('l10n_bo_hr_payroll.hr_work_entry_type_hours_night_overtime')
            if overtime_hours.hours_night_overtime != 0:
                res.append({
                    'sequence': we_type.sequence,
                    'work_entry_type_id': we_type.id,
                    'number_of_days': overtime_hours.hours_night_overtime / hours_per_day,
                    'number_of_hours': overtime_hours.hours_night_overtime,
                    'amount': 0,
                })
            # sunday_overtime
            we_type = self.env.ref('l10n_bo_hr_payroll.hr_work_entry_type_sunday_overtime')
            if overtime_hours.sunday_overtime != 0:
                res.append({
                    'sequence': we_type.sequence,
                    'work_entry_type_id': we_type.id,
                    'number_of_days': overtime_hours.sunday_overtime / hours_per_day,
                    'number_of_hours': overtime_hours.sunday_overtime,
                })
            # sunday_worked
            we_type = self.env.ref('l10n_bo_hr_payroll.hr_work_entry_type_sunday_worked')
            if overtime_hours.sunday_worked != 0:
                res.append({
                    'sequence': we_type.sequence,
                    'work_entry_type_id': we_type.id,
                    'number_of_days': overtime_hours.sunday_worked / hours_per_day,
                    'number_of_hours': overtime_hours.sunday_worked,
                })

        return res

    def _get_worked_day_lines(self, domain=None, check_out_of_contract=True):
        """
        :returns: a list of dict containing the worked days values that should be applied for the given payslip
        """
        res = []
        # fill only if the contract as a working schedule linked
        self.ensure_one()
        contract = self.contract_id
        if contract.resource_calendar_id:
            res = self._get_worked_day_lines_values(domain=domain)
            if not check_out_of_contract:
                return res

            # If the contract doesn't cover the whole month, create
            # worked_days lines to adapt the wage accordingly
            out_days, out_hours = 0, 0
            reference_calendar = self._get_out_of_contract_calendar()
            if self.date_from < contract.date_start:
                start = fields.Datetime.to_datetime(self.date_from)
                stop = fields.Datetime.to_datetime(contract.date_start) + relativedelta(days=-1, hour=23, minute=59)
                out_time = reference_calendar.get_work_duration_data(start, stop, compute_leaves=False,
                                                                     domain=['|', ('work_entry_type_id', '=', False), (
                                                                     'work_entry_type_id.is_leave', '=', False)])
                out_days += out_time['days']
                out_hours += out_time['hours']
            if contract.date_end and contract.date_end < self.date_to:
                start = fields.Datetime.to_datetime(contract.date_end) + relativedelta(days=1)
                stop = fields.Datetime.to_datetime(self.date_to) + relativedelta(hour=23, minute=59)
                out_time = reference_calendar.get_work_duration_data(start, stop, compute_leaves=False,
                                                                     domain=['|', ('work_entry_type_id', '=', False), (
                                                                     'work_entry_type_id.is_leave', '=', False)])
                out_days += out_time['days']
                out_hours += out_time['hours']

            if out_days or out_hours:
                work_entry_type = self.env.ref('hr_payroll.hr_work_entry_type_out_of_contract')
                res.append({
                    'sequence': work_entry_type.sequence,
                    'work_entry_type_id': work_entry_type.id,
                    'number_of_days': out_days,
                    'number_of_hours': out_hours,
                })
                work_entry_type = self.env.ref('hr_work_entry.work_entry_type_attendance')
                work100 = next(filter(lambda x: x['work_entry_type_id'] == work_entry_type.id, res), None)
                if work100:
                    days = work100['number_of_days'] - out_days
                    hours = work100['number_of_hours'] - out_hours
                    work100.update(
                        {
                            'number_of_days': days,
                            'number_of_hours': hours,
                        }
                )
        return res


def special_round(number):
    parte_decimal = number - int(number)  # Obtener la parte decimal del número
    if parte_decimal < 0.5:
        return int(number)
    else:
        return int(number) + 1


def leave_antiquity_bonus(payslip, employee):
    leave_leave_antiquity_bonus_percen = 0
    if payslip:
        leave_leave_antiquity_bonus_percen = payslip.dict._get_antiquity_bonus(employee)
    return leave_leave_antiquity_bonus_percen


def credit_balance_previous_month(payslip, employee):
    credit_balance_previous_month_amount = 0
    if payslip:
        credit_balance_previous_month_amount = payslip.dict._get_credit_balance_previous_month(employee)
    return credit_balance_previous_month_amount


def amount_total_gained_average(payslip, employee, aguinaldo, ruler):
    amount_christmas_bonus = 0
    if payslip:
        if aguinaldo:
            date_limit = date(payslip.dict.date_from.year, 10, 1)
            if employee.date_hired > date_limit:
                return 0
            date_start_cal = date(payslip.dict.date_from.year, 9, 1)
            if employee.date_hired == date_limit:
                date_start_cal = employee.date_hired
            date_to_cal = date(payslip.dict.date_from.year, 11, 30)
        else:
            date_start_cal = date(payslip.dict.date_from.year, 10, 1)
            date_to_cal = date(payslip.dict.date_from.year, 12, 31)
        amount_christmas_bonus = payslip.dict._get_amount_total_gained(employee, date_start_cal, date_to_cal, ruler)
    return amount_christmas_bonus/3


def days_total_worked(payslip, employee, aguinaldo, ruler):
    amount_christmas_bonus = 0
    if payslip:
        if aguinaldo:
            date_limit = date(payslip.dict.date_from.year, 10, 1)
            if employee.date_hired > date_limit:
                return 0
            date_start_cal = date(payslip.dict.date_from.year, 9, 1)
            if employee.date_hired >= date_start_cal:
                days = 30 - employee.date_hired.day + 1
                return 60 + days
            else:
                return 360
        else:
            date_start_cal = date(payslip.dict.date_from.year, 10, 1)
            date_to_cal = date(payslip.dict.date_from.year, 12, 31)
        amount_christmas_bonus = payslip.dict._get_amount_total_gained(employee, date_start_cal, date_to_cal, ruler)
    return amount_christmas_bonus/3


def total_average_earned(payslip, employee, ruler, months):
    average_earned = payslip.dict._get_total_average_earned(payslip.date_to, employee, ruler, months)
    return average_earned


