from odoo import models, fields, _
import datetime


class Fascicolo(models.Model):
    _inherit = "sd.fascicolo.fascicolo"

    def fascicolo_aggiungi_documento_action(self):
        context = dict(self._context or {})
        context["fascicolo_id"] = self.id
        context["documents_ids"] = self.documento_ids.ids
        return {
            "type": "ir.actions.act_window",
            "name": _("Add documents"),
            "view_mode": "form",
            "target": "new",
            "res_model": "sd.fascicolo.wizard.fascicolo.aggiungi.documento",
            "context": context,
        }

    def fascicolo_aggiungi_contatto_action(self):
        self.ensure_one()
        context = dict(
            self.env.context,
            fascicolo_id=self.id
        )
        return {
            "name": context.get("wizard_label", ""),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "sd.dms.wizard.document.add.contact",
            "type": "ir.actions.act_window",
            "target": "new",
            "context": context
        }
