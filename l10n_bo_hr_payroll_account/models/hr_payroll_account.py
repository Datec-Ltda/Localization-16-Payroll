#-*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict
from markupsafe import Markup

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero, plaintext2html

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    closing_table = fields.Boolean(default=False, string="Has closing table", readonly=True, copy=False)

    def action_payslip_cancel(self):
        moves = self.mapped('move_id')
        moves.filtered(lambda x: x.state == 'posted').button_cancel()
        moves.unlink()
        return super(HrPayslip, self).action_payslip_cancel()

    def action_payslip_done(self):
        """
            Generate the accounting entries related to the selected payslips
            A move is created for each journal and for each month.
        """
        res = super(HrPayslip, self).action_payslip_done()
        self._action_create_closing_table()
        return res

    # def _action_close_suplementary_work(self):
    #

    def _action_create_closing_table(self):
        precision = self.env['decimal.precision'].precision_get('Payroll')

        # Add payslip without run
        payslips_to_post = self.filtered(lambda slip: not slip.payslip_run_id)

        # Adding pay slips from a batch and deleting pay slips with a batch that is not ready for validation.
        payslip_runs = (self - payslips_to_post).mapped('payslip_run_id')
        for run in payslip_runs:
            if run._are_payslips_ready():
                payslips_to_post |= run.slip_ids

        # A payslip need to have a done state and not an accounting move.
        payslips_to_post = payslips_to_post.filtered(lambda slip: slip.state == 'done' and not slip.closing_table)

        for slip in payslips_to_post:
            closing_table = {'payslip_id': slip.id, 'contract_id': slip.contract_id.id,
                             'employee_id': slip.employee_id.id, 'date_from': slip.date_from, 'date_to': slip.date_to,
                             'net_salary': 0.0, 'gross': 0.0, 'worked_days': 0.0}
            for line in slip.line_ids.filtered(lambda x: x.code in ['NET']):
                if line.code == 'NET':
                    closing_table['net_salary'] = line.amount
            for worked_day in slip.worked_days_line_ids.filtered(lambda x: x.code in ['WORK100']):
                if worked_day.code == 'WORK100':
                    closing_table['worked_days'] = worked_day.number_of_days
            # Para las categorias
            categories = {}
            categories_mapping = {
                'GROSS': 'gross',
            }
            for line in slip.line_ids:
                category_code = line.category_id.code
                if category_code in ('GROSS', ):
                    if category_code not in categories:
                        categories[category_code] = line.amount
                    else:
                        categories[category_code] += line.amount
            for category in categories:
                if category in categories_mapping:
                    field_name = categories_mapping[category]
                    closing_table[field_name] = categories[category]

            closing_table_env = self.env['hr.payroll.closing.table']
            closing_table_element = closing_table_env.search([('contract_id', '=', slip.contract_id.id),
                                                  ('date_from', '=', slip.date_from),
                                                  ('date_to', '=', slip.date_to)])
            if closing_table_element:
                move = closing_table_element.sudo().write(closing_table)
            else:
                move = closing_table_env.sudo().create(closing_table)

            #Para marcar el registro quinquenal como pagado
