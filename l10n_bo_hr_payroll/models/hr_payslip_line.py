# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, _
from odoo.exceptions import UserError


class HrPayslipLine(models.Model):
    _inherit = 'hr.payslip.line'

    @api.depends('quantity', 'amount', 'rate')
    def _compute_total(self):
        for line in self:
            line.total = float(line.quantity) * line.amount * line.rate / 100
            if line.code in ['BASE_IMPONIBLE', 'IMPUESTO', 'TAX_2_SMN', 'IMP_NETO_RC_IVA', 'SALDO_A_FAVOR_FISCO',
                             'SALDO_A_FAVOR_DEPEND', 'SALDO_A_FAVOR_MES_ANT', 'ACTUALIZACION', 'SAL_ANT_ACT',
                             'SALDO_UTILIZADO', 'IMP_RET_PAGAR', 'SAL_PROX_MES']:
                line.total = round(line.total, 0)
