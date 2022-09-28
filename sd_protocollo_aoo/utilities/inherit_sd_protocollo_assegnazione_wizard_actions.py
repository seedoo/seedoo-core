from odoo import models

class AssegnazioneWizardActions(models.Model):
    _inherit = "sd.protocollo.assegnazione"

    def assegnazione_modifica_action(self):
        context = dict(
            self.env.context,
            aoo_id=self.protocollo_id.aoo_id.id
        )
        return super(AssegnazioneWizardActions, self.with_context(context)).assegnazione_modifica_action()
