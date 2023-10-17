# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from datetime import date
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    type_identification_document = fields.Selection([
        ('01', 'Cédula de identidad'),
        ('02', 'Licencia de Conducir'),
        ('03', 'Código de Dependiente')],
        string='Clase de documento', default='01')

    valid_date = fields.Date(string='Fecha de validez')

    document_number = fields.Char(string="Numero de documento")

    document_extension = fields.Selection([
        ('SC', 'SC Santa Cruz'),
        ('CB', 'CB Cochabamba ')],
        string='Extensión de documento', default='SC')

    # Datos de la AFP
    
    afp_id = fields.Many2one('res.partner', string='Administradora de fondo de penciones',
                             domain=[('l10n_bo_afp', '=', True)])
    afp_code = fields.Char(related='afp_id.l10n_bo_afp_code', readonly=True, string="Código")
    afp_nua_cua = fields.Char(string="NUA/CUA")
    aft_quotation_type = fields.Many2one('hr.aft.quotation.type', 'Tipo de Cotización')
    monthly_quotation = fields.Float(string="Cotización mensual ", compute="_get_monthly_quotation", store=True)

    @api.depends('aft_quotation_type')
    def _get_monthly_quotation(self):
        for record in self:
            if record.aft_quotation_type:
                details = self.env['hr.aft.quotation.type.details'].search([('code', '=', 'cm'), ('aft_quotation_type_id', '=', record.aft_quotation_type.id)])
                if details:
                    record.monthly_quotation = details.percent
                else:
                    record.monthly_quotation = 0

    common_risk_premium = fields.Float(string="Prima riesgo común", compute="get_common_risk_premium", store=True)

    @api.depends('aft_quotation_type')
    def get_common_risk_premium(self):
        for record in self:
            if record.aft_quotation_type:
                details = self.env['hr.aft.quotation.type.details'].search([('code', '=', 'prc'), ('aft_quotation_type_id', '=', record.aft_quotation_type.id)])
                if details:
                    record.common_risk_premium = details.percent
                else:
                    record.common_risk_premium = 0

    solidarity_contribution = fields.Float(string="Aporte solidario", compute="get_solidarity_contribution", readonly=True, store=True)

    @api.depends('aft_quotation_type')
    def get_solidarity_contribution(self):
        for record in self:
            if record.aft_quotation_type:
                details = self.env['hr.aft.quotation.type.details'].search([('code', '=', 'as'), ('aft_quotation_type_id', '=', record.aft_quotation_type.id)])
                if details:
                    record.solidarity_contribution = details.percent
                else:
                    record.solidarity_contribution = details.percent

    afp_commission = fields.Float(string="Comisión AFP", compute="get_afp_commission", readonly=True, store=True)

    @api.depends('aft_quotation_type')
    def get_afp_commission(self):
        for record in self:
            if record.aft_quotation_type:
                details = self.env['hr.aft.quotation.type.details'].search([('code', '=', 'c_afp'), ('aft_quotation_type_id', '=', record.aft_quotation_type.id)])
                if details:
                    record.afp_commission = details.percent
                else:
                    record.afp_commission = details.percent

    afp_retired = fields.Boolean(
        'Jubilado', help='Para identificar que el empleado esta jubilado', default=False)
    afp_retired_date = fields.Date(string='Retire date',
                                   help='Identifica la fecha en que se jubila el empleado')
    current_date = fields.Date(string='Current date', default=datetime.now().strftime('%Y-%m-%d'))
    afp_age_str = fields.Char(string="Edad", readonly=True, compute='_compute_age', store=True)
    afp_age = fields.Integer('Años')
    afp_age_months = fields.Integer(string="Meses")
    afp_age_days = fields.Integer(string="Días")

    give_aft = fields.Boolean(
        string='Aporta AFT',help='Para idientificar que el empleado jubilado aporta AFT', default=False
    )

    @api.depends('birthday', 'current_date')
    def _compute_age(self):
        for rec in self:
            if rec.birthday:
                # db_day = datetime.strptime(rec.birthday, DEFAULT_SERVER_DATE_FORMAT).date()
                db_day = rec.birthday
                db_today = datetime.now().date()
                diff = relativedelta(db_today, db_day)
                rec.afp_age = diff.years
                rec.afp_age_months = diff.months
                rec.afp_age_days = diff.days
                rec.afp_age_str = str(rec.afp_age) + ' años ' + str(rec.afp_age_months) + ' meses ' + str(rec.afp_age_days) + ' días'
                # rec.age = dToday.year - dBday.year - ((dToday.month, dToday.day) < (dBday.month, dBday.day))

    earned_average = fields.Float(string='Earned Average',
                                  help='Campo calculado promedio sobre el total ganado de los 3 meses ',
                                  required=False
                                  )

    paid_percentage = fields.Float(string='Paid Percentage',
                                   help='Porcentaje a pagar de prima',
                                   required=False
                                   )

    days_considered = fields.Integer(string='Days considered',
                                     help='Días trabajados en la gestión a pagar por el cual se paga el monto de prima',
                                     required=False
                                     )

    amount_paid = fields.Float(string='Amount paid',
                               help='Campo calculado del monto de prima pagado para la gestión',
                               required=False
                               )

    attachment_ids = fields.One2many('l10n_bo_hr.employee_docs', 'employee_id')

    pay_in = fields.Selection(
        string='Pay in',
        selection=[('chk', 'Cheque'), ('ef', 'Efectivo')]
    )

    bank_id = fields.Many2one('res.bank', string='Bank')

    date_of_pay = fields.Date(string='Date of pay',
                                default=fields.Date.context_today,
                            )
    # Asignación organizativa
    staff_division_id = fields.Many2one('hr.employee.staff.division', string='División de personal')
    staffing_subdivision_id = fields.Many2one('hr.employee.staffing.subdivision', string='SubDivisión de personal', domain="[('division_id', '=', staff_division_id)]")
    personnel_group_id = fields.Many2one('hr.employee.personnel.group', string='Grupo de personal')
    personnel_area_id = fields.Many2one('hr.employee.personnel.area', string='Área de personal', domain="[('personnel_group_id', '=', personnel_group_id)]")
    payroll_area_id = fields.Many2one('hr.employee.payroll.area', string='Área de nómina')

    # Datos salud
    health_box_id = fields.Many2one('res.partner', string='Seguro de la caja de salud',
                             domain=[('l10n_bo_health_box', '=', True)])
    health_box_code = fields.Char(related='health_box_id.l10n_bo_health_box_code', readonly=True, string="Código")

    insured_number = fields.Char(string="Número de Asegurado")
    
    # Datos de la cuenta

    currency_id = fields.Many2one(related='bank_account_id.currency_id', readonly=True, string="Moneda de pago")
    payment_method = fields.Selection([
        ('T', 'Tranferencia bancaria'),
        ('C', 'Cheque'),
        ('E', 'Efectivo')],
        string='Metodo de pago', default='T')

    # Datos de discapacidad
    disabled = fields.Boolean(
        string='Discapacitado',
    )
    tutor_disabled = fields.Boolean(
        string='Tutor de Discapacitado',
    )
class HrAftQuotationType(models.Model):
    _name = "hr.aft.quotation.type"
    _description = "Tipo de cotización"
    _rec_name = 'description'

    code = fields.Char('Código', required=True)
    name = fields.Char(string="Tipo cotización", translate=True, required=True)
    percent = fields.Float("Porciento")
    description = fields.Char(string="Descripción", readonly=True, compute='_compute_description', store=True)

    aft_quotation_type_details_ids = fields.One2many(
        comodel_name='hr.aft.quotation.type.details',
        inverse_name='aft_quotation_type_id',
    )

    @api.depends('code', 'name')
    def _compute_description(self):
        code = ''
        name = ''
        for rec in self:
            if rec.code:
                code = rec.code
            if rec.name:
                name = rec.name
            rec.description = code + ' ' + name


class HrAftQuotationTypeDetails(models.Model):
    _name = "hr.aft.quotation.type.details"
    _decription = "HrAftQuotationTypeDetails"
    code = fields.Char('Código', required=True)
    name = fields.Char(string="Desglose AFP", translate=True, required=True)
    percent = fields.Float("Porciento")
    aft_quotation_type_id = fields.Many2one('hr.aft.quotation.type', ondelete="cascade")


