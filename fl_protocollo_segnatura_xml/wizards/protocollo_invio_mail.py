from odoo import models


class WizardProtocolloInvioMail(models.TransientModel):
    _inherit = "sd.protocollo.wizard.protocollo.invio.mail"

    def crea_invii(self):
        invio_obj = self.env["sd.protocollo.invio"]
        protocollo_id = self.env.context.get("protocollo_id")

        invio_obj._update_segnatura_xml_before_invio(protocollo_id, [self.account_id.id], False)
        super(WizardProtocolloInvioMail, self).crea_invii()