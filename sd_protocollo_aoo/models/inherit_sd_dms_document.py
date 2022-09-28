from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class Document(models.Model):
    _inherit = "sd.dms.document"

    @api.model
    def _get_codice_ipa_aoo(self, protocollo):
        codice_ipa = super(Document, self)._get_codice_ipa_aoo(protocollo)
        codice_aoo = self._get_codice_aoo(protocollo)
        if codice_ipa and codice_aoo:
            return "%s - %s" % (codice_ipa, codice_aoo)
        elif codice_ipa:
            return codice_ipa
        elif codice_aoo:
            return codice_aoo
        return ""

    @api.model
    def _get_codice_aoo(self, protocollo):
        return protocollo.aoo_id.cod_aoo
