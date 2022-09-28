from odoo import models, fields, api, _


class InheritSdFascicoloDocumentoAggiungiFascicolo(models.TransientModel):
    _inherit = "sd.fascicolo.wizard.documento.aggiungi.fascicolo"



    def write_dossiers(self):
        result = super(InheritSdFascicoloDocumentoAggiungiFascicolo, self).write_dossiers()
        document_obj = self.env["sd.dms.document"]
        document_id = self.env.context.get("document_id", False)
        document = document_obj.browse(document_id)
        if not document.protocollo_id:
            return result
        new_document_list = document_obj.search([
            ("id", "!=", document.id),
            ("protocollo_id", "=", document.protocollo_id.id),
            ("voce_titolario_id", "=", document.voce_titolario_id.id),
            ("fascicolo_ids", "=", False)
        ])
        for new_document in new_document_list:
            new_document.documento_aggiungi_fascicoli([self.fascicolo_id.id])
        return result