# -*- coding:utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero
from odoo.exceptions import ValidationError
import time
from datetime import datetime, timedelta
from dateutil import relativedelta


class HrPayrollClosingTable(models.Model):
    _name = 'hr.payroll.closing.table'
    _description = 'Tabla Cierre de nómina'
    _rec_name = "employee_id"

    payslip_id = fields.Many2one('hr.payslip')
    contract_id = fields.Many2one('hr.contract', 'Contract', required=True)
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True)
    date_from = fields.Date(string='Date From', copy=False)
    date_to = fields.Date(string='Date To', copy=False)
# Reglas --------------------------------------------------
    basic = fields.Float(string="Salario basico", default=0)
    antiquity_bonus = fields.Float(string="Bono de antigüedad", default=0)
    production_bonus = fields.Float(string="Bono de producción", default=0)
    frontier_subsidy = fields.Float(string="Subsidio de frontera", default=0)
    other_bonuses = fields.Float(string="Otros bonos", default=0)
    net_salary = fields.Float(string="Salario neto", default=0)
    credit_next_month = fields.Float(string="Saldo proximo mes", default=0)

    overtime_amount = fields.Float(string="Monto horas extras", default=0)
    sunday_overtime_amount = fields.Float(string="Monto horas extras dominical", default=0)
    night_overtime_hours_amount = fields.Float(string="Monto horas recargo nocturno", default=0)
    sunday_worked_amount = fields.Float(string="Monto domingo trabajado", default=0)
    prima = fields.Float(string="Prima", default=0)
# Categorias ----------------------------------------------
    gross = fields.Float(string="Salario devengado", default=0)
# Dias  ----------------------------------------------------
    worked_days = fields.Float(string="Días trabajados", required=True)
    worked_hours = fields.Float(string="Horas trabajadas", required=True)
    overtime = fields.Float(string="Horas extras", default=0)
    sunday_overtime = fields.Float(string="Horas extra dominical", default=0)
    night_overtime_hours = fields.Float(string="Horas recargo nocturno", default=0)
    sunday_worked = fields.Float(string="Domingos trabajados", default=0)

    @api.constrains('date_from', 'date_to', 'contract_id')
    def _check_leave(self):
        for closing_table in self:
            if closing_table.date_from and closing_table.date_to and closing_table.contract_id:
                register_leaves = self.search([('date_from', '=', closing_table.date_from),
                                               ('date_to', '=', closing_table.date_to),
                                               ('contract_id', '=', closing_table.contract_id.id)])
                if len(register_leaves) > 1:
                    raise ValidationError(_('No puedes crear dos registro para el trabajador en el mismo periodo de tiempo.'))


