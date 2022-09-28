from odoo import models, _

HISTORY_CLASS = "history_icon"


class DocumentoStoricoActions(models.Model):
    _inherit = "sd.dms.document"

    def storico_aggiunta_documento_a_bozza(self, protocollo_name):
        self.ensure_one()
        action_class = "%s created" % HISTORY_CLASS
        subject = _("Protocol %s created from that document as main document") % protocollo_name
        body = "<div class='%s'>" % action_class
        body += subject
        body += "</div>"
        self.message_post(body=body)

    def storico_aggiunta_allegato_a_bozza(self, protocollo_name):
        self.ensure_one()
        action_class = "%s created" % HISTORY_CLASS
        subject = _("Protocol %s created with that document as attachment") % protocollo_name
        body = "<div class='%s'>" % action_class
        body += subject
        body += "</div>"
        self.message_post(body=body)
