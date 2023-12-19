# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

MES_LITERAL = [('1', 'Enero'),
               ('2', 'Febrero'),
               ('3', 'Marzo'),
               ('4', 'Abril'),
               ('5', 'Mayo'),
               ('6', 'Junio'),
               ('7', 'Julio'),
               ('8', 'Agosto'),
               ('9', 'Septiembre'),
               ('10', 'Octubre'),
               ('11', 'Noviembre'),
               ('12', 'Diciembre')]


class HrPlanWizard(models.TransientModel):
    _name = 'hr.payments.wizard'
    _description = 'Payments Wizard'

    month_pay = fields.Selection(
        string='Mes',
        selection=MES_LITERAL,
        required=True, default='1')

    def action_generate(self):
        # TODO Nota que esto hay que hacerlo para cada mes
        #  lo ideal es hacer un cilclo
        #  for mes in meses
        #    hacer lo que esta explicacion de abajo
        # la variable meses puede ser una lista de dicionario con las fechas
        # meses = {'mes': 'enero', 'date_start': '2023-01-01', 'date_end': '2023-01-31'},
        #         {'mes': 'febrero', 'date_start': '2023-02-01', 'date_end': '2023-02-28'}, etc...

        # Esto no es nesesario pero para que quede organizado en lotes
        # puede ser bueno poner tambien en este modelo una marca para saber que son lotes de nominas rectroactiva
        # por si guiere ocultarla o hacer una opción que solo muestre este tipo de nomina
        # o para ocultar el botón de contabilizar etc..
        values = {'name': 'Nómina rectroactiva de enero', 'date_start': '2023-01-01', 'date_end': '2023-01-31'}
        payslip_run_id = self.env['hr.payslip.run'].create(values)

        # Obtenga los datos de la nómina
        # aqui quisas tengas que adicionar una nueva condicion al domain
        # como la structura
        domain = [('date_from', '>=', '2023-01-01'), ('date_to', '<=', '2023-01-31')]
        payroll_january = self.env['hr.payslip'].search(domain)

        # Cree una copia de la nómina
        # la ventaja de hacerlo con el copy es que trae toda la informacion
        # ademas los campos que no se deben de duplicar deben tener el parametro
        # copy=False, eso ya odoo lo debe tener, o sea si el copy te da error de que x campo debe
        # ser un campo unico solo debes poner copy=False a ese campo y luego en el ciclo poner el nuevo valor
        payroll_january.with_context(retroactive=True, basic_percent=5, smn_percent=4).compute_sheet()
        # payroll_january_retro = payroll_january.copy()

        # Modificar la copia de la nómina de enero para reflejar los cambios en el salario de los empleados
        # for payslip in payroll_january_retro:
            # aqui poner el nombre de la nomina y demas datos
            # como marcar que es una nomina de pago rectroactivo etc..
        #     payslip.name = 'nombre de la nomina'
        #     payslip.payslip_run_id = payslip_run_id
        #
        #     for line in payslip.line_ids:
        #         if line.code == 'BASIC':
        #             # TODO aqui poner el nuevo valor que supongo se debe coger del alguna parte ejemplo el contrato
        #             nuevo = payslip.contract_id.wage
        #             line.amount = nuevo
        #         # if line.code == 'OTRO_CONCEPTO':
        #         #     line.amount = nuevo_valor
        #
        # # Calcule la nómina de los empleados con el salario actualizado
        # payroll_january_retro.with_context(retroactive=True).compute_sheet()
        # payroll_january_retro.compute_sheet()


    # @api.depends('month_pay', 'employee_id')
    # def _compute_payments_ids(self):
    #     for history in self:
    #         domain = [('month_pay', '=', history.month_pay), ('employee_id', '=', history.employee_id.id)]
    #         history.payments_ids = self.env['hr.employee.payments'].search(domain)