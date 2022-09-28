from odoo import models, fields, api


class SetTitolarioOnDocument(models.TransientModel):
    _name = "sd.dms.titolario.wizard.set.titolario"
    _description = "Wizard set Titolario"

    document_id = fields.Many2one(
        string="Document",
        comodel_name="sd.dms.document",
        readonly=True
    )
