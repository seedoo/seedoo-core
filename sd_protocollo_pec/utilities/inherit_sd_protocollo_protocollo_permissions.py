from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class Protocollo(models.Model):
    _inherit = "sd.protocollo.protocollo"

    button_gestisci_invii_invisible = fields.Boolean(
        string="button gestisci invii",
        compute="compute_buttons_invisible",
    )

    @api.depends("tipologia_protocollo")
    def compute_buttons_invisible(self):
        super(Protocollo, self).compute_buttons_invisible()
        for protocollo in self:
            protocollo.button_gestisci_invii_invisible = protocollo._compute_button_gestisci_invii_invisible()

    def _compute_button_gestisci_invii_invisible(self):
        # - almeno uno degli invii ha il campo button_reinvia_mail_invisible o button_reset_mail_invisible a False
        for invio in self.invio_ids:
            if not invio.button_reinvia_mail_invisible or not invio.button_reset_mail_invisible:
                return False
        return True

    def _compute_tipologia_protocollo_readonly(self):
        super(Protocollo, self)._compute_tipologia_protocollo_readonly()
        for rec in self:
            if rec.mail_id:
                rec.tipologia_protocollo_readonly = True

    def _compute_button_modifica_allegati_invisible(self):
        button_modifica_allegati_invisible = super(Protocollo, self)._compute_button_modifica_allegati_invisible()
        conf = bool(self.env["ir.config_parameter"].sudo().get_param("sd_protocollo.modifica_documenti_pec"))
        # caso mail: il protocollo è in bozza, il campo mail_id è popolato e il parametro modifica_documenti_pec è false
        if self.state == "bozza" and self.mail_id and conf:
            button_modifica_allegati_invisible = False
        return button_modifica_allegati_invisible
