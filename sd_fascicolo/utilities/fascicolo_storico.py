from odoo import models, fields, api, _

HISTORY_CLASS = "history_icon"
ERROR_CLASS = "error"
SUCCESS_CLASS = "success"


class FascicoloHistoryActions(models.Model):
    _inherit = "sd.fascicolo.fascicolo"

    def storico_apertura_fascicolo(self):
        self.ensure_one()
        tipologia_fascicolo = {
            "fascicolo": _("Dossier"),
            "sottofascicolo": _("Sub-Dossier"),
            "inserto": _("Insert")
        }
        if self.tipologia:
            subject = _("%s opened") % tipologia_fascicolo[self.tipologia]
        else:
            subject = _("Dossier opened")
        subject = "<b>%s</b>" % subject
        self.message_post(body=subject)

    def storico_chiusura_fascicolo(self):
        self.ensure_one()
        tipologia_fascicolo = {
            "fascicolo": _("Dossier"),
            "sottofascicolo": _("Sub-Dossier"),
            "inserto": _("Insert")
        }
        if self.tipologia:
            subject = _("%s closed") % tipologia_fascicolo[self.tipologia]
        else:
            subject = _("Dossier closed")
        subject = "<b>%s</b>" % subject
        self.message_post(body=subject)

    def storico_aggiunta_documento(self, document_ids):
        self.ensure_one()
        document_obj = self.env["sd.dms.document"]
        documents = document_obj.search([("id", "in", document_ids)])
        documents_name = ", ".join([x.filename for x in documents])
        action_class = "%s update" % HISTORY_CLASS
        subject = _("Documents added")
        subject = "<b>%s</b>" % subject
        body = "<div class='%s'>" % action_class
        body += _("Documents: <span class='%s'> %s</span>") % (SUCCESS_CLASS, documents_name)
        body += "</div>"
        self.message_post(body=subject + body)

    def storico_disassocia_documento(self, document_ids, from_dossiers=False):
        self.ensure_one()
        document_obj = self.env["sd.dms.document"]
        documents = document_obj.search([("id", "in", document_ids)])
        documents_name = ", ".join([x.filename for x in documents])
        action_class = "%s remove" % HISTORY_CLASS
        subject = _("Documents removed")
        if from_dossiers:
            subject += _(" from Dossiers")
        subject = "<b>%s</b>" % subject
        body = "<div class='%s'>" % action_class
        body += _("Documents: <span class='%s'> %s</span>") % (ERROR_CLASS, documents_name)
        body += "</div>"
        self.message_post(body=subject + body)

    def storico_aggiunta_sottofascicolo_inserto(self, tipologia, nome):
        # Tipologia -> sottofascicolo/inserto
        # Nome -> nome sottofascicolo/inserto che si sta creando
        self.ensure_one()
        action_class = "%s update" % HISTORY_CLASS
        tipologia_fascicolo = {
            "fascicolo": _("Dossier"),
            "sottofascicolo": _("Sub-Dossier"),
            "inserto": _("Insert")
        }
        subject = _("%s added") % tipologia_fascicolo[tipologia]
        subject = "<b>%s</b>" % subject
        body = "<div class='%s'>" % action_class
        body += _("%s: <span class='%s'> %s</span>") % (tipologia_fascicolo[tipologia], SUCCESS_CLASS, nome)
        body += "</div>"
        self.message_post(body=subject + body)

    def storico_crea_fascicolo_sottofascicolo_inserto(self):
        self.ensure_one()
        tipologia_fascicolo = {
            "fascicolo": _("Dossier"),
            "sottofascicolo": _("Sub-Dossier"),
            "inserto": _("Insert")
        }
        if self.tipologia:
            subject = _("%s created") % tipologia_fascicolo[self.tipologia]
        else:
            subject = _("Dossier created")
        subject = "<b>%s</b>" % subject
        self.message_post(body=subject)

    def storico_disassocia_sottofascicolo_inserto(self, tipologia, nome):
        # Tipologia -> sottofascicolo/inserto
        # Nome -> nome sottofascicolo/inserto che si sta eliminando
        self.ensure_one()
        action_class = "%s removed" % HISTORY_CLASS
        fascicolo_tipologia = tipologia.title()
        subject = _("%s removed") % fascicolo_tipologia
        subject = "<b>%s</b>" % subject
        body = "<div class='%s'>" % action_class
        body += _("%s: <span class='%s'> %s</span>") % (fascicolo_tipologia, ERROR_CLASS, nome)
        body += "</div>"
        self.message_post(body=subject + body)

