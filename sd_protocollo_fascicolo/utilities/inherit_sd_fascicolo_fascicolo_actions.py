from odoo import models, _


class InheritSdFascicoloFascicoloActions(models.Model):
    _inherit = "sd.fascicolo.fascicolo"

    def disassocia_fascicolo(self):
        self.ensure_one()
        # se nel context è presente il valore disassocia_fascicolo_protocollo_id allora si sta disassociando il
        # fascicolo da un protocollo (action eseguita dalla lista dei fascicoli di un protocollo), quindi si devono
        # disassociare tutti i documenti del protocollo con la stessa voce di titolario
        protocollo_id = self.env.context.get("disassocia_fascicolo_protocollo_id", False)
        if protocollo_id:
            document_data_list = self.env["sd.dms.document"].search_read([
                ("protocollo_id", "=", protocollo_id),
                ("voce_titolario_id", "=", self.voce_titolario_id.id),
                ("fascicolo_ids", "=", self.id)
            ], ["id"])
            documento_ids = [document_data["id"] for document_data in document_data_list]
            self.fascicolo_disassocia_documenti(documento_ids)
            return
        # se la action di disassociazione viene invece eseguita a partire dalla lista fascicoli di un documento allora
        # si deve controllare comunque che il documento che si sta cercando di disassociare non sia associato ad un
        # protocollo
        documento_id = self.env.context.get("disassocia_fascicolo_documento_id", False)
        documento_ids = [documento_id]
        documento = self.env["sd.dms.document"].browse(documento_id)
        protocollo = documento.protocollo_id
        if protocollo:
            # nel caso in cui il documento fosse associato ad un protocollo si applica lo stesso ragionamento precedente
            # e quindi si ricercando i documenti con stesso protocollo, voce di titolario del documento che si sta
            # cercando di disassaciare
            document_data_list = self.env["sd.dms.document"].search_read([
                ("protocollo_id", "=", protocollo.id),
                ("voce_titolario_id", "=", self.voce_titolario_id.id),
                ("fascicolo_ids", "=", self.id)
            ], ["id"])
            documento_ids = [document_data["id"] for document_data in document_data_list]
        # se la lista dei documenti da disassociare è minore o guale a 1 allora avviene la disassociazione diretta
        if len(documento_ids) <= 1:
            self.fascicolo_disassocia_documenti(documento_ids)
            return
        # se invece la lista dei documenti da disassociare è maggiore di 1 allora di deve passare per il wizard di
        # richiesta conferma
        context = dict(self.env.context or {})
        context["default_fascicolo_id"] = self.id
        context["default_protocollo_id"] = protocollo.id
        context["default_voce_titolario_id"] = self.voce_titolario_id.id
        context["default_documento_ids"] = documento_ids
        return {
            "name": _("Documento disassocia fascicolo"),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "sd.protocollo.wizard.documento.disassocia.fascicolo",
            "type": "ir.actions.act_window",
            "target": "new",
            "context": context
        }

    def fascicolo_disassocia_documenti(self, documento_ids):
        document_obj = self.env["sd.dms.document"]
        protocollo = document_obj.browse(documento_ids[0]).protocollo_id
        # Rimozione del documento/i dal fascicolo con conseguente rimozione del fascicolo dal protocollo
        if protocollo:
            protocollo.storico_elimina_fascicolazione(self.nome)
        super(InheritSdFascicoloFascicoloActions, self).fascicolo_disassocia_documenti(documento_ids)

    def fascicolo_aggiungi_documenti(self, documento_ids, from_document=True):
        document_obj = self.env["sd.dms.document"]
        protocollo_obj = self.env["sd.protocollo.protocollo"]
        super(InheritSdFascicoloFascicoloActions, self).fascicolo_aggiungi_documenti(documento_ids)

        protocollo_ids = []
        for documento_id in documento_ids:
            documento = document_obj.browse(documento_id)
            if not documento.protocollo_id:
                continue
            if documento.protocollo_id.id not in protocollo_ids:
                protocollo_ids.append(documento.protocollo_id.id)

        if from_document:
            for protocollo_id in protocollo_ids:
                protocollo_obj.browse(protocollo_id).storico_aggiungi_fascicolazione_da_fascicolo(self.nome)
