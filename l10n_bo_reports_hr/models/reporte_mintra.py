from odoo import _, models, fields, api
from odoo.exceptions import UserError
import requests
import logging
import json

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    is_retired = fields.Boolean("Retirado", compute="_compute_is_retired", store=False)
    has_disability = fields.Boolean(
        "Discapacidad",
        help="Indica si el empleado tiene alguna discapacidad",
        default=False,
    )
    disability_tutor = fields.Boolean(
        "Tutor de discapacidad",
        help="Indica si el empleado es tutor de una persona con discapacidad",
        default=False,
    )
    laboral_clasication = fields.Selection(
        [
            ("1", "Ocupaciones de dirección en la administración pública y empresas."),
            ("2", "Ocupaciones de profesionales científicos e intelectuales."),
            ("3", "Ocupaciones de técnicos y profesionales de apoyo."),
            ("4", "Empleados de oficina."),
            ("5", "Trabajadores de los servicios y vendedores del comercio."),
            (
                "6",
                "Productores y trabajadores en la agricultura, pecuaria, agropecuaria y pesca.",
            ),
            (
                "7",
                "Trabajadores de la industria extractiva, construcción, industria manufacturera y otros oficios.",
            ),
            ("8", "Operadores de instalaciones y maquinarias."),
            ("9", "Trabajadores no calificados."),
            ("10", "Fuerzas armadas."),
        ],
        string="Clasificación Laboral",
    )

    def _compute_is_retired(self):
        for employee in self:
            employee.is_retired = employee.contract_id.state == "close"


class HrPayrollMintraWizard(models.TransientModel):
    _name = "hr.payroll.mintra.wizard"

    name = fields.Char("Nombre", default="Reporte mintra")
    doc_type = fields.Selection(
        [
            ("pdf", "PDF"),
            ("csv", "CSV"),
        ]
    )
    month = fields.Selection(
        [
            ("01", "Enero"),
            ("02", "Febrero"),
            ("03", "Marzo"),
            ("04", "Abril"),
            ("05", "Mayo"),
            ("06", "Junio"),
            ("07", "Julio"),
            ("08", "Agosto"),
            ("09", "Septiembre"),
            ("10", "Octubre"),
            ("11", "Noviembre"),
            ("12", "Diciembre"),
        ],
        string="Mes",
        default="01",
    )
    year = fields.Char("Año", default="2021")

    @api.onchange("month", "year")
    def _onchange_month_year(self):
        if self.year and self.month:
            self.name = f"Reporte mintra {self.month}/{self.year}"

    @api.model
    def _onchange_year(self):
        if not self.year.isdigit():
            raise UserError(_("El año debe ser un número"))

    def action_generate_mintra(self):
        data = self.generate_data()
        url = f"{self.env.user.company_id.url_report_service}/process"
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            json_response = response.json()
            base64_doc = json_response['data']['document']
            attachment = self.env['ir.attachment'].create({
                'name': f"Reporte Mintra {self.month}/{self.year}",
                'type': 'binary',
                'datas': base64_doc,
                'store_fname': f"Reporte Mintra {self.month}/{self.year}.csv",
                'res_model': 'hr.payroll.mintra.wizard',
                'res_id': self.id,
            })
            # Return the attachment to download it
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/{attachment.id}?download=true',
                'target': 'self',
            }
        else:
            raise UserError(_("Error al generar el reporte mintra"))

    def generate_data(self):
        employee_ids = self.get_employee_ids()
        employee_data = []
        index = 1
        for employee in employee_ids:
            employee_data.append(self.employee_mintra_data(employee, position=index))
            index += 1
        data = json.dumps({
            "extension": 'csv',
            "report": "mintra",
            "data": employee_data
        })
        # url = ""
        # headers = {"Content-Type": "application/json"}
        # response = requests.post(url, headers=headers, data=data)
        # if response.status_code == 200:
        #     return response.content
        # else:
        #     raise UserError(_("Error al generar el reporte mintra"))
        return data

    def get_employee_ids(self):
        return self.env["hr.employee"].search([("active", "=", True)])

    def _bool_to_number(self, value):
        return 1 if value else 0

    def employee_mintra_data(self, employee, position=0):
        employee_data = {
            "code": position,
            "personal_number": employee.id,
            "document_type": employee.address_id.l10n_bo_document_type or "ci",
            "document_number": employee.address_id.vat or "0",
            "expedition_city": employee.address_id.l10n_bo_document_city_id.name or "",
            "date_of_birth": (
                employee.birthday.strftime("%d/%m/%Y") if employee.birthday else ""
            ) or "",
            "last_name": employee.lastname or "",
            "mother_last_name": employee.lastname2 or "",
            "first_name": f"{employee.firstname} {employee.firstname2}".strip() or "",
            "nationality": employee.country_id.name or "",
            "gender": employee.gender or "",
            "retired": self._bool_to_number(employee.is_retired),
            "contributes_to_afp": self._bool_to_number(employee.afp_code),
            "disabled": self._bool_to_number(employee.has_disability),
            "disability_tutor": self._bool_to_number(employee.disability_tutor),
            "date_of_entry": (
                employee.date_hired.strftime("%d/%m/%Y") if employee.date_hired else ""
            ),
            "date_of_exit": (
                employee.contract_id.date_end.strftime("%d/%m/%Y")
                if employee.contract_id.date_end
                else ""
            ),
            "reason_for_exit": employee.contract_id.notes or "",
            "health_box": employee.health_box_id.id or 0,
            "afp_contributing": self._bool_to_number(employee.afp_code is not False),
            "membership_number": int(employee.afp_nua_cua) or 0,
            "branch_number": employee.company_id.id or 0,
            "laboral_clasication": employee.laboral_clasication or "",
            "job_name": employee.job_id.name if employee.job_id else "",
            "contract_type": employee.contract_id.contract_type_id.id if employee.contract_id.contract_type_id else 0,
            "contract_type_format": 1,
            "payed_days": 30,
            "payed_hours": employee.contract_id.structure_type_id.default_resource_calendar_id.full_time_required_hours,
            "salary": employee.contract_id.wage,
            "antiquity_bonus": 0,
            "extra_hours_total_time": 0,
            "extra_hours_total_amount": 0,
            "extra_hours_night_time": 0,
            "extra_hours_night_amount": 0,
            "extra_hours_dominical_time": 0,
            "extra_hours_dominical_amount": 0,
            "total_dominical": 0,
            "worked_sunday_total": 0,
            "worked_sunday_amount": 0,
            "worked_sundsay_salary": 0,
            "productive_bonus": 0,
            "frontier_bonus": 0,
            "other_bonuses": 0,
            "tax_discount": 0,
            "health_box_discount": 0,
            "afp_discount": 0,
            "other_discounts": 0,
        }
        return employee_data


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def compute_extra_hours_total_time(self, date_from, date_to):
        self.ensure_one()
        payroll_time_model = self.env['hr.payroll.overtime.hours.list']
        overtime_hours = payroll_time_model.search([
            ('employee_id', '=', self.id),
            ('date', '>=', date_from),
            ('date', '<=', date_to),
        ])