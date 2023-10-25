# -*- coding:utf-8 -*-

from odoo import api, fields, models, tools, _
from datetime import date
import calendar
from datetime import datetime

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


