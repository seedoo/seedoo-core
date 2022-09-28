from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class RegistroGiornalieroConfigurazione(models.Model):
    _inherit = "sd.protocollo.registro.giornaliero.configurazione"

    documento_id_voce_titolario_id = fields.Many2one(
        string="Classificazione",
        comodel_name="sd.dms.titolario.voce.titolario",
        domain="[('titolario_id.active','=',True), ('titolario_id.state','=',True), ('parent_active', '=', True), ('titolario_company_id','=', company_id )]",
        required=1
    )

    def _get_protocollo_values(self):
        self.ensure_one()
        values = super(RegistroGiornalieroConfigurazione, self)._get_protocollo_values()
        values.update({
            "documento_id_voce_titolario_id": self.documento_id_voce_titolario_id.id
        })
        return values