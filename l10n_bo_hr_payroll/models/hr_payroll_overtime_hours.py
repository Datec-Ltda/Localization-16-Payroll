# -*- coding:utf-8 -*-

from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero
import time
from datetime import datetime, timedelta
from dateutil import relativedelta
from odoo.exceptions import UserError, ValidationError


class HrPayrollOvertimeHours(models.Model):
    _name = 'hr.payroll.overtime.hours'
    _description = 'Horas extras'

    def _get_comp_domain(self):
        if self.env.user.company_ids.ids:
            return ['|', ('parent_id', '=', False), ('parent_id', 'child_of', self.env.user.company_id.id)]
        return []
    domain = _get_comp_domain

    company_id = fields.Many2one('res.company', domain=domain,
                                 string='Company', required=True,
                                 default=lambda self: self.env['res.company']._company_default_get())

    @api.onchange('date_from', 'date_to')
    def onchange_name(self):
        if self.date_from and self.date_to:
            ttyme = datetime.fromtimestamp(time.mktime(self.date_from.timetuple()))
            self.name = _('Horas extras para %s') % (tools.ustr(ttyme.strftime('%B-%Y')))

    name = fields.Char(string='Name', readonly=True, required=True,
                       states={'draft': [('readonly', False)]})

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('open', 'Abierto'),
        ('closed', 'Cerrado'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft')

    date_from = fields.Date(string='Date From', readonly=True, required=True,
                            default=time.strftime('%Y-%m-01'),
                            states={'draft': [('readonly', False)], 'open': [('readonly', False)]})
    date_to = fields.Date(string='Date To', readonly=True, required=True,
                          default=str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],
                          states={'draft': [('readonly', False)], 'open': [('readonly', False)]})

    def action_period_draft(self):
        self.write({'state': 'draft'})
        for record in self.overtime_hours_ids:
            if record.state != 'closed':
                record.write({'state': 'draft'})
        return True

    def action_period_open(self):
        self.write({'state': 'open'})
        for record in self.overtime_hours_ids:
            if record.state != 'closed':
                record.write({'state': 'open'})
        return True

    def action_period_closed(self):
        self.write({'state': 'closed'})
        self.overtime_hours_ids.write({'state': 'closed'})
        return True

    overtime_hours_ids = fields.One2many(
        comodel_name='hr.payroll.overtime.hours.list',
        inverse_name='overtime_hours_id',
    )

    def option_remove(self):
        self.env['hr.payroll.overtime.hours.list'].search(
            [('company_id', '=', self.company_id.id), ('date_from', '=', self.date_from),
             ('date_to', '=', self.date_to), ('state', '=', 'draft')]).unlink()

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        """ make sure date_from < date_to"""

        for rec in self:
            if rec.date_from and rec.date_to:
                if rec.date_from > rec.date_to:
                    raise ValidationError(_('Intervalo invalido.'))
                clause_1 = ['&', ('date_to', '<=', rec.date_to), ('date_to', '>=', rec.date_from)]
                # OR if it starts between the given dates
                clause_2 = ['&', ('date_from', '<=', rec.date_to), ('date_from', '>=', rec.date_from)]
                # OR if it starts before the date_from and finish after the date_end
                clause_3 = ['&', ('date_from', '<=', rec.date_from),('date_to', '>=', rec.date_to)]
                clause_final = [('id', '!=', rec.id)] + clause_1 + clause_2 + clause_3
                overlaps = self.search(clause_final).ids
                if len(overlaps) > 0:
                    raise ValidationError(_('Existe intervalo.'))


class HrPayrollOvertimeHoursList(models.Model):
    _name = 'hr.payroll.overtime.hours.list'
    _description = 'Horas extras List'

    overtime_hours_id = fields.Many2one('hr.payroll.overtime.hours', ondelete="cascade")
    payslip_id = fields.Many2one('hr.payslip')
    number = fields.Char(related='payslip_id.number', readonly=False, tracking=True)
    employee_id = fields.Many2one('hr.employee','Employee', required=True)
    contract_id = fields.Many2one('hr.contract', 'Contract', required=True)
    date_from = fields.Date(string='Date From', readonly=True, required=True,
                            default=time.strftime('%Y-%m-01'),
                            states={'draft': [('readonly', False)], 'open': [('readonly', False)]})
    date_to = fields.Date(string='Date To', readonly=True, required=True,
                          default=str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],
                          states={'draft': [('readonly', False)], 'open': [('readonly', False)]})
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('open', 'Abierto'),
        ('closed', 'Cerrado'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft')
    company_id = fields.Many2one('res.company', string='Company', readonly=True, copy=False,
                                 default=lambda self: self.env['res.company']._company_default_get(),
                                 states={'draft': [('readonly', False)]})
    overtime = fields.Integer('Horas extras', default=0.0)
    hours_night_overtime = fields.Integer('Horas Recargo nocturno', default=0.0)
    sunday_overtime = fields.Integer('Horas Extra Dominical', default=0.0)
    sunday_worked = fields.Integer('Domingos Trabajados', default=0.0)

    def action_period_draft(self):
        self.write({'state': 'draft'})
        return True

    def action_period_open(self):
        self.write({'state': 'open'})
        return True

    def action_period_closed(self):
        self.write({'state': 'closed'})
        return True