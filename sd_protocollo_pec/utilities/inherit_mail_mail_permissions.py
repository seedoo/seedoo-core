from odoo import models, fields


class MailPermissions(models.Model):
    _inherit = "mail.mail"

    button_crea_bozza_protocollo_invisible = fields.Boolean(
        string="button crea bozza protocollo invisible",
        compute="compute_buttons_invisible"
    )

    button_non_protocollare_invisible = fields.Boolean(
        string="button non protocollare invisible",
        compute="compute_buttons_invisible"
    )

    button_ripristina_da_non_protocollata_invisible = fields.Boolean(
        string="button ripristina da non protocollare invisible",
        compute="compute_buttons_invisible"
    )

    button_ripristina_da_protocollata_invisible = fields.Boolean(
        string="button ripristina da protocollata invisible",
        compute="compute_buttons_invisible"
    )

    def compute_buttons_invisible(self):
        for mail in self:
            mail.button_crea_bozza_protocollo_invisible = mail._compute_button_crea_bozza_protocollo_invisible()
            mail.button_non_protocollare_invisible = mail.button_crea_bozza_protocollo_invisible
            mail.button_ripristina_da_non_protocollata_invisible = mail._compute_button_ripristina_da_non_protocollata_invisible()
            mail.button_ripristina_da_protocollata_invisible = mail._compute_button_ripristina_da_protocollata_invisible()

    def _compute_button_crea_bozza_protocollo_invisible(self):
        # - l'utente corrente ha il permesso group_sd_protocollo_crea_protocollo_ingresso_da_pec
        # - la direction della mail è in ingresso
        # - lo stato della mail è non_protocollata
        # - la mail non è associata ad un protocollo
        # - la mail è una PEC di tipo posta certificata (quindi non è una ricevuta PEC) oppure una semplice mail (errore)
        if self.env.user.has_group('sd_protocollo_pec.group_sd_protocollo_crea_protocollo_ingresso_da_pec') and \
                self.direction == "in" and \
                self.protocollo_action == "mail_da_protocollare" and \
                not self.protocollo_id and \
                self.pec and (self.pec_type == "posta-certificata" or self.pec_type == "errore"):
            return False
        return True

    def _compute_button_ripristina_da_non_protocollata_invisible(self):
        # - l'utente corrente ha profilo protocollatore
        # - la direction della mail è in ingresso
        # - lo stato della mail è non_protocollata
        if self.env.user.has_group('sd_protocollo.group_sd_protocollo_protocollatore') and \
                self.direction == "in" and \
                self.protocollo_action == "non_protocollata":
            return False
        return True

    def _compute_button_ripristina_da_protocollata_invisible(self):
        # - l'utente corrente ha profilo protocollatore
        # - la direction della mail è in ingresso
        # - lo stato della mail è protocollata
        # - la mail è associata ad un protocollo in stato annullato
        # - la mail non è mai stata ripristinata
        if self.env.user.has_group('sd_protocollo.group_sd_protocollo_protocollatore') and \
                self.direction == "in" and \
                self.protocollo_action == "protocollata" and \
                (self.protocollo_id and self.protocollo_id.state == "annullato") and \
                self.search([("protocollo_restore_mail_id", "=", self.id)], count=True) == 0:
            return False
        return True
