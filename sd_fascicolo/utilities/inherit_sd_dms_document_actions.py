from odoo import models, fields, api, _

class Document(models.Model):
    _inherit = "sd.dms.document"

    def action_show_dossiers(self):
        self.ensure_one()
        context = dict(self._context or {})
        context["default_documento_ids"] = [(6, 0, self.ids)]
        context["disassocia_fascicolo_documento_id"] = self.id
        #TODO: gestire la creazione di un fascicolo con associazione del documento
        context["create"] = False
        return {
            "name": _("Dossiers"),
            "view_mode": "tree,form",
            "res_model": "sd.fascicolo.fascicolo",
            "domain": [("documento_ids", "=", self.id)],
            "type": "ir.actions.act_window",
            "target": "current",
            "context": context,
        }

    def documento_aggiungi_fascicoli(self, fascicolo_ids):
        self.ensure_one()
        self.write({
            "fascicolo_ids": [(4, fascicolo_id) for fascicolo_id in fascicolo_ids]
        })

    def documento_disassocia_fascicoli(self, fascicolo_ids):
        fascicolo_obj = self.env["sd.fascicolo.fascicolo"]
        to_unlink_list = []
        for fascicolo_id in fascicolo_ids:
            to_unlink_list.append((3, fascicolo_id))
            fascicolo = fascicolo_obj.browse(fascicolo_id)
            fascicolo.storico_disassocia_documento(self.ids, True)
        self.write({"fascicolo_ids": to_unlink_list})

    def disassocia_documento(self):
        self.ensure_one()
        fascicolo_id = self.env.context.get("disassocia_documento_fascicolo_id", False)
        if not fascicolo_id:
            return
        self.documento_disassocia_fascicoli([fascicolo_id])