from odoo import models, fields, api, _


class Protocollo(models.Model):
    _inherit = "sd.protocollo.protocollo"

    def classifica_documento(self, new_voce_titolario=False, old_voce_titolario=False, before_competenza="", after_competenza=""):
        self.ensure_one()
        before_classificazione = old_voce_titolario.path_name if old_voce_titolario else ""
        after_classificazione = new_voce_titolario.path_name if new_voce_titolario else ""
        # Aggiornamento del name della voce di titolario
        if new_voce_titolario:
            self.documento_id.voce_titolario_name = after_classificazione
        self.storico_classifica_documento(
            before_classificazione,
            after_classificazione,
            "",
            before_competenza,
            after_competenza
        )

    @api.model
    def verifica_campi_obbligatori(self):
        errors = super(Protocollo, self).verifica_campi_obbligatori()
        if self.documento_id_document_type_id and \
                self.documento_id_document_type_id.classification_required and \
                not self.documento_id.voce_titolario_id:
            if errors:
                errors.append("Classificazione")
            else:
                errors = ["Classificazione"]

        if self.documento_id_document_type_id and \
                self.documento_id_document_type_id.classification_required and \
                self.documento_id.voce_titolario_id:
            error_classificazione_allegati = False
            for allegato in self.allegato_ids:
                if allegato.voce_titolario_id.id != self.documento_id.voce_titolario_id.id:
                    error_classificazione_allegati = True
                    break
            if error_classificazione_allegati:
                error_string = "Gli allegati hanno una classificazione diversa dal documento principale"
                if errors:
                    errors.append(error_string)
                else:
                    errors = [error_string]
        return errors

    def _get_context_for_list_allegati(self):
        context = super(Protocollo, self)._get_context_for_list_allegati()
        if self.documento_id_voce_titolario_id:
            context = dict(
                context,
                default_voce_titolario_id=self.documento_id_voce_titolario_id.id
            )
        return context