from odoo import models, api


class InheritSdFascicoloFascicoloAggiungiDocumento(models.TransientModel):
    _inherit = "sd.fascicolo.wizard.fascicolo.aggiungi.documento"

    def write_documents(self):
        new_document_ids = []
        documento_ids = self.documento_ids.ids
        document_obj = self.env["sd.dms.document"]
        document_data_list = document_obj.search_read([
            ("id", "in", documento_ids),
            ("protocollo_id", "!=", False),
        ], ["id", "protocollo_id", "voce_titolario_id"])
        for document_data in document_data_list:
            new_document_data_list = document_obj.search_read([
                ("id", "not in", documento_ids),
                ("protocollo_id", "=", document_data["protocollo_id"][0]),
                ("voce_titolario_id", "=", document_data["voce_titolario_id"][0]),
                ("fascicolo_ids", "=", False)
            ], ["id"])
            for new_document_data in new_document_data_list:
                new_document_ids.append(new_document_data["id"])
        self.documento_ids = [(6, 0, documento_ids + new_document_ids)]
        super(InheritSdFascicoloFascicoloAggiungiDocumento, self).write_documents()