from odoo import _, models, fields
from odoo.exceptions import UserError
from ..hooks.fetch import useFetch
import base64
import json


gender = {"male": "Masculino", "female": "Femenino", "other": "Otro"}


class ReporteFiniquito(models.TransientModel):
    _name = "hr.payroll.reporte.sso"
    _description = "Formulario para reporte de seguro social obligatorio"

    doc_type = fields.Selection(
        [("xlsx", "Excel"), ("txt", "TXT")],
        string="Formato de documento",
        default="xlsx",
    )
    month = fields.Selection(
        [
            ("1", "Enero"),
            ("2", "Febrero"),
            ("3", "Marzo"),
            ("4", "Abril"),
            ("5", "Mayo"),
            ("6", "Junio"),
            ("7", "Julio"),
            ("8", "Agosto"),
            ("9", "Septiembre"),
            ("10", "Octubre"),
            ("11", "Noviembre"),
            ("12", "Diciembre"),
        ],
        string="Mes",
        default="4",
    )
    year = fields.Char("Año", default="2023")
    file_name = fields.Char("Nombre de archivo")
    report_file = fields.Binary("Archivo de reporte", readonly=True)

    def get_employee_ids(self):
        employees = self.env["hr.payslip"].search([("state", "=", "paid")])
        data = []
        for pay in employees:
            if pay.date_from.year == int(self.year) and pay.date_from.month == int(
                self.month
            ):
                data.append(pay)
        return data

    def employee_sso_data(self, employee, payment, position=0):

        data = {
            "nro": position,
            "document_type": "",
            "document_value": "",
            "insured_number": employee.insured_number if employee.insured_number else "",
            "birthday": (
                employee.birthday.strftime("%d/%m/%Y") if employee.birthday else ""
            ),
            "date_hire": employee.contract_id.date_start.strftime("%d/%m/%Y") if employee.contract_id.date_start else "",
            "full_name": employee.display_name,
            "date_fire": (
                employee.contract_id.date_end.strftime("%d/%m/%Y")
                if employee.contract_id.date_end
                else ""
            ),
            "country_birth": employee.country_of_birth.name if employee.country_of_birth.name else "",
            "gender": gender[employee.gender] if employee.gender else "",
            "job_title": employee.job_title if employee.job_title else "",
            "paid_hour": payment.sum_worked_hours,
            "basic_days": 0,
            "paid_days": 0,
            "salary": payment.basic_wage if payment.basic_wage else 0,
            "extra_time": 0,
            "extra_time_amount": payment.net_wage - payment.basic_wage,
            "senior_bonus": 0,
            "other_bonuses": 0,
            "total_payment": payment.net_wage if payment.net_wage else 0,
        }

        if employee.identification_documents:
            for document in employee.identification_documents:
                if document.type_identification_document_id.code == "01":
                    data["document_type"] = "CI"
                    data["document_value"] = document.document_number

        for wd in payment.worked_days_line_ids:
            if wd.code == "WORK100":
                data["basic_days"] = wd.number_of_days
            else:
                data["extra_time"] += wd.number_of_days

            data["paid_days"] += wd.number_of_days

        return data

    def generate_data(self):
        payments = self.get_employee_ids()
        employee_data = []
        index = 1
        for payment in payments:
            employee_data.append(
                self.employee_sso_data(payment.employee_id, payment, position=index)
            )
            index += 1
        return json.dumps({
            "report":"sso",
            "extension":self.doc_type,
            "data": employee_data
            })

    def action_generate_report(self):
        if not self.doc_type:
            raise UserError("Selecciona el formato de documento")

        company = self.env.user.company_id
        data = self.generate_data()

        resp = useFetch(company.url_report_service, data)
        try:
            self.file_name = f"reporte actualizado.{self.doc_type}"
            file = base64.b64decode(resp["data"]["document"])
            self.report_file = base64.b64encode(file).decode("utf-8")
            return {
                "type": "ir.actions.act_url",
                "url": f"/web/content?model={self._name}&id={self.id}&field=report_file&filename_field=file_name&download=true",
                "target": "new",
            }
        except:
            notification = {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Advertencia"),
                    "type": "warning",
                    "message": "Error al realizar petición, por favor intenta de nuevo!",
                    "sticky": True,
                },
            }
        return notification
