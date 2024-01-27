from odoo import fields, models, api, _


class HrBonusPayment(models.Model):
    _name = "hr.bonus.payment"
    _description = "Pago de prima"
    _rec_name = "employee_id"

    employee_id = fields.Many2one('hr.employee', string='Empleado', required=True, ondelete="cascade")
    payslip_id = fields.Many2one('hr.payslip')
    number = fields.Char(related='payslip_id.number', readonly=False, tracking=True)
    contract_id = fields.Many2one('hr.contract', 'Contract', required=True)
    date_from = fields.Date(string='Date From', copy=False)
    date_to = fields.Date(string='Date To', copy=False)

    earned_average = fields.Float(string='Promedio Ganado',
                                  help='Campo calculado promedio sobre el total ganado de los 3 meses ',
                                  required=False
                                  )

    paid_percentage = fields.Float(string='Paid Percentage',
                                   help='Porcentaje pagado',
                                   required=False
                                   )

    days_considered = fields.Integer(string='Días considerados',
                                     help='Días trabajados en la gestión a pagar por el cual se paga el monto de prima',
                                     required=False
                                     )

    amount_paid = fields.Float(string='Importe Pagado',
                               help='Campo calculado del monto de prima pagado para la gestión',
                               required=False
                               )