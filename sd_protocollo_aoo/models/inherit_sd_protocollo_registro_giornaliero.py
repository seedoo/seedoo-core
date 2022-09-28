from odoo import models, fields, api


class RegistroGiornaliero(models.Model):
    _inherit = "sd.protocollo.registro.giornaliero"

    aoo_id = fields.Many2one(
        string="AOO",
        comodel_name="fl.set.set",
        domain="[('company_id', '=', company_id), ('set_type', '=', 'aoo')]",
        required=True
    )

    _sql_constraints = [
        (
            "unique",
            "UNIQUE(data, company_id, aoo_id)",
            "Esiste già un registro per la stessa data e AOO"
        )
    ]

    @api.onchange("company_id")
    def _default_aoo_id(self):
        aoo_id = False
        if self.env.user.get_aoo_id_readonly():
            aoo_id = self.env.user.fl_set_set_ids[0].aoo_id.id
        self.aoo_id = aoo_id

    @api.onchange("company_id")
    def _onchange_company_id(self):
        self.aoo_id = False

    def get_protocollo_domain(self):
        domain = super(RegistroGiornaliero, self).get_protocollo_domain()
        domain.append(("aoo_id", "=", self.aoo_id.id))
        return domain

    @api.model
    def crea_registro_giornaliero(self, **kwargs):
        registro_obj = self.env["sd.protocollo.registro"]
        aoo_list = self.env["fl.set.set"].search([
            ("set_type", "=", "aoo"),
            ("company_id", "=", kwargs["company_id"])
        ])
        for aoo in aoo_list:
            if registro_obj.search([("ufficiale", "=", True), ("aoo_id", "=", aoo.id)], count=True) == 0:
                continue
            kwargs["aoo_id"] = aoo.id
            super(RegistroGiornaliero, self).crea_registro_giornaliero(**kwargs)
