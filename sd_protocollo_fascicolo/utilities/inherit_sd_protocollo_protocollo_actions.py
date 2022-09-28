from odoo import models, fields


class ProtocolloActions(models.Model):
    _inherit = "sd.protocollo.protocollo"

    def action_show_dossiers(self):
        self.ensure_one()
        documento_ids = [self.documento_id.id] if self.documento_id else []
        documento_ids += self.allegato_ids.ids
        context = dict(self._context or {})
        #TODO: gestire la creazione di un fascicolo con associazione dei documenti del protocollo
        context["create"] = False
        if not self._is_fascicolazione_disabled():
            context["disassocia_fascicolo_protocollo_id"] = self.id
        return {
            "name": "Fascicoli",
            "view_mode": "tree,form",
            "res_model": "sd.fascicolo.fascicolo",
            "domain": [("documento_ids", "in", documento_ids)],
            "type": "ir.actions.act_window",
            "target": "current",
            "context": context,
        }

    def protocollo_documento_disassocia_fascicoli(self, documenti, fascicolo):
        # Action di disassociazione dei fascicoli collegati ai documenti passando dal protocollo
        self.ensure_one()
        documenti.documento_disassocia_fascicoli([fascicolo.id])
        self.storico_elimina_fascicolazione(fascicolo.nome)
