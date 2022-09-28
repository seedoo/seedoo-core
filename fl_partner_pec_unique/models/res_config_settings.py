from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # ----------------------------------------------------------
    # Rubrica
    # ----------------------------------------------------------

    unique_pec_mail = fields.Boolean(
        string="Uniqueness of PEC Mail",
        config_parameter="fl_partner_pec_unique.unique_pec_mail"
    )
