from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import collections

HISTORY_CLASS = "history_icon"
ERROR_CLASS = "error"
SUCCESS_CLASS = "success"


class ProtocolloHistoryActions(models.Model):
    _inherit = "sd.protocollo.protocollo"

    def salva_storico(self):
        return

    @api.model
    def get_stati_tracciamento_storico(self):
        return ["registrato", "annullato"]

    def is_stato_tracciamento_storico(self):
        self.ensure_one()
        if self.state in self.get_stati_tracciamento_storico():
            return True
        return False

    @api.model
    def get_label_storico_competenza(self):
        return _("Assignee competence")

    @api.model
    def get_label_storico_conoscenza(self):
        return _("Assignee knowledge")

    def _get_subject(self, string):
        return "<b>%s</b>" % string

    def storico_crea_bozza(self, module=False):
        if not module:
            subject = _("Protocol draft created")
        else:
            subject = _("Protocol draft created from %s") % module
        subject = self._get_subject(subject)
        self.message_post(body=subject)

    def storico_registra(self):
        self.ensure_one()
        action_class = "%s register" % HISTORY_CLASS
        body = "<div class='%s'><b>%s %s</b><ul>" % (action_class, _("Protocol registered"), self.numero_protocollo)
        body = self._get_li_storico_registra(body)
        body += "</ul></div>"
        self.message_post(body=body)

    def _get_li_storico_registra(self, body):
        ass_com = ', '.join([a.assegnatario_id.path_name for a in self.assegnazione_competenza_ids])
        ass_con = ', '.join([a.assegnatario_id.path_name for a in self.assegnazione_conoscenza_ids])
        if ass_com:
            body = body + "<li>%s: <span> %s </span></li>" % (self.get_label_storico_competenza(), ass_com)
        if ass_con:
            body = body + "<li>%s: <span> %s </span></li>" % (self.get_label_storico_conoscenza(), ass_con)
        return body

    def storico_annulla(self, causa, responsabile, richiedente, data):
        self.ensure_one()
        action_class = "%s cancel" % HISTORY_CLASS
        subject = _("Protocol canceled (requested by %s)") % richiedente.name
        body = "<div class='%s'>" % action_class
        body += self._get_subject(subject)
        body += "</div>"
        self.message_post(body=body)

    def storico_aggiungi_assegnatario(self, assegnatario_competenza_id, assegnatario_conoscenza_ids, motivazione):
        self.ensure_one()
        voce_organigramma_obj = self.env["fl.set.voce.organigramma"]
        if not self.is_stato_tracciamento_storico():
            return
        subject = _("Protocol assigned:")
        subject = "%s%s" % (self._get_subject(subject), ": " + motivazione if motivazione else "")
        action_class = "%s update" % HISTORY_CLASS
        body = "<div class='%s'><ul>" % action_class
        if assegnatario_competenza_id:
            assegnatario = voce_organigramma_obj.browse(assegnatario_competenza_id).path_name
            body = body + "<li>%s: <span class='%s'> %s</span></li>" % (
                self.get_label_storico_competenza(),
                SUCCESS_CLASS,
                assegnatario
            )
        if assegnatario_conoscenza_ids:
            assegnatari = voce_organigramma_obj.search([("id", "in", assegnatario_conoscenza_ids)])
            assegnatari_nome = [a.path_name for a in assegnatari]
            assegnatari = ", ".join(assegnatari_nome)
            body = body + "<li>%s: <span class='%s'> %s</span></li>" % (
                self.get_label_storico_conoscenza(),
                SUCCESS_CLASS,
                assegnatari
            )
        body += "</ul></div>"
        self.message_post(body=subject + body)

    def storico_elimina_assegnazione(self, assegnatario_id, tipologia, motivazione):
        self.ensure_one()
        voce_organigramma_obj = self.env["fl.set.voce.organigramma"]
        if not self.is_stato_tracciamento_storico():
            return
        subject = _("Elimination of assignee")
        subject = "%s%s" % (self._get_subject(subject), ": " + motivazione if motivazione else "")
        action_class = "%s update" % HISTORY_CLASS
        body = "<div class='%s'>" % action_class
        label = self.get_label_storico_conoscenza() if tipologia == "conoscenza" else self.get_label_storico_competenza()
        if assegnatario_id:
            assegnatario = voce_organigramma_obj.browse(assegnatario_id).path_name
            body = body + _("<p>%s removed: <span class='%s'> %s</span></p>") % (
                label,
                ERROR_CLASS,
                assegnatario
            )
        body += "</div>"
        self.message_post(body=subject + body)

    def storico_prendi_in_carico_assegnazione(self, utente_id):
        self.ensure_one()
        action_class = "%s taken_charge" % HISTORY_CLASS
        body = "<div class='%s'>" % action_class
        body = body + self._get_subject(_("Assignment taken charge"))
        body += "</div>"

        self.message_post(body=body)

    def storico_rifiuta_assegnazione(self, utente_id, motivazione):
        self.ensure_one()
        subject = _("Assignment refused")
        subject = "<p>%s: %s</p>" % (self._get_subject(subject), motivazione)
        self.message_post(body=subject)

    def storico_leggi_assegnazione(self, utente_id):
        self.ensure_one()
        action_class = "%s read" % HISTORY_CLASS
        body = "<div class='%s'>" % action_class
        body = body + self._get_subject(_("Protocol read"))
        body += "</div>"
        self.message_post(body=body)

    def storico_riassegna(self, old_assegnatario_id, new_assegnatario_id):
        self.ensure_one()
        voce_organigramma_obj = self.env["fl.set.voce.organigramma"]
        old_assegnatario_name = voce_organigramma_obj.browse(old_assegnatario_id).path_name
        new_assegnatario_name = voce_organigramma_obj.browse(new_assegnatario_id).path_name
        subject = _("Protocol reassigned")
        subject = "<p>%s</p>" % (self._get_subject(subject))
        action_class = "%s reasigned" % HISTORY_CLASS
        body = "<div class='%s'>" % action_class
        body = body + "%s: <span class='%s'> %s</span> -> <span class='%s'> %s</span></li>" % (
            self.get_label_storico_competenza(),
            ERROR_CLASS,
            old_assegnatario_name,
            SUCCESS_CLASS,
            new_assegnatario_name
        )
        body += "</div>"
        self.message_post(body=subject + body)

    def storico_completa_lavorazione(self, utente_id, motivazione):
        self.ensure_one()
        action_class = "%s completa_lavorazione" % HISTORY_CLASS
        subject = _("Processing completed")
        body = "<div class='%s'>" % action_class
        body = body + "<p>%s%s%s</p>" % (
            self._get_subject(subject), self._get_user_office(utente_id), ": " + motivazione if motivazione else "")
        body += "</div>"
        self.message_post(body=body)

    def storico_rimetti_in_lavorazione(self, utente_id, motivazione):
        self.ensure_one()
        action_class = "%s rimetti_in_lavorazione" % HISTORY_CLASS
        subject = _("Processing reopened")
        body = "<div class='%s'>" % action_class
        body = body + "<p>%s%s%s</p>" % (
            self._get_subject(subject), self._get_user_office(utente_id), ": " + motivazione if motivazione else "")
        body += "</div>"
        self.message_post(body=body)

    def storico_documento(self, filename, tipologia_documento):
        action_class = "%s upload" % HISTORY_CLASS
        subject = _("Upload document")
        subject = self._get_subject(subject)
        body = "<div class='%s'>" % action_class
        if tipologia_documento == "documento":
            body += _("Added main document: %s") % filename
        else:
            body += _("Added document: %s") % filename
        body += "</div>"
        self.message_post(body=subject + body)

    def storico_data_ricezione(self, old_data, new_data):
        if not self.is_stato_tracciamento_storico():
            return
        action_class = "%s data_ricezione" % HISTORY_CLASS
        subject = _("Reception date changed")
        subject = self._get_subject(subject)
        body = "<div class='%s'>" % action_class
        body += _("Reception date: <span class='%s'> %s</span> -> <span class='%s'> %s</span>" % (
        ERROR_CLASS, old_data, SUCCESS_CLASS, new_data))
        body += "</div>"
        self.message_post(body=subject + body)

    def storico_bozza_aggiunta_allegato_da_documenti(self, allegato_list):
        self.ensure_one()
        action_class = "%s created" % HISTORY_CLASS
        subject = _("Documents inserted as attachments from Documents:")
        body = "<div class='%s'>" % action_class
        body += subject
        body += "</div>"
        body += "<ul>"
        for allegato in allegato_list:
            body += "<li>%s</li>" % allegato
        body += "</ul>"
        self.message_post(body=body)

    def _get_class(self):
        class_vals = {
            "history": HISTORY_CLASS,
            "error": ERROR_CLASS,
            "success": SUCCESS_CLASS
        }
        return class_vals

    def _get_user_office(self, user_id):
        if True:
            return ""
        return _("(for office %s)") % ""
