from odoo import fields, models, api, SUPERUSER_ID, _


SELECTION_REGISTRATION_TYPE_ADD = [
    ("protocol", "Protocol")
]

class DocumentType(models.Model):
    _inherit = "sd.dms.document.type"

    registration_type = fields.Selection(
        selection_add=SELECTION_REGISTRATION_TYPE_ADD,
        ondelete={
            "protocol": "set default"
        }
    )

