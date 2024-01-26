# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import date
from dateutil.relativedelta import relativedelta

MESES= {'1': 'Enero',
        '2':'Febrero',
        '3':'Marzo',
        '4':'Abril',
        '5':'Mayo',
        '6':'Junio',
        '7':'Julio',
        '8':'Agosto',
        '9':'Septiembre',
        '10':'Octubre',
        '11':'Noviembre',
        '12':'Diciembre'}

class HrPayrollFiniquito(models.Model):
    _name = "hr.payroll.finiquito"
    _description = "Calculo del finiquito"

    employee_id = fields.Many2one('hr.employee', 'Empleado', required=True,
                                  domain="[('active', '=', False)]")
    contract_id = fields.Many2one(related='employee_id.contract_id', string="Contrato", store=True)
    date_hire = fields.Date(related='employee_id.date_hired', string='Fecha contratación', required=True)
    date_end = fields.Date(related='employee_id.departure_date', string='Fecha fin del contrato', required=True)
    report_date = fields.Date(string='Fecha de reporte', required=True)
    leave_id = fields.Many2one('hr.leave', string="Ausencia")

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('open', 'Abierto'),
        ('paid', 'Pagado'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft')

    month1 = fields.Char(compute='_compute_month')

    @api.depends('date_end')
    def _compute_month(self):
        if self.date_end:
            months = self.get_previous_months()
            if months:
                self.month1 = MESES[str(months['mes 1'])]
                self.month2 = MESES[str(months['mes 2'])]
                self.month3 = MESES[str(months['mes 3'])]
            else:
                self.month1 = "Mes 1"
                self.month2 = "Mes 2"
                self.month3 = "Mes 3"
        else:
            self.month1 = "Mes 1"
            self.month2 = "Mes 2"
            self.month3 = "Mes 3"

    month2 = fields.Char(compute='_compute_month')
    month3 = fields.Char(compute='_compute_month')

    christmas_bonus_one = fields.Char(string="Aguinaldo uno")
    has_christmas_bonus_one = fields.Boolean(string="Tiene Aguinaldo", default=False)

    christmas_bonus_two = fields.Char(string="Segundo aguinaldo")
    has_christmas_bonus_two = fields.Boolean(string="Tiene Seg Aguinaldo", default=False)

    pay_second = fields.Boolean(string="Segundo Aguinaldo", default=False)

    monthly_compensation1 = fields.Float(string="Remuneración Mensual mes 1", required=True)
    monthly_compensation2 = fields.Float(string="Remuneración Mensual mes 2", required=True)
    monthly_compensation3 = fields.Float(string="Remuneración Mensual mes 3", required=True)
    monthly_compensation_total = fields.Float(string="Remuneración Mensual total", compute='_compensation_total',
                                              store=True)

    seniority_bonus1 = fields.Float(string="Bono Antiguedad mes 1", required=True)
    seniority_bonus2 = fields.Float(string="Bono Antiguedad mes 2", required=True)
    seniority_bonus3 = fields.Float(string="Bono Antiguedad mes 3", required=True)
    seniority_bonus_total = fields.Float(string="Bono Antiguedad Total", compute='_seniority_bonus', store=True)

    border_bonus1 = fields.Float(string="Bono Frontera mes 1", required=True)
    border_bonus2 = fields.Float(string="Bono Frontera mes 2", required=True)
    border_bonus3 = fields.Float(string="Bono Frontera mes 3", required=True)
    border_bonus_total = fields.Float(string="Bono Frontera Total", compute='_border_bonus', store=True)

    commissions1 = fields.Float(string="Comisiones mes 1", required=True)
    commissions2 = fields.Float(string="Comisiones mes 2", required=True)
    commissions3 = fields.Float(string="Comisiones mes 3", required=True)
    commissions_total = fields.Float(string="Comisiones Total", compute='_commissions', store=True)

    overtime1 = fields.Float(string="Horas Extras mes 1", required=True)
    overtime2 = fields.Float(string="Horas Extras mes 2", required=True)
    overtime3 = fields.Float(string="Horas Extras mes 3", required=True)
    overtime_total = fields.Float(string="Horas Extras Total", compute='_overtime', store=True)

    other_bonuses1 = fields.Float(string="Otros bonos 1", required=True)
    other_bonuses2 = fields.Float(string="Otros bonos 2", required=True)
    other_bonuses3 = fields.Float(string="Otros bonos 3", required=True)
    other_bonuses_total = fields.Float(string="Otros bonos total", compute='_other_bonuses', store=True)

    total1 = fields.Float(string="Total 1", compute='_get_total_colum1', store=True)
    total2 = fields.Float(string="Total 2", compute='_get_total_colum2', store=True)
    total3 = fields.Float(string="Total 3", compute='_get_total_colum3', store=True)
    total_total = fields.Float(string="Total", compute='_get_total', store=True)

    average = fields.Float(string="Promedio", compute='_get_average', store=True)

    has_eviction = fields.Boolean(string="Tiene Desahucio", required=True)
    eviction = fields.Float(string="Desahucio", compute='_get_eviction', store=True)

    indemnity_year = fields.Integer(string="Cantidad de Años", required=True)
    indemnity_year_amount = fields.Float(string="Años Importe", compute='_get_indemnity_year_amount', store=True)
    indemnity_month = fields.Integer(string="Cantidad de Meses", required=True)
    indemnity_month_amount = fields.Float(string="Meses Importe", compute='_get_indemnity_month_amount', store=True)
    indemnity_day = fields.Integer(string="Cantidad de días", required=True)
    indemnity_day_amount = fields.Float(string="Días Importe", compute='_get_indemnity_day_amount', store=True)

    christmas_bonus_month = fields.Integer(string="Aguinaldo meses", required=True)
    christmas_bonus_month_amount = fields.Float(string="Importe de Aguinaldo",
                                                compute='_get_christmas_bonus_month_amount', store=True)

    christmas_bonus_day = fields.Integer(string="Aguinaldo dias", required=True)
    christmas_bonus_day_amount = fields.Float(string="Importe de Aguinaldo en días",
                                              compute='_get_christmas_bonus_day_amount', store=True)

    holidays_days = fields.Integer(string="Días de vacaciones", required=True)
    holidays_amount = fields.Float(string="Importe de vacaciones", compute='_get_holidays_amount_amount', store=True)

    other_extraordinary_bonuses = fields.Float(string="Otros Bonos extraordinarios", required=True)

    has_penalties = fields.Boolean(string="Tiene Multa", required=True)

    penalties = fields.Float(string="Multas", compute='_get_penalties', store=True)

    finiquito = fields.Float(string="Finiquito", compute='_get_finiquito', store=True)

    def action_period_draft(self):
        self.write({'state': 'draft'})
        return True

    def action_period_open(self):
        self.write({'state': 'open'})
        return True

    def action_refresh(self):
        if self.employee_id:
            self.onchange_employee_id()
        return True

    def action_period_closed(self):
        self.write({'state': 'closed'})
        return True

    @api.depends('monthly_compensation1', 'monthly_compensation2', 'monthly_compensation3')
    def _compensation_total(self):
        for record in self:
            record.monthly_compensation_total = record.monthly_compensation1 + record.monthly_compensation2 + record.monthly_compensation3

    @api.depends('seniority_bonus1', 'seniority_bonus2', 'seniority_bonus3')
    def _seniority_bonus(self):
        for record in self:
            record.seniority_bonus_total = record.seniority_bonus1 + record.seniority_bonus2 + record.seniority_bonus3

    @api.depends('border_bonus1', 'border_bonus2', 'border_bonus3')
    def _border_bonus(self):
        for record in self:
            record.border_bonus_total = record.border_bonus1 + record.border_bonus2 + record.border_bonus3

    @api.depends('commissions1', 'commissions2', 'commissions3')
    def _commissions(self):
        for record in self:
            record.commissions_total = record.commissions1 + record.commissions2 + record.commissions3

    @api.depends('overtime1', 'overtime2', 'overtime3')
    def _overtime(self):
        for record in self:
            record.overtime_total = record.overtime1 + record.overtime2 + record.overtime3

    @api.depends('other_bonuses1', 'other_bonuses2', 'other_bonuses3')
    def _other_bonuses(self):
        for record in self:
            record.other_bonuses_total = record.other_bonuses1 + record.other_bonuses2 + record.other_bonuses3

    @api.depends('monthly_compensation1', 'seniority_bonus1', 'border_bonus1', 'commissions1', 'overtime1',
                 'other_bonuses1')
    def _get_total_colum1(self):
        for record in self:
            record.total1 = record.monthly_compensation1 + record.seniority_bonus1 + record.border_bonus1 + record.commissions1 + record.overtime1 + record.other_bonuses1

    @api.depends('monthly_compensation2', 'seniority_bonus2', 'border_bonus2', 'commissions2', 'overtime2',
                 'other_bonuses2')
    def _get_total_colum2(self):
        for record in self:
            record.total2 = record.monthly_compensation2 + record.seniority_bonus2 + record.border_bonus2 + record.commissions2 + record.overtime2 + record.other_bonuses2

    @api.depends('monthly_compensation3', 'seniority_bonus3', 'border_bonus3', 'commissions3', 'overtime3',
                 'other_bonuses3')
    def _get_total_colum3(self):
        for record in self:
            record.total3 = record.monthly_compensation3 + record.seniority_bonus3 + record.border_bonus3 + record.commissions3 + record.overtime3 + record.other_bonuses3

    @api.depends('total1', 'total2', 'total3')
    def _get_total(self):
        for record in self:
            record.total_total = record.total1 + record.total2 + record.total3

    @api.depends('total_total')
    def _get_average(self):
        for record in self:
            record.average = record.total_total / 3

    @api.depends('average', 'has_eviction')
    def _get_eviction(self):
        for record in self:
            if record.has_eviction:
                record.eviction = record.average * 3
            else:
                record.eviction = 0

    @api.depends('average', 'indemnity_year')
    def _get_indemnity_year_amount(self):
        for record in self:
            record.indemnity_year_amount = record.average * record.indemnity_year

    @api.depends('average', 'indemnity_month')
    def _get_indemnity_month_amount(self):
        for record in self:
            record.indemnity_month_amount = record.average / 12 * record.indemnity_month

    @api.depends('average', 'indemnity_day')
    def _get_indemnity_day_amount(self):
        for record in self:
            record.indemnity_day_amount = record.average / 360 * record.indemnity_day

    @api.depends('average', 'christmas_bonus_month')
    def _get_christmas_bonus_month_amount(self):
        for record in self:
            record.christmas_bonus_month_amount = record.average / 12 * record.christmas_bonus_month

    @api.depends('average', 'christmas_bonus_day')
    def _get_christmas_bonus_day_amount(self):
        for record in self:
            record.christmas_bonus_day_amount = record.average / 360 * record.christmas_bonus_day

    @api.depends('average', 'holidays_days')
    def _get_holidays_amount_amount(self):
        for record in self:
            record.holidays_amount = record.average / 30 * record.holidays_days

    @api.depends('eviction', 'indemnity_year_amount', 'indemnity_month_amount', 'indemnity_day_amount',
                 'christmas_bonus_month_amount', 'christmas_bonus_day_amount', 'holidays_amount',
                 'other_extraordinary_bonuses', 'has_penalties')
    def _get_penalties(self):
        total = 0
        for record in self:
            if record.has_penalties:
                if record.has_eviction:
                    total += record.eviction
                total += record.indemnity_year_amount + record.indemnity_month_amount + record.indemnity_day_amount + \
                         record.christmas_bonus_month_amount + record.christmas_bonus_day_amount + record.holidays_amount + \
                         record.other_extraordinary_bonuses

                record.penalties = total * 0.30
            else:
                record = 0

    @api.depends('eviction', 'indemnity_year_amount', 'indemnity_month_amount', 'indemnity_day_amount',
                 'christmas_bonus_month_amount', 'christmas_bonus_day_amount', 'holidays_amount',
                 'other_extraordinary_bonuses', 'penalties')
    def _get_finiquito(self):
        total = 0
        for record in self:
            if record.has_eviction:
                total += record.eviction
            if record.has_penalties:
                total += record.penalties
            total += record.indemnity_year_amount + record.indemnity_month_amount + record.indemnity_day_amount + \
                     record.christmas_bonus_month_amount + record.christmas_bonus_day_amount + record.holidays_amount + \
                     record.other_extraordinary_bonuses

            record.finiquito = total

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        self.holidays_days = self.employee_id.remaining_leave_year
        self.indemnity_year = self.employee_id.balance
        self.indemnity_month = self.indemnity_accumulated_month(self.employee_id)
        self.indemnity_day = self.indemnity_accumulated_day(self.employee_id)
        self.christmas_bonus_month = self.christmas_bonus_accumulated_month(self.employee_id)
        self.christmas_bonus_day = self.christmas_bonus_accumulated_day(self.employee_id)
        # inicializar variables
        self.monthly_compensation1 = 0
        self.monthly_compensation2 = 0
        self.monthly_compensation3 = 0
        self.seniority_bonus1 = 0
        self.seniority_bonus2 = 0
        self.seniority_bonus3 = 0
        self.border_bonus1 = 0
        self.border_bonus2 = 0
        self.border_bonus3 = 0
        self.commissions1 = 0
        self.commissions2 = 0
        self.commissions3 = 0
        self.overtime1 = 0
        self.overtime2 = 0
        self.overtime3 = 0
        self.other_bonuses1 = 0
        self.other_bonuses2 = 0
        self.other_bonuses3 = 0
        values_basic = self.get_previous_month_rule('BASIC')
        if values_basic:
            self.monthly_compensation1 = values_basic['mes 1']
            self.monthly_compensation2 = values_basic['mes 2']
            self.monthly_compensation3 = values_basic['mes 3']
        values_basic = self.get_previous_month_rule('BONO_ANT')
        if values_basic:
            self.seniority_bonus1 = values_basic['mes 1']
            self.seniority_bonus2 = values_basic['mes 2']
            self.seniority_bonus3 = values_basic['mes 3']
        values_basic = self.get_previous_month_rule('SUBS_FRONTERA')
        if values_basic:
            self.border_bonus1 = values_basic['mes 1']
            self.border_bonus2 = values_basic['mes 2']
            self.border_bonus3 = values_basic['mes 3']
        values_basic = self.get_previous_month_rule('EXTRAS')
        if values_basic:
            self.overtime1 = values_basic['mes 1']
            self.overtime2 = values_basic['mes 2']
            self.overtime3 = values_basic['mes 3']
        values_prod = self.get_previous_month_rule('BONO_PROD')
        values_bono = self.get_previous_month_rule('BONOS')
        values_sunday = self.get_previous_month_rule('DOMINGO')
        values_dt = self.get_previous_month_rule('DT')
        values_recargo = self.get_previous_month_rule('RECARGO')
        if values_basic:
            self.other_bonuses1 = values_prod['mes 1'] + values_bono['mes 1'] + values_sunday['mes 1'] + values_dt['mes 1'] + values_recargo['mes 1']
            self.other_bonuses2 = values_prod['mes 2'] + values_bono['mes 2'] + values_sunday['mes 2'] + values_dt['mes 2'] + values_recargo['mes 2']
            self.other_bonuses3 = values_prod['mes 3'] + values_bono['mes 3'] + values_sunday['mes 3'] + values_dt['mes 3'] + values_recargo['mes 3']

    @api.constrains('employee_id', 'contract_id')
    def _check_unique_employee_contract(self):
        for finiquito in self:
            existing_finiquitos = self.env['hr.payroll.finiquito'].search([
                ('employee_id', '=', finiquito.employee_id.id),
                ('contract_id', '=', finiquito.contract_id.id),
                ('id', '!=', finiquito.id)  # Exclude the current record
            ])
            if existing_finiquitos:
                raise ValidationError("Ya existe un registro de finiquito con el mismo empleado y contrato.")

    def get_previous_month_rule(self, ruler):
        values = {}
        if self.date_end:
            date_to_cal = date(self.date_end.year, self.date_end.month, 1)
            domain = [('employee_id', '=', self.employee_id.id),
                      ('contract_id', '=', self.contract_id.id),
                      ('date_from', '<', date_to_cal)]
            closing_table = self.env['hr.payroll.closing.table'].search(domain,  order='date_to desc', limit=3)
            amount = 0
            for idx, record in enumerate(reversed(closing_table), start=1):
                if ruler == 'BASIC':
                    amount = record.basic
                if ruler == 'BONO_ANT':
                    amount = record.antiquity_bonus
                if ruler == 'BONO_PROD':
                    amount = record.production_bonus
                if ruler == 'SUBS_FRONTERA':
                    amount = record.frontier_subsidy
                if ruler == 'EXTRAS':
                    amount = record.overtime_amount
                if ruler == 'DOMINGO':
                    amount = record.sunday_overtime_amount
                if ruler == 'DT':
                    amount += record.sunday_worked_amount
                if ruler == 'RECARGO':
                    amount = record.night_overtime_hours_amount
                if ruler == 'NET':
                    amount = record.net_salary
                if ruler == 'PRIMA':
                    amount = record.prima
                if ruler == 'GROSS':
                    amount = record.gross
                if ruler == 'BONOS':
                    amount = record.other_bonuses
                values['mes {}'.format(idx)] = amount
        return values

    def get_previous_months(self):
        values = {}
        if self.date_end:
            date_to_cal = date(self.date_end.year, self.date_end.month, 1)
            domain = [('employee_id', '=', self.employee_id.id),
                      ('contract_id', '=', self.contract_id.id),
                      ('date_from', '<', date_to_cal)]
            closing_table = self.env['hr.payroll.closing.table'].search(domain,  order='date_to desc', limit=3)
            for idx, record in enumerate(reversed(closing_table), start=1):
                values['mes {}'.format(idx)] = record.date_from.month
        return values

    def indemnity_accumulated_month(self, employee_id):
        if employee_id.date_hired:
            date_hired_last_year = date(self.date_end.year - 1, employee_id.date_hired.month, employee_id.date_hired.day)
            date_hired_this_year = date(self.date_end.today().year, employee_id.date_hired.month, employee_id.date_hired.day)
            if self.date_end < date_hired_this_year:
                diff = relativedelta(self.date_end, date_hired_last_year)
            else:
                diff = relativedelta(self.date_end, date_hired_this_year)
            return diff.months
        else:
            return 0

    def indemnity_accumulated_day(self, employee_id):
        if employee_id.date_hired:
            date_hired_last_year = date(self.date_end.year - 1, employee_id.date_hired.month, employee_id.date_hired.day)
            date_hired_this_year = date(self.date_end.year, employee_id.date_hired.month, employee_id.date_hired.day)
            if self.date_end < date_hired_this_year:
                diff = relativedelta(self.date_end, date_hired_last_year)
            else:
                diff = relativedelta(self.date_end, date_hired_this_year)
            return diff.days
        else:
            return 0

    def christmas_bonus_accumulated_month(self, employee_id):
        if employee_id.departure_date:
            date_init = date(employee_id.departure_date.year, 1, 1)
            date_from_aguinaldo = date(employee_id.departure_date.year, 12, 1)
            month_bonus = 0
            if date_from_aguinaldo < employee_id.departure_date:
                if self.has_christmas_bonus(employee_id):
                    if self.pay_second:
                        diff = relativedelta(employee_id.departure_date, date_init)
                        month_bonus = diff.months
                    else:
                        month_bonus = 0
                else:
                    diff = relativedelta(employee_id.departure_date, date_init)
                    month_bonus = diff.months
            else:
                diff = relativedelta(employee_id.departure_date, date_init)
                month_bonus = diff.months
            return month_bonus
        else:
            return 0

    def christmas_bonus_accumulated_day(self, employee_id):
        if employee_id.departure_date:
            date_init_month = date(employee_id.departure_date.year, employee_id.departure_date.month, 1)
            date_from_aguinaldo = date(employee_id.departure_date.year, 12, 1)
            days_bonus = 0
            if date_from_aguinaldo < employee_id.departure_date:
                if self.has_christmas_bonus(employee_id):
                    if self.pay_second:
                        diff = relativedelta(self.date_end, date_init_month)
                        days_bonus = diff.days + 1
                    else:
                        days_bonus = 0
                else:
                    diff = relativedelta(self.date_end, date_init_month)
                    days_bonus = diff.days + 1
            else:
                diff = relativedelta(self.date_end, date_init_month)
                days_bonus = diff.days + 1
            return days_bonus
        else:
            return 0

    def has_christmas_bonus(self, employee_id):
        # Ver si tiene aguinaldo
        date_from_aguinaldo = date(employee_id.departure_date.year, 12, 1)
        date_to_aguinaldo = date(employee_id.departure_date.year, 12, 31)
        structure_one = self.env.ref('l10n_bo_hr_payroll.structure_christmas_bonus')
        structure_two = self.env.ref('l10n_bo_hr_payroll.structure_christmas_bonus_second')
        # Crear el domain para buscar cominas de aguinando en el año de baja
        payroll_domain = [
            ('date_from', '>=', date_from_aguinaldo),
            ('date_to', '<=', date_to_aguinaldo),
            ('employee_id', '=', employee_id.id),
            ('struct_id', '=', structure_one.id),
            ('state', '=', 'paid'),
            ('has_refund_slip', '=', True),
        ]

        # Buscar las nóminas de aguinaldo del mes actual mes actual
        payrolls = self.env['hr.payslip'].search(payroll_domain)
        if payrolls:
            payroll_domain_two = [
                ('date_from', '>=', date_from_aguinaldo),
                ('date_to', '<=', date_to_aguinaldo),
                ('employee_id', '=', employee_id.id),
                ('struct_id', '=', structure_two.id),
                ('state', '=', 'paid'),
                ('has_refund_slip', '=', False),
            ]
            payrolls_two = self.env['hr.payslip'].search(payroll_domain_two)
            if payrolls_two:
                self.has_christmas_bonus_one = True
                self.has_christmas_bonus_two = True
                self.pay_second = False
                return True
            else:
                self.has_christmas_bonus_one = True
                self.has_christmas_bonus_two = False
                return True
        else:
            self.has_christmas_bonus_one = False
            self.has_christmas_bonus_two = False
            self.pay_second = False
            return False
