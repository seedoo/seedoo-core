from odoo import models, api, fields, _


SELECTION_EMAIL_ADDRESS_TYPE = [
    ("pec_mail", "PEC e-mail")
]

class PartnerDigitalDomicile(models.Model):
    _name = "res.partner.digital.domicile"
    _description = "Partner digital domicile"
    _inherit = "res.partner.email.mixin"
    _rec_name = "email_address"
    _partner_id_field = "aoo_id"

    aoo_id = fields.Many2one(
        string="AOO",
        comodel_name="res.partner",
        domain=[('is_aoo', '=', True)],
        required=True,
        ondelete="cascade"
    )

    aoo_id_name = fields.Char(
        string="AOO",
        related="aoo_id.name",
        readonly=True
    )

    type = fields.Selection(
        string="Type",
        selection=SELECTION_EMAIL_ADDRESS_TYPE,
        default="pec_mail",
        required=True
    )

    email_address = fields.Char(
        string="PEC mail address",
        required=True
    )

    @api.model
    def get_uniqueness_mail_domain(self, mail_type, value, model_name, check_id, parent_id=False):
        domain = [("type", "=", mail_type), ("email_address", "=", value)]
        if model_name == self._name and check_id:
            domain.append(("id", "!=", check_id))
        # si aggiunge la gestione di un coso particolare nella univocità della pec mail: un domicilio digitale può avere
        # la stessa pec mail della pa o gps associata alla propria AOO
        elif model_name != self._name and model_name == "res.partner" and check_id:
            aoo_data_list = self.env["res.partner"].search_read([
                ("is_aoo", "=", True),
                ("amministrazione_id", "=", check_id),
            ], ["id"])
            aoo_ids = [aoo_data["id"] for aoo_data in aoo_data_list]
            domain.append(("aoo_id", "not in", aoo_ids))
        return domain