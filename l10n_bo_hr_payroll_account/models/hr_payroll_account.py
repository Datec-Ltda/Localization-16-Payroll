# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict
from markupsafe import Markup

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero, plaintext2html
from dateutil.relativedelta import relativedelta


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    closing_table = fields.Boolean(default=False, string="Has closing table", readonly=True, copy=False)

    def action_payslip_cancel(self):
        moves = self.mapped('move_id')
        moves.filtered(lambda x: x.state == 'posted').button_cancel()
        moves.unlink()
        self._action_quinquennial_cancel()
        self._action_finiquito_cancel()
        self._action_prima_cancel()
        return super(HrPayslip, self).action_payslip_cancel()

    def action_payslip_done(self):
        """
            Generate the accounting entries related to the selected payslips
            A move is created for each journal and for each month.
        """
        res = super(HrPayslip, self).action_payslip_done()
        self._action_create_closing_table()
        self._action_quinquennial_pay()
        self._action_finiquito_pay()
        self._action_create_prima_table()
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
                             'basic': 0.0, 'antiquity_bonus': 0.0, 'production_bonus': 0.0, 'frontier_subsidy': 0.0,
                             'other_bonuses': 0.0, 'net_salary': 0.0, 'credit_next_month': 0.0, 'overtime_amount': 0.0,
                             'sunday_overtime_amount': 0.0, 'sunday_worked_amount': 0.0, 'night_overtime_hours_amount': 0.0, 'gross': 0.0,
                             'worked_days': 0.0, 'worked_hours': 0.0, 'overtime': 0.0, 'sunday_overtime': 0.0,
                             'prima': 0.0, 'night_overtime_hours': 0.0, 'sunday_worked': 0.0}
            # Para el caso que el pago quinquenal no archivar en la tabla de cierre, si es una estructura aparte
            for line in slip.line_ids.filtered(lambda x: x.code in ['QUINQUENAL', 'FINIQUITO']):
                if line.code == 'QUINQUENAL' or line.code == 'FINIQUITO':
                    return 0
            for line in slip.line_ids.filtered(lambda x: x.code in ['BASIC', 'BONO_ANT', 'BONO_PROD', 'SUBS_FRONTERA', 'EXTRAS', 'DOMINGO', 'DT', 'RECARGO', 'NET', 'SAL_PROX_MES', 'PRIMA']):
                if line.code == 'BASIC':
                    closing_table['basic'] = line.amount
                if line.code == 'BONO_ANT':
                    closing_table['antiquity_bonus'] = line.amount
                if line.code == 'BONO_PROD':
                    closing_table['production_bonus'] = line.amount
                if line.code == 'SUBS_FRONTERA':
                    closing_table['frontier_subsidy'] = line.amount
                if line.code == 'EXTRAS':
                    closing_table['overtime_amount'] = line.amount
                if line.code == 'DOMINGO':
                    closing_table['sunday_overtime_amount'] = line.amount
                if line.code == 'DT':
                    closing_table['sunday_worked_amount'] = line.amount
                if line.code == 'RECARGO':
                    closing_table['night_overtime_hours_amount'] = line.amount
                if line.code == 'NET':
                    closing_table['net_salary'] = line.amount
                if line.code == 'SAL_PROX_MES':
                    closing_table['credit_next_month'] = line.amount
                if line.code == 'PRIMA':
                    closing_table['prima'] = line.amount
            for worked_day in slip.worked_days_line_ids.filtered(lambda x: x.code in ['WORK100', 'HE', 'HRN', 'HED', 'DT']):
                if worked_day.code == 'WORK100':
                    closing_table['worked_days'] = worked_day.number_of_days
                    closing_table['worked_hours'] = worked_day.number_of_hours
                if worked_day.code == 'HE':
                    closing_table['overtime'] = worked_day.number_of_hours
                if worked_day.code == 'HRN':
                    closing_table['night_overtime_hours'] = worked_day.number_of_hours
                if worked_day.code == 'HED':
                    closing_table['sunday_overtime'] = worked_day.number_of_hours
                if worked_day.code == 'DT':
                    closing_table['sunday_worked'] = worked_day.number_of_hours
            # Para las categorias
            categories = {}
            categories_mapping = {
                'GROSS': 'gross',
                'BONO': 'other_bonuses',
            }
            for line in slip.line_ids:
                category_code = line.category_id.code
                if category_code in ('GROSS', 'BONO'):
                    if category_code not in categories:
                        if category_code == 'BONO':
                            if line.code not in ('BONO_ANT', 'BONO_PROD', 'SUBS_FRONTERA'):
                                categories[category_code] = line.amount
                        else:
                            categories[category_code] = line.amount
                    else:
                        if category_code == 'BONO':
                            if line.code not in ('BONO_ANT', 'BONO_PROD', 'SUBS_FRONTERA'):
                                categories[category_code] += line.amount
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
                move = closing_table_element.sudo().update(closing_table)
            else:
                move = closing_table_env.sudo().create(closing_table)

    # Para marcar el registro quinquenal como pagado
    def _action_quinquennial_pay(self):
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
            for line in slip.line_ids.filtered(lambda x: x.code in ['QUINQUENAL']):
                if line.code == 'QUINQUENAL':
                    quinquennial_env = self.env['hr.payroll.quinquennial.data']
                    quinquennial_element = quinquennial_env.search([('contract_id', '=', slip.contract_id.id),
                                                                    ('date_pay', '>=', slip.date_from),
                                                                    ('date_pay', '<=', slip.date_to),
                                                                    ('state', '=', 'open')])
                    if quinquennial_element:
                        move = quinquennial_element.sudo().write({'state': 'paid'})

    def _action_quinquennial_cancel(self):
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
            for line in slip.line_ids.filtered(lambda x: x.code in ['QUINQUENAL']):
                if line.code == 'QUINQUENAL':
                    quinquennial_env = self.env['hr.payroll.quinquennial.data']
                    quinquennial_element = quinquennial_env.search([('contract_id', '=', slip.contract_id.id),
                                                                    ('date_pay', '>=', slip.date_from),
                                                                    ('date_pay', '<=', slip.date_to),
                                                                    ('state', '=', 'paid')])
                    if quinquennial_element:
                        move = quinquennial_element.sudo().write({'state': 'open'})

    def _action_finiquito_pay(self):
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
            for line in slip.line_ids.filtered(lambda x: x.code in ['FINIQUITO']):
                if line.code == 'FINIQUITO':
                    finiquito_env = self.env['hr.payroll.finiquito']
                    finiquito_element = finiquito_env.search([('contract_id', '=', slip.contract_id.id),
                                                                    ('report_date', '>=', slip.date_from),
                                                                    ('report_date', '<=', slip.date_to),
                                                                    ('state', '=', 'open')])
                    if finiquito_element:
                        move = finiquito_element.sudo().write({'state': 'paid'})
                        if finiquito_element.holidays_days > 0:
                            # generar la petición de usencia con los dias pedidos
                            current_employee = self.env.user.employee_id
                            date_to = finiquito_element.date_end + relativedelta(days=finiquito_element.holidays_days)
                            values = [{
                                'date_from': finiquito_element.date_end,
                                'date_to': date_to,
                                'request_date_from': finiquito_element.date_end,
                                'request_date_to': date_to,
                                'holiday_status_id': 1,
                                'employee_id': finiquito_element.employee_id.id,
                                'employee_company_id': finiquito_element.contract_id.company_id.id,
                                'department_id': finiquito_element.contract_id.department_id.id,
                                'first_approver_id': current_employee.id,
                                'second_approver_id': current_employee.id,
                                'private_name': 'vacaciones liquidadas por finiquito'  + finiquito_element.employee_id.name,
                                'state': 'draft',
                                'duration_display': finiquito_element.holidays_days,
                                'holiday_type': 'employee',
                                'payslip_state': 'done',
                            }]
                            leave_env = self.env['hr.leave']
                            # work_days_data = leave_env._get_work_days_data_batch(finiquito_element.date_end, date_to)
                            if finiquito_element.leave_id:
                                leave_element = leave_env.search([('id', '=', finiquito_element.leave_id.id)])
                                if leave_element:
                                    leave_element.update({
                                        'state': 'draft',
                                    })
                                    move = leave_element.sudo().unlink()
                            leave = leave_env.sudo().create(values)
                            leave.update({
                                'state': 'validate',
                                'number_of_days': finiquito_element.holidays_days,
                                'duration_display': finiquito_element.holidays_days,
                            })
                            finiquito_element.write({'leave_id': leave.id})

    def _action_finiquito_cancel(self):
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
            for line in slip.line_ids.filtered(lambda x: x.code in ['FINIQUITO']):
                if line.code == 'FINIQUITO':
                    finiquito_env = self.env['hr.payroll.finiquito']
                    finiquito_element = finiquito_env.search([('contract_id', '=', slip.contract_id.id),
                                                                    ('report_date', '>=', slip.date_from),
                                                                    ('report_date', '<=', slip.date_to),
                                                                    ('state', '=', 'paid')])
                    if finiquito_element:
                        move = finiquito_element.sudo().update({'state': 'open'})
                        leave_env = self.env['hr.leave']
                        if finiquito_element.leave_id:
                            leave_element = leave_env.search([('id', '=', finiquito_element.leave_id.id)])
                            leave_element.update({
                                'state': 'draft',
                            })
                            move = leave_element.sudo().unlink()

    def _action_create_prima_table(self):
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
            bonus_table = {'payslip_id': slip.id, 'contract_id': slip.contract_id.id,
                             'employee_id': slip.employee_id.id, 'date_from': slip.date_from, 'date_to': slip.date_to,
                             'earned_average': 0.0, 'paid_percentage': 0.0, 'days_considered': 0.0, 'amount_paid': 0.0}
            # Para el caso que el pago quinquenal no archivar en la tabla bonus
            for line in slip.line_ids.filtered(lambda x: x.code in ['QUINQUENAL', 'FINIQUITO']):
                if line.code == 'QUINQUENAL' or line.code == 'FINIQUITO':
                    return 0
            for line in slip.line_ids.filtered(lambda x: x.code in ['TOTAL_GANADO', 'PERCEN_PAY', 'DIAS_TRAB', 'PRIMA']):
                if line.code == 'TOTAL_GANADO':
                    bonus_table['earned_average'] = line.amount
                if line.code == 'PERCEN_PAY':
                    bonus_table['paid_percentage'] = line.amount
                if line.code == 'DIAS_TRAB':
                    bonus_table['days_considered'] = line.amount
                if line.code == 'PRIMA':
                    bonus_table['amount_paid'] = line.amount

            bonus_table_env = self.env['hr.bonus.payment']
            bonus_table_element = bonus_table_env.search([('contract_id', '=', slip.contract_id.id),
                                                          ('date_from', '=', slip.date_from,),
                                                          ('date_to', '=', slip.date_to)])

            if bonus_table_element:
                move = bonus_table_element.sudo().update(bonus_table)
            else:
                move = bonus_table_env.sudo().create(bonus_table)

    def _action_prima_cancel(self):
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
            for line in slip.line_ids.filtered(lambda x: x.code in ['PRIMA']):
                if line.code == 'PRIMA':
                    bonus_table_env = self.env['hr.bonus.payment']
                    bonus_table_element = bonus_table_env.search([('contract_id', '=', slip.contract_id.id),
                                                                  ('date_from', '=', slip.date_from,),
                                                                  ('date_to', '=', slip.date_to)])
                    if bonus_table_element:
                        move = bonus_table_element.sudo().unlink()
