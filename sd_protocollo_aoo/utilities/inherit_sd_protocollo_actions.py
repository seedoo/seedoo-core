from odoo import models
import logging

_logger = logging.getLogger(__name__)


class Protocollo(models.Model):
    _inherit = "sd.protocollo.protocollo"

    def _get_domain_mezzo_trasmissione(self):
        if self.mezzo_trasmissione_id.integrazione == "pec":
            return True
        return False

    def _get_domain_numero_protocollo_emergenza(self, protocollo):
        domain = super(Protocollo, self)._get_domain_numero_protocollo_emergenza(protocollo)
        domain.append(("aoo_id", "=", protocollo.aoo_id.id))
        return domain

    class ProtocolloActions(models.Model):
        _inherit = "sd.protocollo.protocollo"

    def get_reply_values(self):
        values = super(Protocollo, self).get_reply_values()
        values["aoo_id"] = self.aoo_id.id
        return values