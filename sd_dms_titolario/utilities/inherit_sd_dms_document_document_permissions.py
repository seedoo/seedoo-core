from odoo import models, fields, api


class DocumentPermissions(models.Model):
    _inherit = "sd.dms.document"

    voce_titolario_id_required = fields.Boolean(
        string="Classification required",
        compute="_compute_voce_titolario_id_required"
    )

    voce_titolario_id_readonly = fields.Boolean(
        string="Classification readonly",
        compute="_compute_voce_titolario_id_readonly"
    )

    @api.onchange("document_type_id")
    def _compute_voce_titolario_id_required(self):
        for rec in self:
            rec.voce_titolario_id_required = rec.document_type_id.classification_required

    def _compute_voce_titolario_id_readonly(self):
        for rec in self:
            rec.voce_titolario_id_readonly = rec.field_readonly