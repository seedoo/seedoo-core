from odoo import models


class WizardProtocolloReinvioMail(models.TransientModel):
    _inherit = "sd.protocollo.wizard.protocollo.reinvio.mail"

    #TODO refactory segnatura xml prima di riattivare (decommentare l'import del file all'interno del file __init__.py)
    def _crea_invio_mail(self, protocollo, destinatari_ids, invii, account):
        invio_obj = self.env["sd.protocollo.invio"]
        invio_obj._update_segnatura_xml_before_invio(protocollo.id, [account.id], invii)
        super(WizardProtocolloReinvioMail, self)._crea_invio_mail(protocollo, destinatari_ids, invii, account)
