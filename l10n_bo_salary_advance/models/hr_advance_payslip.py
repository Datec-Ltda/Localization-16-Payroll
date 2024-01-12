# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import models, Command, fields, api, tools, _


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.depends('employee_id', 'contract_id', 'struct_id', 'date_from', 'date_to', 'struct_id')
    def _compute_input_line_ids(self):
        super(HrPayslip, self)._compute_input_line_ids()
        input_line_vals = []
        attachment_types = self._get_attachment_types_advance()
        attachment_type_ids = [f.id for f in attachment_types.values()]
        lines_to_remove = self.input_line_ids.filtered(lambda x: x.input_type_id.id in attachment_type_ids)
        input_line_vals = [Command.unlink(line.id) for line in lines_to_remove]
        for payslip in self:
            if payslip.employee_id:
                adv_salary = payslip.env['salary.advance'].search(
                    [('employee_id', '=', payslip.employee_id.id),
                     ('state', '=', 'approve')
                     ])
                for adv_obj in adv_salary:
                    current_date = payslip.date_from.month
                    date = adv_obj.date
                    existing_date = date.month
                    if current_date == existing_date:
                        input_type = payslip.env.ref('l10n_bo_salary_advance.payslip_input_type_advance')
                        input_line_vals.append(Command.create({
                            'name': adv_obj.reason,
                            'amount': adv_obj.advance,
                            'input_type_id': input_type.id,
                        }))
                    payslip.update({'input_line_ids': input_line_vals})
            else:
                payslip.update({'input_line_ids': input_line_vals})

    @api.model
    def _get_attachment_types_advance(self):
        return {
            'load': self.env.ref('l10n_bo_salary_advance.payslip_input_type_advance'),
        }
