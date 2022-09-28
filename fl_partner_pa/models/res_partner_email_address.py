from odoo import models, api, fields, _


SELECTION_EMAIL_ADDRESS_TYPE = [
    ("email", "e-mail"),
    ("pec_mail", "PEC e-mail")
]

class PartnerEmailAddress(models.Model):
    _name = "res.partner.email.address"
    _description = "Partner e-mail address"
    _inherit = "res.partner.email.mixin"
    _rec_name = "email_address"
    _partner_id_field = "partner_id"

    partner_id = fields.Many2one(
        string="Partner",
        comodel_name="res.partner",
        required=True,
        ondelete="cascade"
    )

    type = fields.Selection(
        string="Type",
        selection=SELECTION_EMAIL_ADDRESS_TYPE,
        required=True
    )

    email_address = fields.Char(
        string="E-mail address",
        required=True
    )

    @api.model
    def get_uniqueness_mail_domain(self, mail_type, value, model_name, check_id, parent_id=False):
        domain = [("type", "=", mail_type), ("email_address", "=", value)]
        if model_name == self._name and check_id:
            domain.append(("id", "!=", check_id))
        return domain