from odoo import models, fields

SELECTION_ASSEGNATARIO_TYPE = [
    ("conoscenza", "Conoscenza"),
    ("competenza", "Competenza")
]


class WizardProtocolloEliminaAssegnazione(models.TransientModel):
    _name = "sd.protocollo.wizard.protocollo.elimina.assegnazione"

    _description = "Wizard Elimina Assegnazione"

    assegnatario_id = fields.Many2one(
        string="Assegnatario",
        comodel_name="fl.set.voce.organigramma",
        readonly=True
    )

    assegnatario_type = fields.Selection(
        string="Tipologia Assegnazione",
        selection=SELECTION_ASSEGNATARIO_TYPE,
        readonly=True
    )

    motivazione = fields.Text(
        string="Motivazione",
        required=True
    )

    def default_get(self, fields_list):
        assegnazione_obj = self.env["sd.protocollo.assegnazione"]
        assegnazione = assegnazione_obj.browse(self.env.context.get("assegnazione_id"))
        result = super().default_get(fields_list)
        result["assegnatario_id"] = assegnazione.assegnatario_id.id
        result["assegnatario_type"] = assegnazione.tipologia
        result["motivazione"] = ""
        return result

    def action_unlink(self):
        self.ensure_one()
        assegnazione_obj = self.env["sd.protocollo.assegnazione"]
        assegnazione = assegnazione_obj.browse(self.env.context.get("assegnazione_id"))

        assegnazione_competenza_id = []
        assegnazione_conoscenza_id = []

        if self.assegnatario_type == "conoscenza":
            assegnazione_conoscenza_id.append(self.assegnatario_id.id)
        else:
            assegnazione_competenza_id.append(self.assegnatario_id.id)

        assegnazione.protocollo_id.elimina_assegnazione(
            assegnazione.id,
            self.motivazione
        )
