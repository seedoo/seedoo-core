from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # ----------------------------------------------------------
    # Interoperabilità
    # ----------------------------------------------------------

    segnatura_xml_invia_pec = fields.Boolean(
        string="Invia \"Segnatura.xml\" (PEC)",
        config_parameter="sd_protocollo.segnatura_xml_invia_pec"
    )

    valida_segnatura_xml_ingresso = fields.Boolean(
        string="Impedisci protocollazione per \"Segnatura.xml\" non valida",
        config_parameter="sd_protocollo.valida_segnatura_xml_ingresso"
    )

    segnatura_xml_invia_email = fields.Boolean(
        string="Invia \"Segnatura.xml\" (e-mail)",
        config_parameter="sd_protocollo.segnatura_xml_invia_email"
    )

    segnatura_xml_parse = fields.Boolean(
        string="Leggi \"Segnatura.xml\"",
        config_parameter="sd_protocollo.segnatura_xml_parse"
    )

    sender_segnatura_xml_parse = fields.Boolean(
        string="Ricava mittente da \"Segnatura.xml\"",
        config_parameter="sd_protocollo.sender_segnatura_xml_parse"
    )

