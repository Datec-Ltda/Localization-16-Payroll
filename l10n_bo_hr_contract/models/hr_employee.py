from odoo import fields, models


class Employee(models.Model):
    _inherit = "hr.employee"

    contract_id = fields.Many2one(
        'hr.contract', string='Contrato actual', groups="hr.group_hr_user",
        domain="[('company_id', '=', company_id), ('employee_id', '=', id)]", help='Contrato actual del empleado')
