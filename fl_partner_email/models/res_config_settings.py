from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # ----------------------------------------------------------
    # Rubrica
    # ----------------------------------------------------------

    validity_mail = fields.Boolean(
        string="E-mail validation",
        config_parameter="fl_partner_email.validity_mail"
    )
