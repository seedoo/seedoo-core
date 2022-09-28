from odoo import models


class AssegnazioneWizardActions(models.Model):
    _inherit = "sd.protocollo.assegnazione"

    def assegnazione_elimina_action(self):
        self.ensure_one()
        if self.protocollo_id.state == "bozza":
            return self.protocollo_id.elimina_assegnazione(self.id, False)
        context = dict(
            self.env.context,
            assegnazione_id=self.id,
            display="path_name"
        )
        return {
            "name": "Elimina Assegnazione",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "sd.protocollo.wizard.protocollo.elimina.assegnazione",
            "type": "ir.actions.act_window",
            "target": "new",
            "context": context
        }
