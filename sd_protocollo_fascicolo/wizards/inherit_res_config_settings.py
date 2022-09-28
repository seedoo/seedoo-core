from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    non_fascicolati_active = fields.Boolean(
        string="Visualizza box \"Da fascicolare\"",
        config_parameter="sd_protocollo.non_fascicolati_active"
    )
