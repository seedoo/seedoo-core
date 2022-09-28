from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # ----------------------------------------------------------
    # Rubrica
    # ----------------------------------------------------------

    unique_mail = fields.Boolean(
        string="Uniqueness of e-mail",
        config_parameter="fl_partner_email_unique.unique_mail"
    )

