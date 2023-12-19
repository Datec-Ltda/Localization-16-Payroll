# -*- coding:utf-8 -*-

from odoo import api, fields, models, tools, _
from datetime import date
import calendar
import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import float_round, date_utils, convert_file, html2plaintext, is_html_empty, format_amount
from odoo.exceptions import UserError, ValidationError

# This will generate 16th of days
ROUNDING_FACTOR = 16
_logger = logging.getLogger(__name__)


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    is_retroactive = fields.Boolean()
    basic_percent = fields.Float()
    smn_percent = fields.Float()

    line_ids2 = fields.One2many(
        'hr.payslip.line', 'slip_id', string='Payslip Lines',
        compute='_compute_line_ids', store=True, readonly=True, copy=True,
        states={'draft': [('readonly', False)], 'verify': [('readonly', False)]}, domain=[('retroactive', '=', True)])

    payslip_retroactive_id = fields.Many2one(
        'hr.payroll.employee.payments.retroactive.list', string='Batch Name', readonly=True,
        copy=False, states={'draft': [('readonly', False)], 'verify': [('readonly', False)]},
        domain="[('company_id', '=', company_id)]")

    def _get_base_local_dict(self):
        res = super()._get_base_local_dict()
        res.update({
            'leave_antiquity_bonus': leave_antiquity_bonus,
            'credit_balance_previous_month': credit_balance_previous_month,
            'amount_total_gained_average': amount_total_gained_average,
            'days_total_worked': days_total_worked,
            'special_round': special_round,
            'total_average_earned': total_average_earned,
            'get_ufv_from_code': get_ufv_from_code,
            'get_medical_leave_percent': get_medical_leave_percent,
            'amount_total_gained_in_month': amount_total_gained_in_month,
            'get_finiquito_value': get_finiquito_value,
            'get_is_retroactive': get_is_retroactive,
        })
        return res

    def _get_is_retroactive(self):
        return self.is_retroactive

    def _get_antiquity_bonus(self, employee):
        percent = 0
        years_of_service = employee.years_of_service
        domain = [('years_of_antiquity_bonus_start', '<=', years_of_service)]
        leave_antiquity = self.env['hr.antiquity.bonus.table'].search(domain, limit=1, order="years_of_antiquity_bonus_start desc")
        if leave_antiquity:
            percent = leave_antiquity.percentage
        return percent

    def get_day_month_past(self, date_now):
        month_past = date_now.month - 1  # Obtener el mes anterior
        # Manejar el caso especial de enero, donde el mes anterior es diciembre del año anterior
        if month_past == 0:
            month_past = 12
            year_past = date_now.year - 1
        else:
            year_past = date_now.year
        _, last_day_now = calendar.monthrange(date_now.year, date_now.month)
        if last_day_now == date_now.day:
            _, day_past_moth = calendar.monthrange(year_past, month_past)
        else:
            day_past_moth = date_now.day

        # Crear una nueva fecha con el mismo día que la fecha original pero en el mes y año anterior
        date_past = date(year_past, month_past, day_past_moth)
        return date_past

    def _get_credit_balance_previous_month(self, employee):
        credit = 0
        date_from = self.get_day_month_past(self.date_from)
        date_to = self.get_day_month_past(self.date_to)

        domain = [('date_from', '=', date_from),
                  ('date_to', '=', date_to),
                  ('employee_id', '=', employee.id)]
        closing_table = self.env['hr.payroll.closing.table'].search(domain, limit=1)
        if closing_table:
            credit = closing_table.credit_next_month
        return credit

    def _get_amount_total_gained(self, employee,  date_start_cal, date_to_ca, ruler):
        amount = 0
        domain = [('date_from', '>=', date_start_cal),
                  ('date_to', '<=', date_to_ca),
                  ('employee_id', '=', employee.id)]
        closing_table = self.env['hr.payroll.closing.table'].search(domain)
        for record in closing_table:
            if ruler == 'BASIC':
                amount += record.basic
            if ruler == 'BONO_ANT':
                amount += record.antiquity_bonus
            if ruler == 'BONO_PROD':
                amount += record.production_bonus
            if ruler == 'SUBS_FRONTERA':
                amount += record.frontier_subsidy
            if ruler == 'EXTRAS':
                amount += record.overtime_amount
            if ruler == 'DOMINGO':
                amount += record.sunday_overtime_amount
            if ruler == 'DT':
                amount += record.sunday_worked_amount
            if ruler == 'RECARGO':
                amount += record.night_overtime_hours_amount
            if ruler == 'NET':
                amount += record.net_salary
            if ruler == 'PRIMA':
                amount += record.prima
            if ruler == 'GROSS':
                amount += record.gross
            if ruler == 'BONOS':
                amount += record.other_bonuses
        return amount

    def _get_total_average_earned(self, date_to, employee, ruler, months):
        domain = [('date_to', '<=', date_to), ('employee_id', '=', employee.id)]
        closing_table = self.env['hr.payroll.closing.table'].search(domain, order='date_to desc', limit=months)
        if not closing_table:
            return 0
        else:
            amount = 0
            for record in closing_table:
                if ruler == 'BASIC':
                    amount += record.basic
                if ruler == 'BONO_ANT':
                    amount += record.antiquity_bonus
                if ruler == 'BONO_PROD':
                    amount += record.production_bonus
                if ruler == 'SUBS_FRONTERA':
                    amount += record.frontier_subsidy
                if ruler == 'EXTRAS':
                    amount += record.overtime_amount
                if ruler == 'DOMINGO':
                    amount += record.sunday_overtime_amount
                if ruler == 'DT':
                    amount += record.sunday_worked_amount
                if ruler == 'RECARGO':
                    amount += record.night_overtime_hours_amount
                if ruler == 'NET':
                    amount += record.net_salary
                if ruler == 'PRIMA':
                    amount += record.prima
                if ruler == 'GROSS':
                    amount += record.gross
                if ruler == 'BONOS':
                    amount += record.other_bonuses
        return amount/months

    def _get_worked_day_lines_values(self, domain=None):
        self.ensure_one()
        res = []
        if self.struct_id.country_id.code != 'CO':
            super()._get_worked_day_lines_values(domain=domain)

        hours_per_day = self._get_worked_day_lines_hours_per_day()
        date_from = datetime.combine(self.date_from, datetime.min.time())
        date_to = datetime.combine(self.date_to, datetime.max.time())
        work_hours = self.contract_id._get_work_hours(date_from, date_to, domain=domain)
        work_hours_ordered = sorted(work_hours.items(), key=lambda x: x[1])
        biggest_work = work_hours_ordered[-1][0] if work_hours_ordered else 0
        add_days_rounding = 0
        overtime_hours = self.env['hr.payroll.overtime.hours.list'].search([('employee_id', '=', self.employee_id.id),
                                                                    ('contract_id', '=', self.contract_id.id),
                                                                    ('date_from', '>=', self.date_from),
                                                                    ('date_to', '<=', self.date_to),
                                                                    ('state', '=', 'open')], limit=1)
        for work_entry_type_id, hours in work_hours_ordered:
            work_entry_type = self.env['hr.work.entry.type'].browse(work_entry_type_id)
            if work_entry_type.code == 'WORK100':
                we_type = self.env.ref('hr_work_entry.work_entry_type_attendance')
                valor = 30
                horas = 240
                attendance_line = {
                    'sequence': we_type.sequence,
                    'work_entry_type_id': we_type.id,
                    'number_of_days': valor,
                    'number_of_hours': horas,
                }
                res.append(attendance_line)
            else:
                work_entry_type = self.env['hr.work.entry.type'].browse(work_entry_type_id)
                days = round(hours / hours_per_day, 5) if hours_per_day else 0
                if work_entry_type_id == biggest_work:
                    days += add_days_rounding
                day_rounded = self._round_days(work_entry_type, days)
                add_days_rounding += (days - day_rounded)
                attendance_line = {
                    'sequence': work_entry_type.sequence,
                    'work_entry_type_id': work_entry_type_id,
                    'number_of_days': day_rounded,
                    'number_of_hours': hours,
                }
                res.append(attendance_line)

        # obtener el tiempo de trabajo horas extras

        if overtime_hours:
            # overtime
            we_type = self.env.ref('l10n_bo_hr_payroll.hr_work_entry_type_overtime')
            if overtime_hours.overtime != 0:
                res.append({
                    'sequence': we_type.sequence,
                    'work_entry_type_id': we_type.id,
                    'number_of_days': overtime_hours.overtime / hours_per_day,
                    'number_of_hours': overtime_hours.overtime,
                })
            # hours_night_overtime
            we_type = self.env.ref('l10n_bo_hr_payroll.hr_work_entry_type_hours_night_overtime')
            if overtime_hours.hours_night_overtime != 0:
                res.append({
                    'sequence': we_type.sequence,
                    'work_entry_type_id': we_type.id,
                    'number_of_days': overtime_hours.hours_night_overtime / hours_per_day,
                    'number_of_hours': overtime_hours.hours_night_overtime,
                    'amount': 0,
                })
            # sunday_overtime
            we_type = self.env.ref('l10n_bo_hr_payroll.hr_work_entry_type_sunday_overtime')
            if overtime_hours.sunday_overtime != 0:
                res.append({
                    'sequence': we_type.sequence,
                    'work_entry_type_id': we_type.id,
                    'number_of_days': overtime_hours.sunday_overtime / hours_per_day,
                    'number_of_hours': overtime_hours.sunday_overtime,
                })
            # sunday_worked
            we_type = self.env.ref('l10n_bo_hr_payroll.hr_work_entry_type_sunday_worked')
            if overtime_hours.sunday_worked != 0:
                res.append({
                    'sequence': we_type.sequence,
                    'work_entry_type_id': we_type.id,
                    'number_of_days': overtime_hours.sunday_worked / hours_per_day,
                    'number_of_hours': overtime_hours.sunday_worked,
                })

        return res

    def _get_worked_day_lines(self, domain=None, check_out_of_contract=True):
        """
        :returns: a list of dict containing the worked days values that should be applied for the given payslip
        """
        res = []
        # fill only if the contract as a working schedule linked
        self.ensure_one()
        contract = self.contract_id
        if contract.resource_calendar_id:
            res = self._get_worked_day_lines_values(domain=domain)
            if not check_out_of_contract:
                return res

            # If the contract doesn't cover the whole month, create
            # worked_days lines to adapt the wage accordingly
            out_days, out_hours = 0, 0
            reference_calendar = self._get_out_of_contract_calendar()
            if self.date_from < contract.date_start:
                # start = fields.Datetime.to_datetime(self.date_from)
                # stop = fields.Datetime.to_datetime(contract.date_start) + relativedelta(days=-1, hour=23, minute=59)
                # out_time = reference_calendar.get_work_duration_data(start, stop, compute_leaves=False,
                #                                                      domain=['|', ('work_entry_type_id', '=', False), (
                #                                                      'work_entry_type_id.is_leave', '=', False)])
                if self.date_from.month == contract.date_start.month:
                    out_day = contract.date_start + relativedelta(days=-1, hour=23, minute=59)
                    out_days += out_day.day
                    out_hours += out_day.day * 8
                else:
                    out_days += 30
                    out_hours += 240
            if contract.date_end and contract.date_end < self.date_to:
                # start = fields.Datetime.to_datetime(contract.date_end) + relativedelta(days=1)
                # stop = fields.Datetime.to_datetime(self.date_to) + relativedelta(hour=23, minute=59)
                # out_time = reference_calendar.get_work_duration_data(start, stop, compute_leaves=False,
                #                                                      domain=['|', ('work_entry_type_id', '=', False), (
                #                                                      'work_entry_type_id.is_leave', '=', False)])
                if self.date_to.month == contract.date_end.month:
                    out_day = 30 - contract.date_end.day
                    out_days += out_day
                    out_hours += out_day * 8
                else:
                    out_days += 30
                    out_hours += 240
            if out_days or out_hours:
                work_entry_type = self.env.ref('hr_payroll.hr_work_entry_type_out_of_contract')
                res.append({
                    'sequence': work_entry_type.sequence,
                    'work_entry_type_id': work_entry_type.id,
                    'number_of_days': out_days,
                    'number_of_hours': out_hours,
                })
                work_entry_type = self.env.ref('hr_work_entry.work_entry_type_attendance')
                work100 = next(filter(lambda x: x['work_entry_type_id'] == work_entry_type.id, res), None)
                if work100:
                    days = work100['number_of_days'] - out_days
                    hours = work100['number_of_hours'] - out_hours
                    work100.update(
                        {
                            'number_of_days': days,
                            'number_of_hours': hours,
                        }
                    )
            else:
                work_entry_type = self.env.ref('hr_work_entry.work_entry_type_attendance')
                work100 = next(filter(lambda x: x['work_entry_type_id'] == work_entry_type.id, res), None)
                if not work100:
                    valor = 30
                    attendance_line = {
                        'sequence': work_entry_type.sequence,
                        'work_entry_type_id': work_entry_type.id,
                        'number_of_days': valor,
                        'number_of_hours': valor * 8,
                    }
                    res.append(attendance_line)
        return res

    def _get_ufv_from_code(self, date_to, code):
        if code == 'CURRENT_UFV':
            date_search = date_to
        else:
            date_search = self.get_day_month_past(date_to)

        parameter = self.env['hr.payroll.housing.development.unit'].search([
            ('date_month', '<=', date_search)], limit=1,  order='date_month desc')
        if parameter:
            return parameter.ufv_value
        else:
            return 0

    def _get_medical_leave_percent_by_name(self, code):
        percent = 0
        if code == 'BMEC':
            holiday_type = self.env.ref('l10n_bo_hr_payroll.holiday_type_bm_enf_comun')
        if code == 'BM_PRENATAL':
            holiday_type = self.env.ref('l10n_bo_hr_payroll.holiday_type_bm_prenatal')
        if code == 'BM_POSTNATAL':
            holiday_type = self.env.ref('l10n_bo_hr_payroll.holiday_type_bm_postnatal')
        if code == 'BM_ACC_LAB':
            holiday_type = self.env.ref('l10n_bo_hr_payroll.holiday_type_bm_acc_lab')
        if code == 'BM_RIESG_EXT':
            holiday_type = self.env.ref('l10n_bo_hr_payroll.holiday_type_bm_ext_risk')

        domain = [('id', '=', holiday_type.id)]
        leave_type = self.env['hr.leave.type'].search(domain, limit=1)
        if leave_type:
            percent = leave_type.get_percent()

        return percent

    def _get_paid_amount(self):
        self.ensure_one()
        if self.env.context.get('no_paid_amount'):
            return 0.0
        if not self.worked_days_line_ids:
            return self._get_contract_wage()
        total_amount = 0
        for line in self.worked_days_line_ids:
            if line.code == 'WORK100':
                total_amount += line.amount
        return total_amount

    # TODO move this function into hr_contract module, on hr.employee object
    @api.model
    def get_contract(self, employee, date_from, date_to):

        """
        @param employee: recordset of employee
        @param date_from: date field
        @param date_to: date field
        @return: returns the ids of all the contracts for the given employee that need to be considered for the given dates
        """
        # a contract is valid if it ends between the given dates
        clause_1 = ['&', ('date_end', '<=', date_to),
                    ('date_end', '>=', date_from)]
        # OR if it starts between the given dates
        clause_2 = ['&', ('date_start', '<=', date_to),
                    ('date_start', '>=', date_from)]
        # OR if it starts before the date_from and finish after the date_end (or never finish)
        clause_3 = ['&', ('date_start', '<=', date_from), '|',
                    ('date_end', '=', False), ('date_end', '>=', date_to)]
        clause_final = [('employee_id', '=', employee.id),
                        ('state', '=', 'open'), '|',
                        '|'] + clause_1 + clause_2 + clause_3
        return self.env['hr.contract'].search(clause_final).ids

    def _get_rule_finiquito_by_code(self, date_from, date_to, code):
        domain = [('report_date', '>=', date_from),
                  ('report_date', '<=', date_to),
                  ('employee_id', '=', self.employee_id.id),
                  ('contract_id', '=', self.contract_id.id),
                  ('state', '=', 'open'),
                  ]
        finiquito = self.env['hr.payroll.finiquito'].search(domain, limit=1)
        value = 0
        if finiquito:
            if code == 'PROMEDIO':
                value = finiquito.average
            if code == 'MULTA':
                value = finiquito.penalties
            if code == 'DESAHUSIO':
                value = finiquito.eviction
            if code == 'INDEM':
                value = finiquito.indemnity_year_amount + finiquito.indemnity_month_amount + finiquito.indemnity_day_amount
            if code == 'AGUINALDO':
                value = finiquito.christmas_bonus_month_amount + finiquito.christmas_bonus_day_amount
            if code == 'VAC':
                value = finiquito.holidays_amount
            if code == 'OTROS_BONOS':
                value = finiquito.other_extraordinary_bonuses
            if code == 'FINIQUITO':
                value = finiquito.finiquito
        return value

    def compute_sheet(self):
        payslips = self.filtered(lambda slip: slip.state in ['draft', 'verify'])
        # delete old payslip lines
        self.is_retroactive = self.env.context.get('retroactive', False)

        if not self.is_retroactive:
            payslips.line_ids.unlink()
            # this guarantees consistent results
            self.env.flush_all()
            today = fields.Date.today()
            for payslip in payslips:
                number = payslip.number or self.env['ir.sequence'].next_by_code('salary.slip')
                payslip.write({
                    'number': number,
                    'state': 'verify',
                    'compute_date': today
                })
            self.env['hr.payslip.line'].create(payslips._get_payslip_lines())
        else:
            self._act_payslip_lines()
        return True

    def _get_payslip_lines(self):
        line_vals = []
        for payslip in self:
            if not payslip.contract_id:
                raise UserError(_("There's no contract set on payslip %s for %s. Check that there is at least a contract set on the employee form.", payslip.name, payslip.employee_id.name))

            localdict = self.env.context.get('force_payslip_localdict', None)
            if localdict is None:
                localdict = payslip._get_localdict()

            rules_dict = localdict['rules'].dict
            result_rules_dict = localdict['result_rules'].dict

            blacklisted_rule_ids = self.env.context.get('prevent_payslip_computation_line_ids', [])

            result = {}
            for rule in sorted(payslip.struct_id.rule_ids, key=lambda x: x.sequence):
                if rule.id in blacklisted_rule_ids:
                    continue
                localdict.update({
                    'result': None,
                    'result_qty': 1.0,
                    'result_rate': 100,
                    'result_name': False
                })
                if rule._satisfy_condition(localdict):
                    # Retrieve the line name in the employee's lang
                    employee_lang = payslip.employee_id.sudo().address_home_id.lang
                    # This actually has an impact, don't remove this line
                    context = {'lang': employee_lang}
                    if rule.code in localdict['same_type_input_lines']:
                        for multi_line_rule in localdict['same_type_input_lines'][rule.code]:
                            localdict['inputs'].dict[rule.code] = multi_line_rule
                            amount, qty, rate = rule._compute_rule(localdict)
                            tot_rule = amount * qty * rate / 100.0
                            localdict = rule.category_id._sum_salary_rule_category(localdict,
                                                                                   tot_rule)
                            rule_name = payslip._get_rule_name(localdict, rule, employee_lang)
                            line_vals.append({
                                'sequence': rule.sequence,
                                'code': rule.code,
                                'retroactive': rule.retroactive,
                                'name':  rule_name,
                                'note': html2plaintext(rule.note) if not is_html_empty(rule.note) else '',
                                'salary_rule_id': rule.id,
                                'contract_id': localdict['contract'].id,
                                'employee_id': localdict['employee'].id,
                                'amount': amount,
                                'quantity': qty,
                                'rate': rate,
                                'slip_id': payslip.id,
                            })
                    else:
                        amount, qty, rate = rule._compute_rule(localdict)
                        #check if there is already a rule computed with that code
                        previous_amount = rule.code in localdict and localdict[rule.code] or 0.0
                        #set/overwrite the amount computed for this rule in the localdict
                        tot_rule = amount * qty * rate / 100.0
                        localdict[rule.code] = tot_rule
                        result_rules_dict[rule.code] = {'total': tot_rule, 'amount': amount, 'quantity': qty}
                        rules_dict[rule.code] = rule
                        # sum the amount for its salary category
                        localdict = rule.category_id._sum_salary_rule_category(localdict, tot_rule - previous_amount)
                        rule_name = payslip._get_rule_name(localdict, rule, employee_lang)
                        # create/overwrite the rule in the temporary results
                        result[rule.code] = {
                            'sequence': rule.sequence,
                            'code': rule.code,
                            'retroactive': rule.retroactive,
                            'name': rule_name,
                            'note': html2plaintext(rule.note) if not is_html_empty(rule.note) else '',
                            'salary_rule_id': rule.id,
                            'contract_id': localdict['contract'].id,
                            'employee_id': localdict['employee'].id,
                            'amount': amount,
                            'quantity': qty,
                            'rate': rate,
                            'slip_id': payslip.id,
                        }
            line_vals += list(result.values())
        return line_vals

    def _act_payslip_lines(self):
        line_vals = []
        for payslip in self:
            if not payslip.contract_id:
                raise UserError(_("There's no contract set on payslip %s for %s. Check that there is at least a contract set on the employee form.", payslip.name, payslip.employee_id.name))

            localdict = self.env.context.get('force_payslip_localdict', None)
            if localdict is None:
                localdict = payslip._get_localdict()

            rules_dict = localdict['rules'].dict
            result_rules_dict = localdict['result_rules'].dict

            blacklisted_rule_ids = self.env.context.get('prevent_payslip_computation_line_ids', [])

            result = {}
            for line in sorted(self.line_ids, key=lambda x: x.sequence):
                for rule in payslip.struct_id.rule_ids.filtered(lambda x: x.code == line.code):
                    if rule.id in blacklisted_rule_ids:
                        continue
                    # localdict.update({
                    #     'result': None,
                    #     'result_qty': 1.0,
                    #     'result_rate': 100,
                    #     'result_name': False
                    # })
                    if rule._satisfy_condition(localdict):
                        # Retrieve the line name in the employee's lang
                        employee_lang = payslip.employee_id.sudo().address_home_id.lang
                        # This actually has an impact, don't remove this line
                        context = {'lang': employee_lang}
                        self.basic_percent = self.env.context.get('basic_percent', 0)
                        self.smn_percent = self.env.context.get('smn_percent', 0)
                        if rule.code in localdict['same_type_input_lines']:
                            for multi_line_rule in localdict['same_type_input_lines'][rule.code]:
                                localdict['inputs'].dict[rule.code] = multi_line_rule
                                amount_retroactive, qty, rate = rule._compute_rule(localdict)
                                localdict = rule.category_id._sum_salary_rule_category(localdict,
                                                                                       amount_retroactive)
                                # if rule.code == 'BASIC':
                                #     amount_retroactive += (amount_retroactive * basic_porcent)/100
                                # if rule.code == 'SMN':
                                #     amount_retroactive += (amount_retroactive * nmn_porcent)/100
                                line.write({
                                    'retroactive': rule.retroactive,
                                    'amount_retroactive': amount_retroactive,
                                })
                        else:
                            amount_retroactive, qty, rate = rule._compute_rule(localdict)
                            #check if there is already a rule computed with that code
                            previous_amount = rule.code in localdict and localdict[rule.code] or 0.0
                            #set/overwrite the amount computed for this rule in the localdict
                            localdict[rule.code] = amount_retroactive
                            # result_rules_dict[rule.code] = {'amount_retroactive': amount_retroactive}
                            rules_dict[rule.code] = rule
                            # sum the amount for its salary category
                            localdict = rule.category_id._sum_salary_rule_category(localdict, amount_retroactive - previous_amount)
                            # rule_name = payslip._get_rule_name(localdict, rule, employee_lang)
                            # create/overwrite the rule in the temporary results
                            # if rule.code == 'BASIC':
                            #     amount_retroactive += (amount_retroactive * basic_porcent) / 100
                            # if rule.code == 'SMN':
                            #     amount_retroactive += (amount_retroactive * nmn_porcent) / 100
                            line.write({
                                'retroactive': rule.retroactive,
                                'amount_retroactive': amount_retroactive,
                            })
        return True


def special_round(number):
    parte_decimal = number - int(number)  # Obtener la parte decimal del número
    if parte_decimal < 0.5:
        return int(number)
    else:
        return int(number) + 1


def leave_antiquity_bonus(payslip, employee):
    leave_leave_antiquity_bonus_percen = 0
    if payslip:
        leave_leave_antiquity_bonus_percen = payslip.dict._get_antiquity_bonus(employee)
    return leave_leave_antiquity_bonus_percen


def credit_balance_previous_month(payslip, employee):
    credit_balance_previous_month_amount = 0
    if payslip:
        credit_balance_previous_month_amount = payslip.dict._get_credit_balance_previous_month(employee)
    return credit_balance_previous_month_amount


def amount_total_gained_average(payslip, employee, aguinaldo, ruler):
    amount_christmas_bonus = 0
    if payslip:
        if aguinaldo:
            date_limit = date(payslip.dict.date_from.year, 10, 1)
            if employee.date_hired > date_limit:
                return 0
            date_start_cal = date(payslip.dict.date_from.year, 9, 1)
            if employee.date_hired == date_limit:
                date_start_cal = employee.date_hired
            date_to_cal = date(payslip.dict.date_from.year, 11, 30)
            amount_christmas_bonus = payslip.dict._get_amount_total_gained(employee, date_start_cal, date_to_cal, ruler)
        else:
            date_start_cal = date(payslip.dict.date_from.year-1, 10, 1)
            date_to_cal = date(payslip.dict.date_from.year-1, 12, 31)
            if employee.date_hired > date_start_cal:
                return 0
            else:
                amount_christmas_bonus = payslip.dict._get_amount_total_gained(employee, date_start_cal, date_to_cal, ruler)
    return amount_christmas_bonus/3


def amount_total_gained_in_month(payslip, employee, ruler):
    amount_in_month = 0
    if payslip:
        amount_in_month = payslip.dict._get_amount_total_gained(employee, payslip.date_from, payslip.date_to, ruler)
    return amount_in_month


def days_total_worked(payslip, employee, aguinaldo):
    if payslip:
        if aguinaldo:
            date_limit = date(payslip.dict.date_from.year, 10, 1)
            if employee.date_hired > date_limit:
                return 0
            date_start_cal = date(payslip.dict.date_from.year, 9, 1)
            if employee.date_hired >= date_start_cal:
                if employee.date_hired == date_limit:
                    total_days = 60
                else:
                    days = 30 - employee.date_hired.day + 1
                    total_days = 60 + days
            else:
                total_days = 330
            if not employee.departure_date:
                return total_days + 30
        else:
            date_start_cal = date(payslip.dict.date_from.year-1, 10, 1)
            date_init_year = date(payslip.dict.date_from.year-1, 1, 1)
            if employee.date_hired > date_start_cal:
                return 0
            else:
                if employee.date_hired <= date_init_year:
                    return 360
                else:
                    return (12 - employee.date_hired.month + 1) * 30
    return 0


def total_average_earned(payslip, employee, ruler, months):
    average_earned = payslip.dict._get_total_average_earned(payslip.date_to, employee, ruler, months)
    return average_earned


def get_ufv_from_code(payslip, code):
    ufv = payslip.dict._get_ufv_from_code(payslip.date_to, code)
    return ufv

def get_medical_leave_percent(payslip, code):
    percent = 0
    if payslip:
        percent = payslip.dict._get_medical_leave_percent_by_name(code)
    return percent/100


def get_finiquito_value(payslip, code):
    value = payslip.dict._get_rule_finiquito_by_code(payslip.date_from,payslip.date_to, code)
    return value


def get_is_retroactive(payslip):
    value = payslip.dict._get_is_retroactive()
    return value
