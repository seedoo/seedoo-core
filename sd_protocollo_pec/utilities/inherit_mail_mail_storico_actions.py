from odoo import models, _

HISTORY_CLASS = "history_icon"
ERROR_CLASS = "error"
SUCCESS_CLASS = "success"


class HistoryMail(models.Model):
    _inherit = "mail.mail"

    def storico_mail_protocollo_action_protocollata(self, protocol_nome):
        self.ensure_one()
        action_class = "%s protocollo_action" % HISTORY_CLASS
        subject = _("Protocol %s registered") % protocol_nome
        body = "<div class='%s'>" % action_class
        body = body + "<p>%s</p>" % self._get_subject(subject)
        body += "</div>"
        self.message_post(body=body)

    def storico_mail_protocollo_action_non_protocollata(self):
        self.ensure_one()
        action_class = "%s protocollo_action" % HISTORY_CLASS
        subject = _("Message set to protocol not done")  # Messaggio impostato da non protocollare
        body = "<div class='%s'>" % action_class
        body = body + "<p>%s</p>" % self._get_subject(subject)
        body += "</div>"
        self.message_post(body=body)

    def storico_mail_protocollo_action_non_da_protocollare(self):
        self.ensure_one()
        action_class = "%s protocollo_action" % HISTORY_CLASS
        subject = _("Message set to protocol not done")
        body = "<div class='%s'>" % action_class
        body = body + "<p>%s</p>" % self._get_subject(subject)
        body += "</div>"
        self.message_post(body=body)

    def storico_crea_protocollo_da_mail(self, protocollo_nome):
        self.ensure_one()
        action_class = "%s protocollo_da_mail" % HISTORY_CLASS
        subject = _("Protocol %s created") % protocollo_nome
        body = "<div class='%s'>" % action_class
        body = body + "<p>%s</p>" % self._get_subject(subject)
        body += "</div>"
        self.message_post(body=body)

    def storico_protocollo_eliminato(self, protocollo_nome):
        self.ensure_one()
        action_class = "%s protocollo_eliminato" % HISTORY_CLASS
        subject = _("Draft protocol %s deleted") % protocollo_nome
        body = "<div class='%s'>" % action_class
        body = body + "<p>%s</p>" % self._get_subject(subject)
        body += "</div>"
        self.message_post(body=body)

    def storico_ripristina_da_protocollata_mail(self):
        self.ensure_one()
        action_class = "%s mail_ripristinata" % HISTORY_CLASS
        subject = _("New mail created for recovery")
        body = "<div class='%s'>" % action_class
        body = body + "<p>%s</p>" % self._get_subject(subject)
        body += "</div>"
        self.message_post(body=body)

    def storico_ripristina_per_protocollazione_mail(self):
        self.ensure_one()
        action_class = "%s mail_ripristinata" % HISTORY_CLASS
        subject = _("Mail recovered for protocol action")  # Messaggio ripristinato per protocollazione
        body = "<div class='%s'>" % action_class
        body = body + "<p>%s</p>" % self._get_subject(subject)
        body += "</div>"
        self.message_post(body=body)

    def storico_creata_da_ripristino(self):
        self.ensure_one()
        action_class = "%s mail_creata_da_ripristino" % HISTORY_CLASS
        subject = _("Mail created by recovery")
        body = "<div class='%s'>" % action_class
        body = body + "<p>%s</p>" % self._get_subject(subject)
        body += "</div>"
        self.message_post(body=body)

    def _get_subject(self, string):
        return "<b>%s</b>" % string
