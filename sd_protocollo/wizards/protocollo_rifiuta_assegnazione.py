from odoo import models, fields, _
from odoo.exceptions import ValidationError


class WizardProtocolloRifiutaAssegnazione(models.TransientModel):
    _name = "sd.protocollo.wizard.protocollo.rifiuta.assegnazione"
    _description = "Wizard Rifiuta Assegnazione"

    motivazione = fields.Text(
        string="Motivazione",
        required=True
    )

    def action_confirm(self):
        protocollo_obj = self.env["sd.protocollo.protocollo"]
        protocollo = protocollo_obj.browse(self.env.context.get("protocollo_id"))
        assegnazione_competenza_ids = self.env.context.get("assegnazione_ids")
        protocollo.rifiuta_assegnazione(assegnazione_competenza_ids[0], self.env.uid, self.motivazione)
        return protocollo_obj.redirect_menu_protocolli()