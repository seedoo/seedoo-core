from odoo import models, fields

SELECTION_VOCI_TITOLARIO_SELEZIONABILI = [
    ("all", "Tutte"),
    ("only_child", "Voci Senza Figli")
]


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # ----------------------------------------------------------
    # zTree Widget
    # ----------------------------------------------------------

    ztree_widget_config = fields.Selection(
        string="Voci di titolario selezionabili",
        selection=SELECTION_VOCI_TITOLARIO_SELEZIONABILI,
        config_parameter="sd_dms.ztree_widget_config"
    )
