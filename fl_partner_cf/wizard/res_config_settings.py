from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    fiscalcode_unique = fields.Boolean(
        string="Uniqueness of fiscal code",
        help="Check the uniqueness of the fiscal code",
        config_parameter="fl_partner_cf.fiscalcode_unique"
    )

    compute_fiscalcode = fields.Boolean(
        string="Compute fiscal code",
        help="Enable computation of fiscal code",
        config_parameter="fl_partner_cf.compute_fiscalcode"
    )
