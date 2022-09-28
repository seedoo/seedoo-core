from odoo import models, fields


class WizardProtocolloCaricaDocumento(models.TransientModel):
    _inherit = "sd.protocollo.wizard.protocollo.carica.documento"

    protocollo_company_id = fields.Many2one(
        string="Protocollo Company",
        comodel_name="res.company",
        readonly=True
    )

    voce_titolario_id = fields.Many2one(
        string="Classificazione",
        comodel_name="sd.dms.titolario.voce.titolario",
        domain="[('titolario_id.active','=',True), ('titolario_id.state','=',True), ('parent_active', '=', True), ('titolario_company_id','=',protocollo_company_id )]"
    )

    def default_get(self, fields_list):
        protocollo_obj = self.env["sd.protocollo.protocollo"]
        res = super(WizardProtocolloCaricaDocumento, self).default_get(fields_list)
        tipologia_documento = self.env.context.get("tipologia_documento", False)
        protocollo_id = self.env.context.get("protocollo_id", False)
        documento_obj = self.env["sd.dms.document"]

        if self.env.context.get("allegato_id", False):
            documento = documento_obj.browse(protocollo_id)
            protocollo = documento.protocollo_id
        elif tipologia_documento == "allegato":
            protocollo = protocollo_obj.browse(protocollo_id)
            documento = protocollo.documento_id
            voce_titolario_id = documento.voce_titolario_id
            documento = documento_obj
            res["voce_titolario_id"] = voce_titolario_id
        else:
            protocollo = protocollo_obj.browse(protocollo_id)
            documento = protocollo.documento_id

        if "voce_titolario_id" not in res:
            res["voce_titolario_id"] = documento.voce_titolario_id

        res["protocollo_company_id"] = protocollo.company_id.id

        return res

    def _get_documento_vals(self, vals):
        vals = super(WizardProtocolloCaricaDocumento, self)._get_documento_vals(vals)
        if self.voce_titolario_id:
            vals.update({
                "voce_titolario_id": self.voce_titolario_id.id,
                "voce_titolario_name": self.voce_titolario_id.path_name
            })

        return vals
