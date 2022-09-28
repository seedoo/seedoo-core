from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class Document(models.Model):
    _inherit = "sd.dms.document"

    def documento_aggiungi_fascicolo_action(self):
        context = dict(self._context or {})
        context["document_id"] = self.id
        context["dossiers_ids"] = self.fascicolo_ids.ids
        # l'utente corrente non ha permessi di scrittura
        if not self.perm_write:
            raise ValidationError(_("You don't have write permissions!"))
        # il documento non ha una voce di titolario associata
        if not self.voce_titolario_id:
            raise ValidationError(_("The document does not have an associated titular item!"))
        # il documento ha già un fascicolo associato
        if self.fascicolo_ids:
            raise ValidationError(_("The document already has an associated dossier!"))

        return {
            "type": "ir.actions.act_window",
            "name": _("Add dossiers"),
            "view_mode": "form",
            "target": "new",
            "res_model": "sd.fascicolo.wizard.documento.aggiungi.fascicolo",
            "context": context,
        }