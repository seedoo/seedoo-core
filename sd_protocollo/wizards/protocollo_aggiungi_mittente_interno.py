from odoo import models, fields, api


class WizardProtocolloAggiungiMittenteInterno(models.TransientModel):
    _name = "sd.protocollo.wizard.protocollo.add.mittente.in"
    _description = "Wizard Aggiungi Mittente Interno"

    mittente_interno_id = fields.Many2one(
        string="Mittente",
        comodel_name="fl.set.voce.organigramma",
        domain=[("can_used_to_protocol", "=", True)],
        required=True
    )

    def default_get(self, fields_list):
        protocollo_obj = self.env["sd.protocollo.protocollo"]
        res = super(WizardProtocolloAggiungiMittenteInterno, self).default_get(fields_list)
        protocollo_id = self.env.context.get("protocollo_id", False)
        protocollo = protocollo_obj.browse(protocollo_id)
        res["mittente_interno_id"] = protocollo.mittente_interno_id
        return res

    def action_salva(self):
        protocollo_obj = self.env["sd.protocollo.protocollo"]
        protocollo_id = self.env.context.get("protocollo_id", False)
        protocollo = protocollo_obj.browse(protocollo_id)
        protocollo.salva_mittente_interno(self.mittente_interno_id)