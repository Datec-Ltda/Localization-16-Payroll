import logging

from odoo import fields, models, api, _
from odoo.exceptions import AccessError, UserError, ValidationError


_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    # Datos quinquenio
    balance = fields.Float(string="Saldo", compute='_compute_balance', store=True)
    quinquennial_ids = fields.One2many('hr.payroll.quinquennial.data', 'employee_id', string='Pago quinquenal')

    bonus_payment_ids = fields.One2many(
        comodel_name='hr.bonus.payment',
        inverse_name='employee_id',
    )

    @api.depends('years_of_service', 'quinquennial_ids.amount_years')
    def _compute_balance(self):
        for record in self:
            total_amount_years = sum(record.quinquennial_ids.mapped('amount_years'))
            record.balance = record.years_of_service - total_amount_years

    def get_total_average_earned(self, date_to, employee, ruler, months):
        domain = [('date_to', '<', date_to), ('employee_id', '=', employee.id)]

        registers = self.env['hr.payroll.closing.table'].search(domain, order='date_to desc', limit=months)
        if not registers:
            return 0
        else:
            sum_day = 0
            sum_salary = 0
            for register in registers:
                sum_day += register.worked_days
                if ruler == 'BASIC':
                    sum_salary += register.basic
                if ruler == 'BONO_ANT':
                    sum_salary += register.antiquity_bonus
                if ruler == 'BONO_PROD':
                    sum_salary += register.production_bonus
                if ruler == 'SUBS_FRONTERA':
                    sum_salary += register.frontier_subsidy
                if ruler == 'EXTRAS':
                    sum_salary += register.overtime_amount
                if ruler == 'DOMINGO':
                    sum_salary += register.sunday_overtime_amount
                if ruler == 'DT':
                    sum_salary += register.sunday_worked_amount
                if ruler == 'RECARGO':
                    sum_salary += register.night_overtime_hours_amount
                if ruler == 'NET':
                    sum_salary += register.net_salary
                if ruler == 'PRIMA':
                    sum_salary += register.prima
                if ruler == 'GROSS':
                    sum_salary += register.gross
                if ruler == 'BONOS':
                    sum_salary += register.other_bonuses

            return sum_salary/months

    def GetQuinquennialAverage(self, date_from, date_to, ruler):
        domain = [('date_pay', '<=', date_to),
                  ('date_pay', '>=', date_from),
                  ('state', '=', 'open'),
                  ('employee_id', '=', self.id)]

        register = self.env['hr.payroll.quinquennial.data'].search(domain, order='date_to desc', limit=1)
        if register:
            average = self.get_total_average_earned(date_to, self, ruler, 3)
            return average
        else:
            return 0

    def GetQuinquennialYear(self, date_from, date_to):
        domain = [('date_pay', '<=', date_to),
                  ('date_pay', '>=', date_from),
                  ('state', '=', 'open'),
                  ('employee_id', '=', self.id)]

        register = self.env['hr.payroll.quinquennial.data'].search(domain, order='date_to desc', limit=1)
        if register:
            return register.amount_years
        else:
            return 0


