from odoo import models, _

class HistoryMail(models.Model):
    _inherit = "mail.mail"

    def storico_crea_eccezione_da_mail(self, exceptions=[]):
        error_message_start = '<div><b><p>'
        error_message_start += _(
            "Unable to create draft protocol, the following errors were found in the segnatura.xml:") + '</p></b><ul>'
        error_message_end = '</ul></div>'
        error_message = ''
        for error in exceptions:
            error_message += '<li>' + error + '</li>'
        subject = self._get_subject(error_message_start + error_message + error_message_end)
        self.message_post(body=subject)
