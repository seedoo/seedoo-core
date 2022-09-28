from odoo import models, fields


class Protocollo(models.Model):
    _inherit = "sd.protocollo.protocollo"

    def protocollo_classifica_action(self):
        self.ensure_one()
        context = dict(
            self.env.context,
            protocollo_id=self.ids
        )
        return {
            "name": context.get("wizard_label", ""),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "sd.protocollo.wizard.protocollo.classifica.step1",
            "type": "ir.actions.act_window",
            "target": "new",
            "context": context
        }
