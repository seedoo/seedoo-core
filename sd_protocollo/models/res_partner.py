from odoo import models, fields, api

SELECTION_PA_TYPE = [
    ("ente", "Ente"),
    ("aoo", "AOO"),
    ("uo", "UO")
]

LIST_HAS_CHANGE = [
    "name", "display_name", "company_type", "cod_amm", "cod_aoo", "cod_ou", "website", "vat", "function", "fiscalcode",
    "street", "street2", "zip", "city", "state_id", "country_id", "email", "pec_mail", "phone", "mobile", "title"
]


class ResPartner(models.Model):
    _inherit = "res.partner"

    has_changed = fields.Boolean(
        string="Has Change",
        default=False,
        store=False
    )

    protocollo_ids_count = fields.Integer(
        string="# Dossiers",
        compute="_compute_protocollo_ids_count",
    )

    @api.onchange(*LIST_HAS_CHANGE)
    def _onchange_has_change(self):
        # Il campo has_change viene cambiato ogni volta che si modifica un campo nella vista, questo attiva il trigger
        # dell' api.depends, che avendo il campo store settato a False non viene salvato alla chiusura dell'istanza e quindi
        # alla modifica sarà possibile riattivare il campo triggger
        self.ensure_one()
        self.has_changed = True

    def _compute_protocollo_ids_count(self):
        protocollo_obj = self.env["sd.protocollo.protocollo"]
        for rec in self:
            protocollo_ids_count = protocollo_obj.search([
                "|",
                ("destinatario_ids.partner_id", "=", self.id),
                ("mittente_ids.partner_id", "=", self.id)
            ], count=True)
            rec.protocollo_ids_count = protocollo_ids_count
