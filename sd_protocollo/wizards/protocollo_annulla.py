from odoo import models, fields, api


class WizardProtocolloAnnulla(models.TransientModel):
    _name = "sd.protocollo.wizard.protocollo.annulla"
    _description = "Wizard Protocollo Annulla"

    causa = fields.Char(
        string="Causa",
        required=True
    )

    responsabile_id = fields.Many2one(
        string="Responsabile",
        comodel_name="res.users",
        required=True,
        readonly=True
    )

    richiedente_id = fields.Many2one(
        string="Richiedente",
        comodel_name="res.users",
        required=True
    )

    data = fields.Datetime(
        string="Data",
        required=True,
        readonly=True
    )

    @api.model
    def default_get(self, wizard_fields):
        res = super(WizardProtocolloAnnulla, self).default_get(wizard_fields)

        res["responsabile_id"] = self.env.user.id
        res["data"] = fields.datetime.now()

        return res

    def action_cancel(self):
        protocollo_obj = self.env["sd.protocollo.protocollo"]

        protocollo = protocollo_obj.browse(self.env.context.get("protocollo_id"))
        protocollo.annulla(
            causa=self.causa,
            responsabile=self.responsabile_id,
            richiedente=self.richiedente_id,
            data=self.data
        )
        self.env.user._request_notify_message("info", "Annulla Protocollo", "Protocollo annullato con successo")