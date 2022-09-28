from odoo import models, fields, api, _
import logging
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class Registro(models.Model):
    _inherit = "sd.protocollo.registro"

    aoo_id = fields.Many2one(
        string="AOO",
        comodel_name="fl.set.set",
        domain="[('company_id', '=', company_id),('set_type', '=', 'aoo')]",
        required=True
    )

    @api.model
    def get_domain_can_used_to_protocol(self):
        domain = super(Registro, self).get_domain_can_used_to_protocol()
        if not self.env.context.get("aoo_id", False):
            return domain
        domain.append(("aoo_id", "=", self.env.context.get("aoo_id")))
        return domain

    @api.constrains("company_id", "ufficiale", "aoo_id")
    def _validate_registro(self):
        return super(Registro, self)._validate_registro()

    def _check_registro(self, registro):
        super(Registro, self)._check_registro(registro)
        check_aoo_id = False
        if self.search_count([("ufficiale", "=", True), ("company_id", "=", registro.company_id.id),
                              ("aoo_id", "=", registro.aoo_id.id)]) > 1:
            check_aoo_id = "Il registro ufficiale è univoco per Company e per AOO"
        return check_aoo_id

    def _get_domain_configurazione_registro_giornaliero(self):
        domain = super(Registro, self)._get_domain_configurazione_registro_giornaliero()
        domain.append(("aoo_id", "=", self.aoo_id.id))
        return domain
