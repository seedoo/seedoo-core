from odoo import models, fields, api, tools


class FascicoloDocumentAcl(models.Model):
    _name = "sd.fascicolo.fascicolo.document.acl"
    _description = "Document dossier acl"

    document_id = fields.Many2one(
        string="Document",
        comodel_name="sd.dms.document",
        ondelete="cascade",
        index=True
    )

    fascicolo_id = fields.Many2one(
        string="Dossier",
        comodel_name="sd.fascicolo.fascicolo",
        ondelete="cascade"
    )

    acl_id = fields.Many2one(
        string="Acl",
        comodel_name="sd.fascicolo.fascicolo.acl",
        ondelete="cascade"
    )

    res_model = fields.Selection(
        string="Resource Model",
        related="acl_id.res_model"
    )

    res_id = fields.Integer(
        string="Resource Id",
        related="acl_id.res_id"
    )

    res_name = fields.Char(
        string="Resource Name",
        related="acl_id.res_name"
    )

    perm_read = fields.Boolean(
        string="Read",
        related="acl_id.perm_read"
    )

    module_id = fields.Many2one(
        string="Module",
        related="acl_id.module_id"
    )