import logging

from odoo import fields, models, api, _
from odoo.exceptions import AccessError, UserError, ValidationError


_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    # Datos quinquenio
    balance = fields.Float(string="Saldo", compute='_compute_balance', store=True)
    quinquennial_ids = fields.One2many('hr.payroll.quinquennial.data', 'employee_id', string='Pago quinquenal')

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


class HrPayrollQuinquennialData(models.Model):
    _name = 'hr.payroll.quinquennial.data'
    _description = 'Datos Quinquenio'
    _rec_name = "employee_id"

    payslip_id = fields.Many2one('hr.payslip')
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True)
    contract_id = fields.Many2one(related='employee_id.contract_id', string="contract employee")
    # Campo calculado entre la fecha de consulta y la fecha de inicio de contrato menos la cantidad
    # de años pagados

    type_of_payment = fields.Selection([
        ('0001', 'Pago de Quinquenio'),
        ('0002', 'Adelanto de Quinquenio')],
        string='Clase de documento', default='0001')

    amount_years = fields.Integer(string = "Cantidad")
    date_from = fields.Date(string='Fecha de inicio', help="Fecha de inicio de formulario de pago de quinquenio", required=True)
    date_to = fields.Date(string='Fecha fin', help="Fecha fin de formulario de pago de quinquenio", required=True)
    date_pay = fields.Date(string='Fecha de pago',  help="Fecha de pago de quinquenio", required=True)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('open', 'Listo'),
        ('paid', 'Pagado'),
    ], default='draft', string="Estado")

    @api.constrains('amount_years')
    def _check_amount_years(self):
        for record in self:
            paid_records = self.search([
                ('state', 'in', ['draft', 'open', 'paid']),
                ('id', '!=', record.id),
                ('employee_id', '=', self.employee_id.id),
            ])
            if paid_records:
                total_years = sum(paid_records.mapped('amount_years'))
                balance = record.employee_id.years_of_service - total_years - record.amount_years
            else:
                balance = record.employee_id.years_of_service - record.amount_years

            if balance < 0:
                raise ValidationError("No puede pedir esa cantidad de años.")

    @api.constrains('employee_id')
    def _check_employee_contract(self):
        for record in self:
            if not record.employee_id.contract_id:
                raise ValidationError("Error: No se puede adicionar pago quinquenal sin contrato asociado para el empleado.")

    @api.constrains('date_from', 'date_to', 'amount_years')
    def _check_date_overlap(self):
        for record in self:
            if record.date_from and record.date_to:
                if record.date_from >= record.date_to:
                    raise ValidationError("La fecha de inicio debe ser anterior a la fecha de fin.")

                unpaid_records = self.search([
                    ('date_from', '<=', record.date_to),
                    ('date_to', '>=', record.date_from),
                    ('state', 'in', ['draft', 'open']),
                    ('employee_id', '=', self.employee_id.id),
                    ('id', '!=', record.id),
                ])

                if unpaid_records:
                    raise ValidationError("No deben existir registros anteriores sin pagar, confecione un solo registro para el pago.")

                overlapping_records = self.search([
                    ('date_from', '<=', record.date_to),
                    ('date_to', '>=', record.date_from),
                    ('employee_id', '=', self.employee_id.id),
                    ('id', '!=', record.id),
                ])

                if overlapping_records:
                    raise ValidationError("Las fechas se solapan con otro registro existente.")

            if record.date_from:
                if record.date_from < record.employee_id.date_hired:
                    raise ValidationError("La fecha de iniciodebe ser mayor a la fecha de contratación.")

    def action_set_draft(self):
        self.write({'state': 'draft'})
        return True

    def action_set_open(self):
        self.write({'state': 'open'})
        return True

    def unlink(self):
        for line in self:
            if line.state != 'draft':
                raise UserError(
                    _('No puede borrar el registro si no esta en estado borrador.')
                )
        return super(HrPayrollQuinquennialData, self).unlink()


