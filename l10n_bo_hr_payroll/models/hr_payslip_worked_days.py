# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class HrPayslipWorkedDays(models.Model):
    _inherit = 'hr.payslip.worked_days'

    @api.depends('is_paid', 'number_of_hours', 'payslip_id', 'contract_id.wage', 'payslip_id.sum_worked_hours')
    def _compute_amount(self):
        res = super()._compute_amount()
        for worked_days in self:
            if worked_days.payslip_id.edited or worked_days.payslip_id.state not in ['draft', 'verify']:
                continue
            if not worked_days.contract_id or worked_days.code in ['OUT', 'HE', 'HRN', 'HED', 'DT']:
                worked_days.amount = 0
                continue
            if worked_days.payslip_id.wage_type == "hourly":
                worked_days.amount = worked_days.payslip_id.contract_id.hourly_wage * worked_days.number_of_hours if worked_days.is_paid else 0
            else:
                if worked_days.code == 'WORK100':
                    worked_days.amount = worked_days.payslip_id.contract_id.contract_wage /30 /8 * worked_days.number_of_hours
                else:
                    worked_days.amount = worked_days.payslip_id.contract_id.contract_wage * worked_days.number_of_hours / (
                                worked_days.payslip_id.sum_worked_hours or 1) if worked_days.is_paid else 0



