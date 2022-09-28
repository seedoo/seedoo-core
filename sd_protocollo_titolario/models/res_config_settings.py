from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # ----------------------------------------------------------
    # Dashboard
    # ----------------------------------------------------------

    non_classificati_active = fields.Boolean(
        string="Visualizza box \"Da classificare\"",
        config_parameter="sd_protocollo.non_classificati_active"
    )

    # ----------------------------------------------------------
    # Altri
    # ----------------------------------------------------------

    sostituisci_assegnatari = fields.Boolean(
        string="Sostituisci assegnatari default in modifica classificazione",
        config_parameter="sd_protocollo.sostituisci_assegnatari"
    )

    modifica_classificazione = fields.Boolean(
        string="Assegnatario competenza può modificare la classificazione",
        config_parameter="sd_protocollo.modifica_classificazione"
    )
