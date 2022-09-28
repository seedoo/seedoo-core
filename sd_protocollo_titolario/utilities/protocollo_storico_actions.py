from odoo import models
from odoo.addons.sd_protocollo.utilities.protocollo_storico_actions import *

class Protocollo(models.Model):
    _inherit = "sd.protocollo.protocollo"

    def storico_classifica_documento(self, before_classificazione, after_classificazione, motivazione="",
                                     before_competenza="", after_competenza=""):
        self.ensure_one()
        if not self.is_stato_tracciamento_storico():
            return
        data_modified = False
        action_class = "%s update" % HISTORY_CLASS
        body = "<div class='%s'>" % action_class
        if (before_classificazione or after_classificazione) and (before_classificazione != after_classificazione):
            data_modified = True
            body = body + "%s: <span class='%s'> %s</span> -> <span class='%s'> %s </span>" % (
                "Classificazione",
                ERROR_CLASS,
                before_classificazione,
                SUCCESS_CLASS,
                after_classificazione
            )
        if before_competenza or after_competenza:
            data_modified = True
            body = body + "%s: <span class='%s'> %s</span> -> <span class='%s'> %s </span>" % (
                self.get_label_storico_competenza(),
                ERROR_CLASS,
                before_competenza,
                SUCCESS_CLASS,
                after_competenza
            )
        body += "</div>"
        if data_modified:
            subject_label = "Aggiunta assegnatari tramite classificazione"
            if before_competenza:
                subject_label = "Modifica assegnatari tramite classificazione"
            if after_classificazione:
                subject_label = "Modifica classificazione" if before_classificazione else "Inserimento classificazione"
            subject = "<p><b>%s</b>%s</p>" % (self._get_subject(subject_label), ": " + motivazione if motivazione else "")
            self.message_post(body=subject + body)
