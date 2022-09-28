from odoo import models


class Document(models.Model):
    _inherit = "sd.dms.document"

    def _compute_field_readonly(self):
        super(Document, self)._compute_field_readonly()
        for rec in self:
            # il documento è modificabile quando:
            # - il campo field_readonly è a False
            # - il protocollo non è stato creato a partire da una mail in ingresso
            field_readonly = True
            if not rec.field_readonly and not (rec.protocollo_id.tipologia_protocollo == "ingresso" and rec.protocollo_id.mail_id):
                field_readonly = False
            rec.field_readonly = field_readonly

    def _compute_document_type_id_readonly(self):
        super(Document, self)._compute_document_type_id_readonly()
        for rec in self:
            # se sono verificate le seguenti condizioni si devono sovrascrivere le condizioni base per rendere il campo
            # document_type_id readonly:
            # - il campo protocollo_id è valorizzato
            # - il protocollo associato è ancora in stato bozza
            if rec.protocollo_id and rec.protocollo_id.state=="bozza":
                rec.document_type_id_readonly = False