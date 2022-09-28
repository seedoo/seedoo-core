from odoo import models, fields, _


class Protocollo(models.Model):
    _inherit = "sd.protocollo.protocollo"

    def storico_create_errors_from_mail(self,exceptions=[]):
        error_message_start = '<div><b><p>'
        error_message_start += _(
            "The following errors were found in the segnatura.xml:") + '</p></b><ul>'
        error_message_end = '</ul></div>'
        error_message = ''
        for error in exceptions:
            error_message += '<li>' + error + '</li>'
        subject = self._get_subject(error_message_start + error_message + error_message_end)
        self.message_post(body=subject)
