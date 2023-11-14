from odoo import fields, models, api


class HolidaysType(models.Model):
    _inherit = 'hr.leave.type'

    medical_leave_has_percent = fields.Boolean('Aplica porciento', default=False)
    medical_leave_percent = fields.Float('% a aplicar', default=False)

    def get_percent(self):
        if self.medical_leave_has_percent:
            return self.medical_leave_percent
        else:
            return 0

