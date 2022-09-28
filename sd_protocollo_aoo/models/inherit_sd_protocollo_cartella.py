from odoo import models, fields, api


class Cartella(models.Model):
    _inherit = "sd.protocollo.cartella"

    aoo_id = fields.Many2one(
        string="AOO",
        comodel_name="fl.set.set",
        domain="[('company_id', '=', company_id), ('set_type', '=', 'aoo')]",
        required=True
    )

    protocollo_cartella_id = fields.Many2one(
        domain="[('company_id', '=', company_id), ('aoo_id','=', aoo_id)]"
    )

    registro_giornaliero_cartella_id = fields.Many2one(
        domain="[('company_id', '=', company_id), ('aoo_id','=', aoo_id)]"
    )

    _sql_constraints = [
        (
            "unique",
            "UNIQUE(company_id, aoo_id)",
            "Esiste già una configurazione per la stessa AOO"
        )
    ]

    @api.onchange("company_id")
    def _onchange_company_id(self):
        aoo_id = False
        if self.env.user.get_aoo_id_readonly():
            aoo_id = self.env.user.fl_set_set_ids[0].aoo_id.id
        self.aoo_id = aoo_id

    @api.onchange("aoo_id")
    def _onchange_aoo_id(self):
        self.protocollo_cartella_id = False
        self.registro_giornaliero_cartella_id = False

    @api.model
    def get_domain(self, record):
        domain = super(Cartella, self).get_domain(record)
        domain.append(("aoo_id", "=", record.aoo_id.id))
        return domain