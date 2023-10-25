# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, tools


class HrEmployeePayrollReport(models.BaseModel):
    _auto = False
    _name = 'hr.employee.payroll.report'
    _description = 'Employee Payroll Report'
    _order = 'employee_id asc, payslip_id desc'

    id = fields.Id()
    display_name = fields.Char(related='employee_id.name')
    employee_id = fields.Many2one('hr.employee', readonly=True)
    company_id = fields.Many2one('res.company', readonly=True)
    department_id = fields.Many2one('hr.department', readonly=True)

    payslip_id = fields.Many2one('hr.payslip', readonly=True)
    date = fields.Date(related='payslip_id.date_from', string="Fecha inicio")
    payslip_line_code = fields.Char(related='payslip_line_id.code', string="Cod.")
    payslip_line_id = fields.Many2one('hr.payslip.line', readonly=True)
    payslip_line_code = fields.Char(related='payslip_line_id.code', string="Cod.")
    type_identification_document = fields.Selection([
        ('01', 'Cédula de identidad'),
        ('02', 'Licencia de Conducir'),
        ('03', 'Código de Dependiente')],
        string='Clase de documento', default='01')
    salary_rule_id = fields.Many2one('hr.salary.rule', readonly=True)
    amount = fields.Float(readonly=True, group_operator="sum")
    devengado = fields.Float(readonly=True, string="Valor Devengado")
    deduction_discount = fields.Float(readonly=True, string="Deduccion Descuento")
    neto = fields.Float(readonly=True, string="Valor neto")
    provisiones = fields.Float(readonly=True, string="IBC-Provisiones")
    liquidacion = fields.Float(readonly=True, string="Liquidación")

    def _where(self):
        return """
            psl.amount != 0 
        """

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)


        self.env.cr.execute("""
        CREATE OR REPLACE VIEW %s AS (
            SELECT
                row_number() OVER () AS id,
                e.id AS employee_id,
                e.company_id AS company_id,
                e.department_id AS department_id,
                e.type_identification_document AS type_identification_document
                ps.id AS payslip_id,
                psl.id AS payslip_line_id,
                psl.code AS payslip_line_code,
                sr.id AS salary_rule_id,
                sr.l10n_co_type_for_reports AS type_for_reports,
                CASE
                WHEN sr.l10n_co_type_for_reports = 'dev'
                THEN psl.amount
                ELSE 0.0
                END AS devengado,                
                CASE
                WHEN sr.l10n_co_type_for_reports = 'ded'
                THEN psl.amount
                ELSE 0.0
                END AS deduction_discount,
                CASE
                WHEN sr.l10n_co_type_for_reports = 'neto'
                THEN psl.amount
                ELSE 0.0
                END AS neto,   
                CASE
                WHEN sr.l10n_co_type_for_reports = 'ibc'
                THEN psl.amount
                ELSE 0.0
                END AS provisiones, 
                CASE
                WHEN sr.l10n_co_type_for_reports = 'liq'
                THEN psl.amount
                ELSE 0.0
                END AS liquidacion,                                              
                psl.amount
            FROM hr_employee e
            LEFT OUTER JOIN hr_payslip ps ON e.id = ps.employee_id
            LEFT OUTER JOIN hr_payslip_line psl ON ps.id = psl.slip_id
            LEFT OUTER JOIN hr_salary_rule sr ON sr.id = psl.salary_rule_id
            WHERE %s
        )
        """ % (self._table, self._where()))
