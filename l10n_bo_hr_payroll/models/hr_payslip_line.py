# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrPayslipLine(models.Model):
    _inherit = 'hr.payslip.line'

    @api.depends('quantity', 'amount', 'rate')
    def _compute_total(self):
        for line in self:
            line.total = float(line.quantity) * line.amount * line.rate / 100
            if line.code in ['GROSS', 'NET', 'TOTAL_AFP', 'TWO_SMN', 'BASE_IMPONIBLE', 'IMPUESTO', 'TAX_2_SMN',
                             'IMP_NETO_RC_IVA', 'IVA_FORM_110', 'SALDO_A_FAVOR_FISCO', 'SALDO_A_FAVOR_DEPEND',
                             'SALDO_A_FAVOR_MES_ANT', 'ACTUALIZACION', 'SAL_ANT_ACT', 'SALDO_UTILIZADO',
                             'IMP_RET_PAGAR', 'SAL_PROX_MES', 'TOTAL_AFP']:
                line.total = special_round(line.total)

    retroactive = fields.Boolean(default=False)
    amount_retroactive = fields.Monetary(default=0.0)
    different_amount = fields.Monetary(compute='_compute_different', string='Total', store=True)
    category_retroactive_id = fields.Many2one(related='salary_rule_id.category_id', readonly=True, store=True)

    @api.depends('amount_retroactive')
    def _compute_different(self):
        for line in self:
            line.different_amount =  line.amount_retroactive - line.amount


def special_round(number):
    if number < 0:
        parte_decimal = -number + int(number)
    else:
        parte_decimal = number - int(number)  # Obtener la parte decimal del número
    if parte_decimal < 0.5:
        return int(number)
    else:
        if number < 0:
            return int(number) - 1
        else:
            return int(number) + 1