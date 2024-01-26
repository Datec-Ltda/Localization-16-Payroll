# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from werkzeug.utils import secure_filename
from datetime import date


class HrEmployeeDocs(models.Model):
    _name = 'l10n_bo_hr.employee_docs'
    _description = 'Documentos adjuntos del empleado'

    _rec_name = 'name'
    _order = 'name ASC'

    name = fields.Char(
        string='Nombre',
        required=True,
        copy=False
    )
    doc_attachment_id = fields.Many2many('ir.attachment', 'doc_attach_rel', 'doc_id', 'attach_id3', string="Attachment",
                                         help='You can attach the copy of your document', copy=False)

    employee_id = fields.Many2one(string='Employee', comodel_name='hr.employee')





    

    


