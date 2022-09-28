from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # ----------------------------------------------------------
    # Base Addons
    # ----------------------------------------------------------

    module_fl_set_pa = fields.Boolean(
        string="Abilita AOO e UO",

    )
