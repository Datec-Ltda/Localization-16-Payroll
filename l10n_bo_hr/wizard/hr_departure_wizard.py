# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class HrDepartureWizard(models.TransientModel):
    _inherit = 'hr.departure.wizard'

    pay_in = fields.Selection(
        string='Pago en',
        selection=[('chk', 'Cheque'), ('ef', 'Efectivo')]
    )

    bank_id = fields.Many2one('res.bank', string='Banco')

    date_of_pay = fields.Date(string='Fecha de pago',  default=fields.Date.context_today, )

    def action_register_departure(self):
        employee = self.employee_id
        if self.env.context.get('toggle_active', False) and employee.active:
            employee.with_context(no_wizard=True).toggle_active()
        employee.departure_reason_id = self.departure_reason_id
        employee.departure_description = self.departure_description
        employee.departure_date = self.departure_date
        employee.pay_in = self.pay_in
        employee.bank_id = self.bank_id
        employee.date_of_pay = self.date_of_pay

        if self.archive_private_address:
            # ignore contact links to internal users
            private_address = employee.address_home_id
            if private_address and private_address.active and not self.env['res.users'].search([('partner_id', '=', private_address.id)]):
                private_address.sudo().toggle_active()
