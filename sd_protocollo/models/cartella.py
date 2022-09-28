from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProtocolloCartella(models.Model):
    _name = "sd.protocollo.cartella"
    _description = "Cartella per la configurazione del modulo Protocollo sul DMS"
    _rec_name = "company_id"

    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        default=lambda self: self.env.company.id,
        required=True
    )

    protocollo_cartella_id = fields.Many2one(
        string="Cartella Protocolli",
        comodel_name="sd.dms.folder",
        domain="[('company_id','=', company_id)]",
        required=True
    )

    registro_giornaliero_cartella_id = fields.Many2one(
        string="Cartella Registri Giornalieri",
        comodel_name="sd.dms.folder",
        domain="[('company_id','=', company_id)]",
        required=True
    )

    _sql_constraints = [
        (
            "unique",
            "UNIQUE(company_id)",
            "Esiste già una configurazione per la stessa company"
        )
    ]

    @api.onchange("company_id")
    def _onchange_company_id(self):
        self.protocollo_cartella_id = False
        self.registro_giornaliero_cartella_id = False

    @api.model
    def get_domain(self, record):
        domain = [
            ("company_id", "=", record.company_id.id)
        ]
        return domain

    @api.model
    def get_folder(self, record, type):
        if not record or not type:
            return False
        cartella = self.search(self.get_domain(record))
        if not cartella:
            return False
        if type == "protocollo":
            return cartella.protocollo_cartella_id
        if type == "registro_giornaliero":
            return cartella.registro_giornaliero_cartella_id
        return False