from odoo import models, fields


class Document(models.Model):
    _inherit = "sd.dms.document"

    button_modifica_allegati_invisible = fields.Boolean(
        string="button modifica allegati invisible",
        related="protocollo_id.button_modifica_allegati_invisible"
    )

    def _compute_field_readonly(self):
        super(Document, self)._compute_field_readonly()
        for rec in self:
            # il documento è modificabile quando:
            # - il campo field_readonly è a False
            # - il campo button_modifica_allegati_invisible è a False
            # - il documento è un allegato del protocollo
            field_readonly = True
            if not rec.field_readonly and not rec.button_modifica_allegati_invisible and rec.id != rec.protocollo_id.documento_id.id:
                field_readonly = False
            rec.field_readonly = field_readonly

    def _compute_button_document_add_contact_sender_invisible(self):
        super(Document, self)._compute_button_document_add_contact_sender_invisible()
        for rec in self:
            if rec.button_document_add_contact_sender_invisible:
                continue
            # l'aggiunta dei mittenti può essere fatta solo passando dal protocollo
            if rec.protocollo_id:
                rec.button_document_add_contact_sender_invisible = True

    def _compute_button_document_add_contact_recipient_invisible(self):
        super(Document, self)._compute_button_document_add_contact_recipient_invisible()
        for rec in self:
            if rec.button_document_add_contact_recipient_invisible:
                continue
            # l'aggiunta dei destinatari può essere fatta solo passando dal protocollo
            if rec.protocollo_id:
                rec.button_document_add_contact_recipient_invisible = True
