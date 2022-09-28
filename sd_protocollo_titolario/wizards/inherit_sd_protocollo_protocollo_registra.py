from odoo import fields, models, api


class WizardProtocolloRegistra(models.TransientModel):
    _inherit = "sd.protocollo.wizard.protocollo.registra"

    voce_titolario_id = fields.Char(
        string="Classificazione",
        readonly=True
    )

    @api.model
    def default_get(self, fields):
        res = super(WizardProtocolloRegistra, self).default_get(fields)
        protocollo_obj = self.env["sd.protocollo.protocollo"]
        protocollo = protocollo_obj.browse(self.env.context.get("protocollo_id"))
        res["voce_titolario_id"] = protocollo.documento_id_voce_titolario_id.path_name
        return res