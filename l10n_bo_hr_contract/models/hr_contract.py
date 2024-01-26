from odoo import fields, models

class Employee(models.Model):
    _inherit = "hr.employee"

    contract_id = fields.Many2one(
        'hr.contract', string='Contrato actual', groups="hr.group_hr_user",
        domain="[('company_id', '=', company_id), ('employee_id', '=', id)]", help='Contrato actual del empleado')

class HrContract(models.Model):
    _inherit = 'hr.contract'

    measurement_staff = fields.Selection([
        ('contratacion', 'Contratación'),
        ('reingreso', 'Reingreso'),
        ('change', 'Cambio Organizativo'),
        ('baja', 'Baja')],
        string='Medida de personal')

    reason_measurement_id = fields.Many2one('hr.contract.reason.measurement', string='Motivo de medida')


class HrContractReasonMeasurement(models.Model):
    _name = 'hr.contract.reason.measurement'
    _description = 'Motivo de medida'

    code = fields.Char('código', required=True)
    name = fields.Char(string="Motivo de medida", translate=True, required=True)
