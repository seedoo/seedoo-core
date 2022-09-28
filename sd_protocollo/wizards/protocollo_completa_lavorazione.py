from odoo import models, fields, api

SELECTION_STATO_DA_MODIFICARE = [
    ("stato_protocollatore", "Stato Protocollatore"),
    ("stato_assegnazione", "Stato Assegnazione")
]


class WizardProtocolloCompletaLavorazione(models.TransientModel):
    _name = "sd.protocollo.wizard.protocollo.completa.lavorazione"
    _description = "Wizard Completa Lavorazione"

    stato_da_modificare = fields.Selection(
        string="Stato da Modificare",
        selection=SELECTION_STATO_DA_MODIFICARE,
        required=True
    )

    assegnazione_id = fields.Many2one(
        string="Assegnazione",
        comodel_name="sd.protocollo.assegnazione",
        domain=lambda self: [("id", "in", self.env.context.get("assegnazione_ids", []))],
    )

    motivazione = fields.Text(
        string="Motivazione",
        default=False
    )

    stato_da_modificare_invisible = fields.Boolean(
        string="Stato da Modificare Invisible"
    )

    assegnazione_id_invisible = fields.Boolean(
        string="Assegnazione Invisible"
    )

    motivazione_invisible = fields.Boolean(
        string="Motivazione Invisible"
    )

    @api.model
    def default_get(self, fields_list):
        result = super(WizardProtocolloCompletaLavorazione, self).default_get(fields_list)
        config_obj = self.env["ir.config_parameter"].sudo()
        is_protocollatore = self.env.context.get("is_protocollatore", False)
        assegnazione_ids = self.env.context.get("assegnazione_ids", [])
        result["stato_da_modificare"] = "stato_protocollatore" if is_protocollatore else "stato_assegnazione"
        result["stato_da_modificare_invisible"] = not is_protocollatore or len(assegnazione_ids)==0
        result["assegnazione_id"] = assegnazione_ids[0] if len(assegnazione_ids)==1 else False
        result["assegnazione_id_invisible"] = True if len(assegnazione_ids) == 1 else False
        result["motivazione_invisible"] = not bool(config_obj.get_param("sd_protocollo.visualizza_motivazione_completa_lavorazione"))
        return result

    def action_completa_lavorazione(self):
        protocollo_obj = self.env["sd.protocollo.protocollo"]
        protocollo = protocollo_obj.browse(self.env.context.get("protocollo_id"))
        if self.stato_da_modificare == "stato_protocollatore":
            return protocollo.completa_lavorazione_protocollatore(self.env.uid, self.motivazione)
        elif self.stato_da_modificare == "stato_assegnazione":
            return protocollo.completa_lavorazione_assegnazione(self.assegnazione_id.id, self.env.uid, self.motivazione)