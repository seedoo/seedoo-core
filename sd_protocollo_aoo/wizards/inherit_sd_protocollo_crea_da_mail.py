from odoo import models, fields, api


class WizardProtocolloCreaDaMail(models.TransientModel):
    _inherit = "sd.protocollo.wizard.protocollo.crea.da.mail"

    aoo_id = fields.Many2one(
        string="AOO",
        comodel_name="fl.set.set",
        readonly=False
    )

    @api.onchange("protocollatore_ufficio_id")
    def onchange_protocollatore_ufficio_id(self):
        aoo_id = self.protocollatore_ufficio_id.aoo_id.id
        self.aoo_id = aoo_id
        context = dict(
            self.env.context,
            aoo_id=aoo_id
        )
        self = self.with_context(context)
        super(WizardProtocolloCreaDaMail, self).onchange_protocollatore_ufficio_id()

    def get_protocollo_vals(self):
        vals = super(WizardProtocolloCreaDaMail, self).get_protocollo_vals()
        vals["aoo_id"] = self.aoo_id.id
        return vals