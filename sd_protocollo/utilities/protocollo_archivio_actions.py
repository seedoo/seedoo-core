from odoo import models, fields, api


class ProtocolloArchivioActions(models.Model):
    _inherit = "sd.protocollo.archivio"

    def show_protocollo_ids_action(self):
        self.ensure_one()
        context = dict(
            self.env.context,
            active_test=False
        )
        return {
            "name": "Protocolli",
            "view_mode": "tree,form",
            "res_model": "sd.protocollo.protocollo",
            "type": "ir.actions.act_window",
            "target": "current",
            "domain": [("archivio_id", "=", self.id)],
            "context": context
        }