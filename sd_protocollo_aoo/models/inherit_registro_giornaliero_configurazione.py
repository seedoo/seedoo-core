from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class RegistroGiornalieroConfigurazione(models.Model):
    _inherit = "sd.protocollo.registro.giornaliero.configurazione"

    _sql_constraints = [
        (
            "unique",
            "UNIQUE(company_id, aoo_id)",
            "Esiste già una configurazione per la AOO"
        )
    ]

    aoo_id = fields.Many2one(
        string="AOO",
        comodel_name="fl.set.set",
        domain="[('company_id', '=', company_id), ('set_type', '=', 'aoo')]",
        required=True
    )

    protocollatore_ufficio_id = fields.Many2one(
        domain="[('company_id', '=', company_id), ('set_type', '=', 'uo')]",
    )

    @api.depends("aoo_id")
    def _compute_nome(self):
        super(RegistroGiornalieroConfigurazione, self)._compute_nome()
        for rec in self:
            if rec.aoo_id:
                rec.nome = "Configurazione Registro Giornaliero - %s" % rec.aoo_id.name

    @api.onchange("company_id")
    def _onchange_company_id(self):
        self.aoo_id = False

    def _get_protocollo_values(self):
        self.ensure_one()
        values = super(RegistroGiornalieroConfigurazione, self)._get_protocollo_values()
        values.update({
            "aoo_id": self.aoo_id.id
        })
        return values