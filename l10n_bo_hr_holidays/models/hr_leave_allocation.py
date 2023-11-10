# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Copyright (c) 2005-2006 Axelor SARL. (http://www.axelor.com)

from collections import defaultdict
import logging

from datetime import datetime, time
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.addons.resource.models.resource import HOURS_PER_DAY
from odoo.addons.hr_holidays.models.hr_leave import get_employee_from_context
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.translate import _
from odoo.tools.float_utils import float_round
from odoo.tools.date_utils import get_timedelta
from odoo.osv import expression


_logger = logging.getLogger(__name__)


class HolidaysAllocation(models.Model):
    _name = 'hr.leave.allocation'
    _inherit = 'hr.leave.allocation'

    # max_allocated_vacation = fields.Float(related='employee_id.allowed_vacation_days', readonly=True, string='Maximas vacaciones permitidas' )

    @api.model_create_multi
    def create(self, vals_list):
        """ Override to avoid automatic logging of creation """
        for values in vals_list:
            holiday_status_id = values.get('holiday_status_id', False)
            if holiday_status_id and holiday_status_id == 1:
                employee_id = values.get('employee_id', False)
                number_of_days = values.get('number_of_days', False)
                if employee_id:
                    employee_one = self.env['hr.employee'].search([('id', '=', employee_id)], limit=1)
                    if number_of_days > employee_one.allowed_vacation_days:
                        raise UserError(_("El numero de días de vacaciones a planificar es mayor que el permitido al "
                                          "empleado %s.", employee_one.allowed_vacation_days))
                else:
                    employee_all = values.get('employee_ids', False)
                    error = False
                    description = ""
                    for employee_id in employee_all[0][2]:
                        employee_one = self.env['hr.employee'].search([('id', '=', employee_id)], limit=1)
                        if number_of_days > employee_one.allowed_vacation_days:
                            error = True
                            description += employee_one.name + ' ' + str(employee_one.allowed_vacation_days) + ' '
                    if error:
                        raise UserError(_("El numero de días de vacaciones a planificar es mayor que el permitido por "
                                            "empleado %s.", description))
        holidays = super(HolidaysAllocation, self.with_context(mail_create_nosubscribe=True)).create(vals_list)
        return holidays

    def write(self, values):
        employee_id = values.get('employee_id', False)
        if not employee_id:
            employee_id = self.employee_id.id
        employee_all = values.get('employee_ids', False)
        if not employee_all:
            employee_all = lista = [[6, False, [employee.id for employee in self.employee_ids]]]
        number_of_days = values.get('number_of_days', False)
        if not number_of_days:
            number_of_days = self.number_of_days
        if employee_id:
            employee_one = self.env['hr.employee'].search([('id', '=', employee_id)], limit=1)
            if self.holiday_status_id and self.holiday_status_id.id == 1:
                if number_of_days > employee_one.allowed_vacation_days:
                    raise UserError(_("El numero de días de vacaciones a planificar es mayor que el permitido al "
                                      "empleado %s.", employee_one.allowed_vacation_days))
        else:
            error = False
            description = ""
            for employee_id in employee_all[0][2]:
                employee_one = self.env['hr.employee'].search([('id', '=', employee_id)], limit=1)
                if number_of_days > employee_one.allowed_vacation_days:
                    error = True
                    description += employee_one.name + ' ' + str(employee_one.allowed_vacation_days) + ' '
            if error:
                raise UserError(_("El numero de días de vacaciones a planificar es mayor que el permitido por "
                                  "empleado %s.", description))

        if values.get('state'):
            self._check_approval_update(values['state'])
        result = super(HolidaysAllocation, self).write(values)
        self.add_follower(employee_id)
        return result