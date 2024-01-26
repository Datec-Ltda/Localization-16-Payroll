# -*- coding: utf-8 -*-

from psycopg2 import sql
from odoo import tools
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import ValidationError

MES_LITERAL = [('1', 'Enero'),
               ('2', 'Febrero'),
               ('3', 'Marzo'),
               ('4', 'Abril'),
               ('5', 'Mayo'),
               ('6', 'Junio'),
               ('7', 'Julio'),
               ('8', 'Agosto'),
               ('9', 'Septiembre'),
               ('10', 'Octubre'),
               ('11', 'Noviembre'),
               ('12', 'Diciembre')]


class HrPayrollPayRetroactiveReport(models.Model):
    _name = "hr.payroll.pay.retroactive.report"
    _description = 'Pagos retroactivos realizados'
    _auto = False
    _order = 'retroactive'

    retroactive = fields.Char(string="Pago retroactivo")
    basic_percent = fields.Float(string='Porciento de incremento del salario basico')
    smn_percent = fields.Float(string='Porciento de incremento del salario minimo nacional')
    company_id = fields.Many2one('res.company', 'Compañia')
    employee_id = fields.Many2one('hr.employee', string='Empleado')
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('open', 'Abierto'),
        ('closed', 'Cerrado'),
    ], string='Status', index=True, default='draft')
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    year = fields.Char(compute="_compute_year", string="Año", store=True)
    month = fields.Char(compute="_compute_month", string="Año", store=True)
    # month = fields.Char(string="Mes")
    payslip = fields.Char(string="Nómina")
    department_id = fields.Many2one('hr.department', string='Departamento')
    job_id = fields.Many2one('hr.job', string='Puesto de trabajo')
    number = fields.Char(string="número de nómina")
    salary_rule_id = fields.Many2one('hr.salary.rule', string='Rule')
    category_id = fields.Many2one('hr.salary.rule.category', string='Category')
    code = fields.Char(string="Código")
    amount = fields.Float(string="Monto anterior", default=0.0)
    total = fields.Float(string='Total', default=0.0)
    amount_retroactive = fields.Float(string='Monto recalculado', default=0.0)
    different_amount = fields.Float(string='Diferencia', default=0.0)

    @api.depends('date_from')
    def _compute_year(self):
        return self.date_from.year

    @api.depends('date_from')
    def _compute_month(self):
        return MES_LITERAL[self.date_from.month-1][1]

    def init(self):
        query = """              
        SELECT hpl.id,
               hrpepr.name AS retroactive,   
               hrpepr.basic_percent,
               hrpepr.smn_percent,
               hrpepr.state,
               hrpepr.company_id,    
               hrpeprl.employee_id,
               hrpeprl.date_from,
               hrpeprl.date_to,
               hp.name AS payslip,
               to_char(hp.date_from, 'TMMonth') AS month_old,
               hp.department_id,
               hp.job_id,
               hp.number,
               hpl.salary_rule_id,
               hpl.category_id,
               hpl.code,
               hpl.amount,
               hpl.total,
               hpl.amount_retroactive,
               hpl.different_amount                                                    
        FROM hr_payroll_employee_payments_retroactive hrpepr
                 JOIN hr_payroll_employee_payments_retroactive_list hrpeprl ON hrpepr.id = hrpeprl.payment_retroactive_id
                 JOIN hr_payslip hp ON hrpeprl.id = hp.payslip_retroactive_id
                 JOIN hr_payslip_line hpl ON hp.id = hpl.slip_id
        WHERE hpl.retroactive = true
        ORDER BY hrpepr.id, hrpeprl.id, hp.id, hpl.sequence
         """
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            sql.SQL("CREATE or REPLACE VIEW {} as ({})").format(
                sql.Identifier(self._table),
                sql.SQL(query)
            ))

