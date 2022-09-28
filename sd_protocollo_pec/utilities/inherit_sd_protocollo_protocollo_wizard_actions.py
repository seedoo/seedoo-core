from odoo import models, _
from odoo.exceptions import ValidationError


class Protocollo(models.Model):
    _inherit = "sd.protocollo.protocollo"

    def protocollo_gestione_invii_action(self, from_wizard=False):
        self.ensure_one()
        invii_da_reinviare = []
        invii_da_resettare = []
        invii_integrazione = []
        # si recuperano tutti gli invii da reinviare o da resettare
        for invio in self.invio_ids:
            if invio.da_reinviare:
                invii_da_reinviare.append(invio)
                invii_integrazione.append(invio.mezzo_trasmissione_integrazione)
            if invio.da_resettare:
                invii_da_resettare.append(invio)
        # se ci sono da reinviare più invii appartenenti a più di un'integrazione per un mezzo di trasmissione allora si
        # genera un errore: può essere gestito il reinvio di una sola integrazione
        if len(set(invii_integrazione)) > 1:
            raise ValidationError(_("The resending of more than one transmission media is not managed!"))
        # se ci sono invii da resettare allora si procede con la relativa action
        for invio_da_resettare in invii_da_resettare:
            invio_da_resettare.action_reset_mail()
        # se non ci sono invii da reinviare allora si conclude la action
        if len(invii_da_reinviare) == 0:
            return
        # si recuperano gli id degli invii da reinviare e si chiama il relativo wizard
        invio_ids = [invio.id for invio in invii_da_reinviare]
        context = dict(
            self.env.context,
            invio_ids=invio_ids,
        )
        return {
            "name": "Reinvio Mail",
            "view_type": "form",
            "view_mode": "form,tree",
            "res_model": "sd.protocollo.wizard.protocollo.reinvio.mail",
            "type": "ir.actions.act_window",
            "target": "new",
            "context": context
        }

    def protocollo_invia_action(self):
        self.ensure_one()
        integrazione_values = self.env["sd.protocollo.mezzo.trasmissione"].get_integrazione_values()
        if self.mezzo_trasmissione_id.integrazione in integrazione_values:
            context = dict(
                self.env.context,
                protocollo_id=self.id
            )
            return {
                "name": "Invio Mail",
                "view_type": "form",
                "view_mode": "form,tree",
                "res_model": "sd.protocollo.wizard.protocollo.invio.mail",
                "type": "ir.actions.act_window",
                "target": "new",
                "context": context
            }
        return super(Protocollo, self).protocollo_invia_action()