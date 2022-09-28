from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # ----------------------------------------------------------
    # E-mail/PEC
    # ----------------------------------------------------------

    inserisci_testo_pec = fields.Boolean(
        string="Testo messaggio PEC",
        config_parameter="sd_protocollo.inserisci_testo_pec"
    )

    rinomina_oggetto_mail_pec = fields.Boolean(
        string="Rinomina oggetto e-mail/PEC",
        config_parameter="sd_protocollo.rinomina_oggetto_mail_pec"
    )

    modifica_documenti_pec = fields.Boolean(
        string="Abilita modifica documenti in stato bozza",
        config_parameter="sd_protocollo.modifica_documenti_pec"
    )

    lunghezza_massima_oggetto_mail = fields.Integer(
        string="Lunghezza massima dell'oggetto dell'e-mail",
        config_parameter="sd_protocollo.lunghezza_massima_oggetto_mail",
    )

    lunghezza_massima_oggetto_pec = fields.Integer(
        string="Lunghezza massima dell'oggetto della PEC",
        config_parameter="sd_protocollo.lunghezza_massima_oggetto_pec",
    )

    # ----------------------------------------------------------
    # Protocollazione PEC
    # ----------------------------------------------------------

    select_eml_pec = fields.Boolean(
        string="Protocolla busta di trasporto PEC (file .eml)",
        config_parameter="sd_protocollo.select_eml_pec",
    )

    select_body_pec = fields.Boolean(
        string="Protocolla corpo del messaggio PEC",
        config_parameter="sd_protocollo.select_body_pec",
    )

    select_postacert_eml_pec = fields.Boolean(
        string="Protocolla messaggio PEC (file .eml)",
        config_parameter="sd_protocollo.select_postacert_eml_pec"
    )

    select_attachments_pec = fields.Boolean(
        string="Protocolla allegati del messaggio PEC",
        config_parameter="sd_protocollo.select_attachments_pec",
    )