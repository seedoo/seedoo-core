from odoo import models


class Document(models.Model):
    _inherit = "sd.dms.document"

    def documento_lista_protocollo_action(self):
        self.ensure_one()
        return {
            "name": "Protocollo",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "sd.protocollo.protocollo",
            "type": "ir.actions.act_window",
            "res_id": self.protocollo_id.id,
            "domain": [('id', '=', self.protocollo_id.id)],
        }
