from odoo import models, fields


class Document(models.Model):
    _inherit = "sd.dms.document"

    aoo_id = fields.Many2one(
        string="AOO",
        related="storage_id.aoo_id",
        store=True
    )
