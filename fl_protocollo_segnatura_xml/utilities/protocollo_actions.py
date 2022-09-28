from odoo import models
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class Protocollo(models.Model):
    _inherit = "sd.protocollo.protocollo"

    def scarica_segnatura_xml(self):
        self.ensure_one()
        if self.segnatura_xml:
            return {
                "type": "ir.actions.act_url",
                "url": "/protocollo/segnatura_xml/%s" % self.id
            }
        raise ValidationError("Segnatura XML non disponibile")

    def aggiorna_segnatura_xml(self, mail_list=False):
        if self.tipologia_protocollo == "ingresso" or self.state == "bozza":
            return
        segnatura_xml = False
        try:
            segnatura_xml = self.get_segnatura_xml(mail_list)
            if segnatura_xml:
                self.interoperability = "2021"
        except Exception as e:
            _logger.error(e)
        self.segnatura_xml = segnatura_xml

    def _add_fields_to_recompute(self):
        super(Protocollo, self)._add_fields_to_recompute()
        # se viene creato un nuovo allegato quando il prot. è registrato viene recomputata la segnatura_xml
        # self.recompute(["segnatura_xml"])
        self.env.add_to_compute(self._fields["segnatura_xml"], self)
