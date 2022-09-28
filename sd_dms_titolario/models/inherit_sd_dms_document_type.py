from odoo import fields, models, api, SUPERUSER_ID, _


class DocumentType(models.Model):
    _inherit = "sd.dms.document.type"

    classification_required = fields.Boolean(
        string="Classification required",
        default=False
    )