from odoo import fields, models, api, _


class InheritSdProtocolloWizardProtocolloRegistra(models.TransientModel):
    _inherit = "sd.protocollo.wizard.protocollo.registra"

    account_id = fields.Many2one(
        string="Sending account",
        comodel_name="fl.mail.client.account",
        domain="[('use_outgoing_server', '=', True), ('pec', '=', pec)]",
        default=False
    )

    pec = fields.Boolean(
        string="PEC",
        default=False
    )

    account_id_required = fields.Boolean(
        string="Account id required",
        default=False
    )

    account_id_invisible = fields.Boolean(
        string="Account id invisible",
        default=False
    )

    @api.model
    def _get_pec(self, protocollo):
        if protocollo.mezzo_trasmissione_id and protocollo.mezzo_trasmissione_id.integrazione == "pec":
            return True
        return False

    @api.model
    def _get_account_id_required(self, protocollo):
        if protocollo.tipologia_protocollo == "uscita" and \
                protocollo.mezzo_trasmissione_id and \
                protocollo.mezzo_trasmissione_id.integrazione == "pec":
            return True
        return False

    @api.model
    def default_get(self, fields):
        result = super(InheritSdProtocolloWizardProtocolloRegistra, self).default_get(fields)
        protocollo_obj = self.env["sd.protocollo.protocollo"]
        protocollo = protocollo_obj.browse(self.env.context.get("protocollo_id"))
        result["pec"] = self._get_pec(protocollo)
        result["account_id_required"] = self._get_account_id_required(protocollo)
        result["account_id_invisible"] = not result["account_id_required"]
        return result

    def action_confirm(self):
        if self.account_id:
            protocollo_id = self.env.context.get("protocollo_id")
            protocollo = self.env["sd.protocollo.protocollo"].browse(protocollo_id)
            protocollo.write({"account_id": self.account_id.id})
        return super(InheritSdProtocolloWizardProtocolloRegistra, self).action_confirm()