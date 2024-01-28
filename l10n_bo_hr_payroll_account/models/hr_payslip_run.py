# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    def action_draft(self):
        if self.slip_ids.filtered(lambda s: s.state == 'paid'):
            raise ValidationError(_('You cannot reset a batch to draft if some of the payslips have already been paid.'))
        self.write({'state': 'draft'})
        self.slip_ids.write({'state': 'draft'})

        for slip in self.slip_ids:
            struct = self.env.ref('l10n_bo_hr_payroll.structure_retroactive')
            if slip.struct_id.id == struct.id:
                retroactive_env = self.env['hr.payroll.employee.payments.retroactive.list']
                retroactive_element = retroactive_env.search([('employee_id', '=', slip.employee_id.id),
                                                                ('date_from', '=', slip.date_from),
                                                                ('date_to', '<=', slip.date_to),
                                                                ('state', '=', 'closed')])
                if retroactive_element:
                    move = retroactive_element.sudo().write({'state': 'open'})
                    retroactive_element.payment_retroactive_id.write({'state': 'open'})


