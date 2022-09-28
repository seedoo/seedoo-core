from odoo import models, fields


class Document(models.Model):
    _inherit = "sd.dms.document"

    protocollo_segnatura_xml = fields.Boolean(
        string="Segnatura Xml",
        default=False
    )
