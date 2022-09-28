from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class Registro(models.Model):
    _inherit = "sd.protocollo.registro.emergenza"

    aoo_id = fields.Many2one(
        string="AOO",
        related="registro_id.aoo_id",
        readonly=True
    )

    def _get_domain_registro_emergenza_aperto(self, rec):
        domain = super(Registro, self)._get_domain_registro_emergenza_aperto(rec)
        domain.append(("aoo_id", "=", rec.aoo_id.id))
        return domain
