# -*- coding: utf-8 -*-

from psycopg2 import sql
from odoo import tools
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import ValidationError


class HrOrganizationalStructureReport(models.Model):
    _name = "hr.organizational.structure.report"
    _description = 'Estructura Organizacional'
    _auto = False
    _order = 'name desc'

    company_id = fields.Many2one('res.company', 'Compañia')
    department_id = fields.Many2one('hr.department', string='Departamento')
    name = fields.Char(string="Empleado")
    gender = fields.Selection([
        ('male', 'Masculino'),
        ('female', 'Femenino'),
        ('other', 'Otro')
    ], 'Sexo')
    staff_division_id = fields.Many2one('hr.employee.staff.division', string='División de personal')
    staffing_subdivision_id = fields.Many2one('hr.employee.staffing.subdivision', string='SubDivisión de personal')
    personnel_area_id = fields.Many2one('hr.employee.personnel.area', string='Área de personal')
    personnel_group_id = fields.Many2one('hr.employee.personnel.group', string='Grupo de personal')
    payroll_area_id = fields.Many2one('hr.employee.payroll.area', string='Área de nómina')

    def init(self):
        query = """              
        SELECT
                e."id",
                e.company_id,
                d.id as department_id,
                e."name",
                e.gender,
                e.staff_division_id,
                e.staffing_subdivision_id,
                e.personnel_area_id,
                e.personnel_group_id,
                e.payroll_area_id
                FROM hr_department d
                LEFT JOIN hr_employee e ON e.department_id = d.id
                LEFT JOIN hr_contract ct ON ct.employee_id = e.id
        """
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            sql.SQL("CREATE or REPLACE VIEW {} as ({})").format(
                sql.Identifier(self._table),
                sql.SQL(query)
            ))


        # tools.drop_view_if_exists(self.env.cr, 'hr_organizational_structure_report')
        # self.env.cr.execute(""" CREATE VIEW hr_organizational_structure_report AS (
        #       )
        #       """)
