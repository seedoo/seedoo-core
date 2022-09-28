from odoo import models, fields

SELECTION_NOMENCLATURA_FASCICOLO = [
    ("classificazione", "Classificazione")
]


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    nomenclatura_fascicolo = fields.Selection(
        string="Nomenclatura fascicolo",
        selection=SELECTION_NOMENCLATURA_FASCICOLO,
        config_parameter="sd_fascicolo.nomenclatura_fascicolo"
    )
