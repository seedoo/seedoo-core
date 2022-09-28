from odoo import models, fields, _
from odoo.exceptions import ValidationError


class WizardProtocolloLeggiAssegnazione(models.TransientModel):
    _name = "sd.protocollo.wizard.protocollo.leggi"
    _description = "Wizard Leggi Assegnazione"

    assegnazione_id = fields.Many2one(
        string="Assegnazione",
        comodel_name="sd.protocollo.assegnazione",
        domain=lambda self: [("id", "in", self.env.context.get("assegnazione_ids", []))],
        required=True
    )

    def action_confirm(self):
        protocollo_obj = self.env["sd.protocollo.protocollo"]
        protocollo = protocollo_obj.browse(self.env.context.get("protocollo_id"))
        protocollo.leggi_assegnazione(self.assegnazione_id.id, self.env.uid)