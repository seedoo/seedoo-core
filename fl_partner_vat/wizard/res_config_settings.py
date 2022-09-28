from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    vat_unique = fields.Boolean(
        string="Uniqueness VAT number",
        help="Check the uniqueness of the VAT number",
        config_parameter="fl_partner_vat.vat_unique"
    )

    vat_mandatory = fields.Boolean(
        string="VAT number mandatory",
        help="VAT number mandatory for companies",
        config_parameter="fl_partner_vat.vat_mandatory"
    )
