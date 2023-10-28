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
    # attachment = fields.Binary(
    #     string='Doc',
    #     attachment=True
    # )
    #
    # attachment_name = fields.Char(
    #     string='Nombre del adjunto',
    #     required=True,
    #     copy=False
    # )

    employee_id = fields.Many2one(string='Employee', comodel_name='hr.employee')

    # @api.onchange('attachment')
    # def _onchange_attachment(self):
    #     if self.attachment:
    #         self.attachment_name = self._get_attachment_name()

    # @api.onchange('attachment')
    # def _onchange_attachment(self):
    #     if self.attachment:
    #         self.attachment_name = secure_filename(self.attachment_name)

    # def _get_attachment_name(self):
    #     attachment_name = ''
    #     if self.attachment:
    #         attachment_name = self.attachment.filename
    #         # attachment_name = self.env['ir.attachment'].browse(self.id).display_name
    #     return attachment_name




    

    


