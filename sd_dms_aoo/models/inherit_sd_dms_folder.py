from odoo import models, fields, api


class Folder(models.Model):
    _inherit = "sd.dms.folder"

    aoo_id = fields.Many2one(
        string="AOO",
        related="storage_id.aoo_id",
        store=True
    )
