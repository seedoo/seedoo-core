from odoo import models, fields, api


class RegistroGiornaliero(models.Model):
    _inherit = "sd.protocollo.registro.giornaliero"

    aoo_id_readonly = fields.Boolean(
        string="visibilità aoo_id readonly",
        compute="_compute_aoo_id_readonly"
    )

    @api.depends("company_id")
    def _compute_aoo_id_readonly(self):
        for rec in self:
            rec.aoo_id_readonly = self.env.user.get_aoo_id_readonly() if rec.aoo_id else False
