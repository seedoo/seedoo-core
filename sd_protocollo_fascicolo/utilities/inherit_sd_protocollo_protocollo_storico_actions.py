from odoo import models, _
from odoo.addons.sd_protocollo.utilities.protocollo_storico_actions import HISTORY_CLASS, ERROR_CLASS, SUCCESS_CLASS


class Protocollo(models.Model):
    _inherit = "sd.protocollo.protocollo"

    def _get_li_storico_registra(self, body):
        body = super(Protocollo, self)._get_li_storico_registra(body)
        fascicoli = ', '.join([a.nome for a in self.fascicolo_ids])
        if fascicoli:
            body = body + "<li>%s: <span> %s </span></li>" % (_("Dossier"), fascicoli)
        return body

    def storico_aggiungi_fascicolazione(self, nome_fascicolo):
        self.ensure_one()
        action_class = "%s update" % HISTORY_CLASS
        subject = _("Dossier action")
        subject = self._get_subject(subject)
        body = "<div class='%s'>" % action_class
        body += "%s: <span class='%s'> %s</span>" % (_("Dossier"), SUCCESS_CLASS, nome_fascicolo)
        body += "</div>"
        self.message_post(body=subject + body)

    def storico_aggiungi_fascicolazione_da_fascicolo(self, nome_fascicolo):
        self.ensure_one()
        nome_fascicolo = "<span class='%s'> %s</span>" % (SUCCESS_CLASS, nome_fascicolo)
        subject = _("Dossier action %s added from Dossier") % nome_fascicolo
        subject = self._get_subject(subject)
        self.message_post(body=subject)

    def storico_elimina_fascicolazione(self, nome_fascicolo, from_dossiers=False):
        self.ensure_one()
        if not self.is_stato_tracciamento_storico():
            return
        action_class = "%s update" % HISTORY_CLASS
        subject = _("Dossier delete ")
        if from_dossiers:
            subject += _("from Dossiers")
        subject = self._get_subject(subject)
        body = "<div class='%s'>" % action_class
        body += "%s: <span class='%s'> %s</span>" % (_("Dossier"), ERROR_CLASS, nome_fascicolo)
        body += "</div>"
        self.message_post(body=subject + body)