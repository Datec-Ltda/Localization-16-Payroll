from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero
import time
from datetime import datetime, timedelta
from dateutil import relativedelta
from odoo.exceptions import UserError, ValidationError

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


class PayrollEmployeePaymentsRetroactive(models.Model):
    _name = 'hr.payroll.employee.payments.retroactive'
    _description = 'Pagos retroactivos'

    basic_percent = fields.Float(string='Porciento de incremento del salario basico')
    smn_percent = fields.Float(string='Porciento de incremento del salario minimo nacional')

    month_init_pay = fields.Selection(
        string='Mes inicio de pago',
        selection=MES_LITERAL,
        required=True, default='1')

    def _get_comp_domain(self):
        if self.env.user.company_ids.ids:
            return ['|', ('parent_id', '=', False), ('parent_id', 'child_of', self.env.user.company_id.id)]
        return []
    domain = _get_comp_domain

    company_id = fields.Many2one('res.company', domain=domain,
                                 string='Company', required=True,
                                 default=lambda self: self.env['res.company']._company_default_get())

    date_from = fields.Date(string='Date From', readonly=True, required=True,
                            default=time.strftime('%Y-%m-01'),
                            states={'draft': [('readonly', False)], 'open': [('readonly', False)]})
    date_to = fields.Date(string='Date To', readonly=True, required=True,
                          default=str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],
                          states={'draft': [('readonly', False)], 'open': [('readonly', False)]})

    @api.onchange('date_from')
    def onchange_name(self):
        if self.date_from:
            ttyme = datetime.fromtimestamp(time.mktime(self.date_from.timetuple()))
            self.name = _('Pago retroactivo para %s') % (tools.ustr(ttyme.strftime('%B-%Y')))

    name = fields.Char(string='Name', readonly=True, required=True,
                       states={'draft': [('readonly', False)]})

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('contract', 'Contrato Generado'),
        ('generated', 'Pago generado'),
        ('open', 'Abierto'),
        ('closed', 'Cerrado'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft')

    def action_period_draft(self):
        self.write({'state': 'draft'})
        for record in self.payment_retroactive_ids:
            if record.state != 'closed':
                record.write({'state': 'draft'})

        contract_env = self.env['hr.contract']
        for record in self.payment_retroactive_contract_ids:
            new_contract = contract_env.search([
                ('id', '=', record.new_contract_id.id),
            ])
            if new_contract:
                try:
                    # 1. Buscar y eliminar las entradas de trabajo asociadas al contrato
                    work_entries = self.env['hr.work.entry'].search([('contract_id', '=', new_contract.id)])
                    work_entries.unlink()
                    new_contract.unlink()  # Intenta eliminar el contrato
                    # Si se elimina quitarle al anterior la fecha de fin y ponerlo en Ejecución
                    old_contract = contract_env.search([
                        ('id', '=', record.old_contract_id.id),
                    ])
                    old_contract.write({'date_end': False, 'state': 'open'})
                    # Si se elimina correctamente, quitarlo de la lista
                    record.unlink()
                except Exception as e:
                    # Si hay un error, registrar el comentario en el campo de comentarios
                    record.comments += f"Error al eliminar contrato {new_contract.id}: {str(e)}\n"
        return True

    def action_period_contract(self):
        self.write({'state': 'contract'})
        for record in self.payment_retroactive_ids:
            if record.state != 'closed':
                record.write({'state': 'contract'})
        return True

    def action_period_generated(self):
        self.write({'state': 'generated'})
        for record in self.payment_retroactive_ids:
            if record.state != 'closed':
                record.write({'state': 'generated'})
        return True

    def action_period_open(self):
        self.write({'state': 'open'})
        for record in self.payment_retroactive_ids:
            if record.state != 'closed':
                record.write({'state': 'open'})
        return True

    def action_period_closed(self):
        self.write({'state': 'closed'})
        self.payment_retroactive_ids.write({'state': 'closed'})
        return True

    payment_retroactive_ids = fields.One2many(
        comodel_name='hr.payroll.employee.payments.retroactive.list',
        inverse_name='payment_retroactive_id',
    )

    payment_retroactive_contract_ids = fields.One2many(
        comodel_name='hr.payroll.employee.payments.retroactive.contract.list',
        inverse_name='payment_retroactive_id',
    )

    def get_periodo_retroactive_pay(self):
        # Obtener el número de mes seleccionado
        selected_month = int(self.month_init_pay)

        # Crear un objeto de fecha para el primer día del mes seleccionado
        start_date = datetime(year=2023, month=selected_month, day=1).date()

        # Iterar sobre los meses hasta la fecha de procesamiento
        months = []
        while start_date < self.date_from:
            # Obtener el nombre del mes
            month_name = start_date.strftime('%B').lower()

            # Obtener la fecha de fin del mes
            end_date = start_date.replace(day=1, month=start_date.month % 12 + 1) - timedelta(days=1)

            # Agregar el mes al diccionario
            months.append({
                'mes': month_name,
                'date_start': start_date.strftime('%Y-%m-%d'),
                'date_end': end_date.strftime('%Y-%m-%d')
            })

            # Avanzar al siguiente mes
            start_date = start_date.replace(day=1, month=start_date.month % 12 + 1)

        return months

    def execute_retroactive_pay(self):
        months = []
        months = self.get_periodo_retroactive_pay()

        # Recorrer el diccionario
        for month in months:
            end_contrat = self.date_from - timedelta(days=1)
            # Los contratos que se pasaron a estado cerrado con la fecha final igual a un dia antes
            # de la fecha de inicio del procesamiento de retroactivo
            domain = [
                ('state', '=', 'close'),
                ('date_end', '=', end_contrat),
            ]
            # Buscar los empleados con contratos en estado "En proceso" para el mes actual
            employees = self.env['hr.contract'].search(domain).mapped('employee_id')

            structure = self.env.ref('l10n_bo_hr_payroll.structure_month')
            # Crear el domain para buscar las nóminas del mes actual
            payroll_domain = [
                ('date_from', '>=', month['date_start']),
                ('date_to', '<=', month['date_end']),
                ('employee_id', 'in', employees.ids),
                ('struct_id', '=', structure.id),
                ('state', '=', 'paid'),
            ]

            # Buscar las nóminas del mes actual
            payrolls = self.env['hr.payslip'].search(payroll_domain)

            # Ejecutar el procesamiento de las nóminas
            # payroll.with_context(retroactive=True, basic_percent=self.basic_percent, smn_percent=self.smn_percent).compute_sheet()
            for payroll in payrolls:
                result = payroll.with_context(retroactive=True, basic_percent=self.basic_percent,
                                         smn_percent=self.smn_percent).compute_sheet()

            # Agregar la información relevante al modelo hr.payroll.employee.payments.retroactive.list
            retroactive_list = self.env['hr.payroll.employee.payments.retroactive.list'].search([
                ('employee_id', 'in', employees.ids),
                ('payment_retroactive_id', '=', self.id)
            ])

            for payroll in payrolls:
                if not retroactive_list.filtered(lambda r: r.employee_id == payroll.employee_id):
                    retroactive_list.create({
                        'payment_retroactive_id': self.id,
                        'name': 'Nombre del pago retroactivo',
                        'date_from': self.date_from,
                        'date_to': self.date_to,
                        'employee_id': payroll.employee_id.id,
                        'contract_id': payroll.employee_id.contract_id.id,
                        'slip_ids': [(6, 0, payroll.filtered(lambda p: p.employee_id == payroll.employee_id).ids)]
                    })
                else:
                    retroactive_list.filtered(lambda r: r.employee_id == payroll.employee_id).write({
                         'slip_ids': [(4, slip.id) for slip in payroll.filtered(lambda p: p.employee_id == payroll.employee_id)]
                })
        self.action_period_generated()
        return True

    def create_new_contract(self):
        end_contrat = self.date_from - timedelta(days=1)
        contract_domain = [
            ('state', '=', 'open'),
            ('date_end', '=', False),
            ('date_start', '<', end_contrat),
            ]
        end_contrat = self.date_from - timedelta(days=1)
        contracts_in_progress = self.env['hr.contract'].search(contract_domain)
        for contract in contracts_in_progress:
            # Crear una copia del contrato con fecha de inicio modificada y salario cambiado
            new_contract = contract.copy(default={'name': contract.name + ' ' + str(self.date_from),
                                                'date_start': self.date_from,
                                                  'wage': contract.wage + contract.wage * self.basic_percent / 100})

            # Actualizar el contrato existente
            contract.write({'date_end': end_contrat, 'state': 'close'})
            # actualizar el estado del nuevo contrato
            new_contract.write({'state': 'open'})
            # Guardar datos de los contratos modificados
            domain_contract_mov = [
                ('employee_id', '=', contract.employee_id.id),
                ('old_contract_id', '=', contract.id),
                ('new_contract_id', '=', new_contract.id),
            ]

            contract_retroactive_env =  self.env['hr.payroll.employee.payments.retroactive.contract.list']
            contracts_move = contract_retroactive_env.search(domain_contract_mov)
            if not contracts_move:
                value = {
                    'payment_retroactive_id': self.id,
                    'name': contract.employee_id.name,
                    'employee_id': contract.employee_id.id,
                    'old_contract_id': contract.id,
                    # 'old_wage': contract.wage,
                    'new_contract_id': new_contract.id,
                    # 'new_wage': new_contract.wage,
                }
                contract_retroactive_env.create(value)
        self.action_period_contract()
        return True


class PayrollEmployeePaymentsRetroactiveList(models.Model):
    _name = 'hr.payroll.employee.payments.retroactive.list'
    _description = 'Pago retroactivo nóminas'

    name = fields.Char(string='Name', readonly=True, required=True,
                       states={'draft': [('readonly', False)]})

    payment_retroactive_id = fields.Many2one('hr.payroll.employee.payments.retroactive', ondelete="cascade")

    slip_ids = fields.One2many('hr.payslip', 'payslip_retroactive_id', string='Payslips', readonly=True,
                               states={'draft': [('readonly', False)]})

    employee_id = fields.Many2one('hr.employee', readonly=True)
    contract_id = fields.Many2one(related='employee_id.contract_id', string="contract employee")

    month_init_pay = fields.Selection(
        string='Mes inicio de pago',
        selection=MES_LITERAL,
        required=True, default='1')

    date_from = fields.Date(string='Date From', readonly=True, required=True,
                            default=time.strftime('%Y-%m-01'),
                            states={'draft': [('readonly', False)], 'open': [('readonly', False)]})
    date_to = fields.Date(string='Date To', readonly=True, required=True,
                          default=str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],
                          states={'draft': [('readonly', False)], 'open': [('readonly', False)]})

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('contract', 'Contrato Generado'),
        ('generated', 'Pago generado'),
        ('open', 'Abierto'),
        ('closed', 'Cerrado'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft')
    company_id = fields.Many2one('res.company', string='Company', readonly=True, copy=False,
                                 default=lambda self: self.env['res.company']._company_default_get(),
                                 states={'draft': [('readonly', False)]})

    def action_period_draft(self):
        self.write({'state': 'draft'})
        return True

    def action_period_contract(self):
        self.write({'state': 'contract'})
        return True

    def action_period_open(self):
        self.write({'state': 'open'})
        return True

    def action_period_closed(self):
        self.write({'state': 'closed'})
        return True

    def unlink(self):
        for line in self:
            if line.state != 'generated':
                raise UserError(
                    _('No puede borrar el registro si no esta en estado contractos realizados.')
                )
        return super(PayrollEmployeePaymentsRetroactiveList, self).unlink()


class PayrollEmployeePaymentsRetroactiveContractList(models.Model):
    _name = 'hr.payroll.employee.payments.retroactive.contract.list'
    _description = 'Contratos y salarios'

    name = fields.Char(string='Name')

    payment_retroactive_id = fields.Many2one('hr.payroll.employee.payments.retroactive', ondelete="cascade")

    employee_id = fields.Many2one('hr.employee', readonly=True)
    old_contract_id = fields.Many2one('hr.contract', string="Contrato anterior")
    currency_id = fields.Many2one('res.currency', string='Currency')
    old_wage = fields.Monetary(related='old_contract_id.wage', string='Salario anterior', currency_field='currency_id')
    old_date_start = fields.Date(related='old_contract_id.date_start', string='Fecha inicio')
    old_date_end = fields.Date(related='old_contract_id.date_end', string='Fecha fin')
    new_contract_id = fields.Many2one('hr.contract', string="Contrato nuevo")
    new_wage = fields.Monetary(related='new_contract_id.wage', string='Salario actual', currency_field='currency_id')
    new_date_start = fields.Date(related='new_contract_id.date_start', string='Fecha inicio')

    comments = fields.Text(string='Comments')