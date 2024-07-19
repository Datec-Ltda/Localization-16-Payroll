from odoo import _, models, fields
from odoo.exceptions import UserError
import logging
import json
import base64
from ..hooks.fetch import useFetch

_logger = logging.getLogger(__name__)


class HrPayrollFiniquito(models.Model):
    _inherit = "hr.payroll.finiquito"

    doc_type = fields.Selection(
        [
            ("pdf", "PDF"),
            ("csv", "CSV"),
        ],
        string="Formato de Documento",
        default="pdf",
    )
    report_file = fields.Binary("Archivo de reporte", readonly=True)
    file_name = fields.Char("Nombre de archivo")

    def get_employee(self):
        id = self.id
        employee = self.env["hr.payroll.finiquito"].browse(id)
        return employee

    def generate_data(self, employee):
        data = {
            "document_type": self.doc_type,
            "report": "finiquito",
            "company": employee.employee_id.company_id.display_name,
            "address_company": employee.employee_id.company_id.partner_id.contact_address_complete,
            "name": employee.employee_id.display_name,
            "address_employee": employee.employee_id.address_home_id.display_name,
            "age": employee.employee_id.afp_age,
            "contract_wage": employee.employee_id.contract_id.contract_wage,
            "marital": employee.employee_id.marital,
            "job_title": employee.employee_id.job_title,
            "passport_id": (
                employee.employee_id.passport_id
                if employee.employee_id.passport_id
                else "NA"
            ),
            "date_hire": employee.date_hire.strftime("%Y-%m-%d"),
            "date_end": employee.date_end.strftime("%Y-%m-%d"),
            "months": {
                "concept": [],
                "month_total_compensation": round(
                    employee.monthly_compensation_total, 2
                ),
                "seniority_bonus_total": round(employee.seniority_bonus_total, 2),
                "border_bonus_total": round(employee.border_bonus_total, 2),
                "commissions_total": round(employee.commissions_total, 2),
                "overtime_total": round(employee.overtime_total, 2),
                "other_bonuses_total": round(employee.other_bonuses_total, 2),
                "average": round(employee.average, 2),
                "total_months": round(employee.total_total, 2),
            },
            "eviction": round(employee.eviction, 2),
            "penalties": round(employee.penalties, 2),
            "indemnity_year": employee.indemnity_year,
            "indemnity_year_amount": round(employee.indemnity_year_amount, 2),
            "indemnity_month": employee.indemnity_month,
            "indemnity_month_amount": round(employee.indemnity_month_amount, 2),
            "indemnity_day": employee.indemnity_day,
            "indemnity_day_amount": round(employee.indemnity_day_amount, 2),
            "christmas_bonus_day": employee.christmas_bonus_day,
            "christmas_bonus_month": employee.christmas_bonus_month,
            "christmas_bonus_amount": round(
                employee.christmas_bonus_month_amount
                + employee.christmas_bonus_day_amount,
                2,
            ),
            "christmas_bonus_one": employee.christmas_bonus_one,
            "christmas_bonus_two": employee.christmas_bonus_two,
            "holidays_days": employee.holidays_days,
            "holidays_amount": round(employee.holidays_amount, 2),
            "other_extraordinary_bonuses": round(
                employee.other_extraordinary_bonuses, 2
            ),
            "finiquito": round(employee.finiquito, 2),
        }

        for i in range(1, 4):
            month_data = {
                f"month{i}": getattr(employee, f"month{i}"),
                f"compensation{i}": round(
                    getattr(employee, f"monthly_compensation{i}"), 2
                ),
                f"seniority_bonus{i}": round(
                    getattr(employee, f"seniority_bonus{i}"), 2
                ),
                f"border_bonus{i}": round(getattr(employee, f"border_bonus{i}"), 2),
                f"commissions{i}": round(getattr(employee, f"commissions{i}"), 2),
                f"overtime{i}": round(getattr(employee, f"overtime{i}"), 2),
                f"other_bonuses{i}": round(getattr(employee, f"other_bonuses{i}"), 2),
                f"total_month{i}": round(getattr(employee, f"total{i}"), 2),
            }
            data["months"]["concept"].append(month_data)

        return json.dumps(data)

    def action_generate_report(self):
        if not self.doc_type:
            raise UserError("Selecciona el formato de documento")

        employee = self.get_employee()
        company = self.env.user.company_id
        data = self.generate_data(employee)

        resp = useFetch(company.url_report_service, data)
        try:
            self.file_name = employee.employee_id.display_name
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

    # action para abrir popup en caso de necesitarse
    def finiquito_open_form_action(self):
        action = {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "reporte.finiquito",
            "target": "new",
        }

        return action


# popup a generarse para reporte csv y pdf
# class ReporteFiniquito(models.TransientModel):
#     _name = "reporte.finiquito"
#     _description = "Formulario para reporte de finiquitos"
