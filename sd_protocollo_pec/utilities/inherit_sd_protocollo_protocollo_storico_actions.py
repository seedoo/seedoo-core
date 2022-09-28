from odoo import models, fields, _


class Protocollo(models.Model):
    _inherit = "sd.protocollo.protocollo"

    def storico_invio_mail(self, invio, state):
        response = False
        if state == "sent":
            response = True

        if invio.mezzo_trasmissione_integrazione == "pec":
            destinatario_list = []
            for destinatario in invio.destinatario_ids:
                if destinatario.email:
                    destinatario_list.append(destinatario.email)
            email_list = ", ".join(destinatario_list)
            self.storico_invio_mail_pec(email_list, response)

    def storico_invio_mail_pec(self, email_list, response):
        self.ensure_one()

        class_vals = self._get_class()

        result = _("Protocol not sent to:")
        class_type = class_vals["error"]

        if response:
            result = _("Protocol sent to:")
            class_type = class_vals["success"]

        result = self._get_subject(result)

        action_class = "%s invio pec" % class_vals["history"]
        body = "<div class='%s'>" % action_class
        body += "%s <span class='%s'>%s</span>" % (result, class_type, email_list)
        body += "</div>"

        self.message_post(body=body)

    def storico_reinvio_modifica_mail(self, nome, mail_after, mail_before, mtype, motivazione):
        self.ensure_one()

        class_vals = self._get_class()

        mail_type = "e-mail"
        if mtype == "pec":
            mail_type = "PEC"

        action_class = "%s update" % class_vals["history"]
        subject = _("Address changed")
        subject = self._get_subject(subject + " %s" % mail_type)
        subject = "<p>%s: %s</p>" % (subject, motivazione)

        body = "<div class='%s'>" % action_class
        body += "%s: <span class='%s'> %s</span> -> <span class='%s'> %s </span>" \
                % (nome, class_vals["error"], mail_before, class_vals["success"], mail_after)
        body += "</div>"
        self.message_post(body=subject + body)
