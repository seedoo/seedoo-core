from odoo import models, fields, api, _

class InheritSdDmsDocumentActions(models.Model):
    _inherit = "sd.dms.document"

    def action_show_dossiers(self):
        # si elimina dal context il valore disassocia_fascicolo_protocollo_id per evitare conflitti nel caso si provenga
        # da una lista di fascicoli di un protocollo (protocollo -> lista fascicoli -> fascicolo -> documenti -> azione
        # di disassociazione documento)
        self = self.with_context(disassocia_fascicolo_protocollo_id=False)
        # se il documento è associato ad un protocollo si deve controllare se l'utente ha i permessi di fascicolazione
        # sul protocollo perché nel caso in cui non li avesse di deve eliminare dal context il valore
        # disassocia_fascicolo_protocollo_id, in modo da rendere il button di disassociazione invisibile
        documento_protocollo_check = self.protocollo_id and self.protocollo_id._is_fascicolazione_disabled()
        if documento_protocollo_check:
            self = self.with_context(disassocia_fascicolo_documento_id=False)
        # si richiama il super con il context aggiornato
        action = super(InheritSdDmsDocumentActions, self).action_show_dossiers()
        # si aggiorna il context della action
        if "disassocia_fascicolo_protocollo_id" in action["context"]:
            action["context"]["disassocia_fascicolo_protocollo_id"] = False
        if documento_protocollo_check and "disassocia_fascicolo_documento_id" in action["context"]:
            action["context"]["disassocia_fascicolo_documento_id"] = False
        return action

    def disassocia_documento(self):
        """
        La disassociazione del documento dal fascicolo avviene senza richiesta di conferma nei seguenti due casi:

        * caso 1: il documento non è associato ha nessun protocollo
        * caso 2: il documento è associato a un protocollo con più di un documento/allegato con la stessa voce di
        titolario del documento di cui si sta richiedendo la disassociazione al fascicolo

        """
        fascicolo_obj = self.env["sd.fascicolo.fascicolo"]
        fascicolo_id = self.env.context.get("disassocia_documento_fascicolo_id", False)
        if not fascicolo_id:
            return
        caso1 = not self.protocollo_id
        if caso1:
            super(InheritSdDmsDocumentActions, self).disassocia_documento()
            return
        documents = self.env["sd.dms.document"].search_read([
            ("protocollo_id", "=", self.protocollo_id.id),
            ("voce_titolario_id", "=", self.voce_titolario_id.id),
            ("fascicolo_ids", "=", fascicolo_id)
        ], ["id"])
        document_ids = [document["id"] for document in documents]
        caso2 = len(document_ids) <= 1
        if caso2:
            fascicolo = fascicolo_obj.browse(fascicolo_id)
            self.protocollo_id.storico_elimina_fascicolazione(fascicolo.nome, True)
            super(InheritSdDmsDocumentActions, self).disassocia_documento()
            return
        context = dict(self.env.context or {})
        context["default_fascicolo_id"] = fascicolo_id
        context["default_protocollo_id"] = self.protocollo_id.id
        context["default_voce_titolario_id"] = self.voce_titolario_id.id
        context["default_documento_ids"] = document_ids
        return {
            "name": _("Documento disassocia fascicolo"),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "sd.protocollo.wizard.documento.disassocia.fascicolo",
            "type": "ir.actions.act_window",
            "target": "new",
            "context": context
        }