{
    "name": "Titolario - Protocollo",
    "version": "14.0.2.0.0",
    "category": "",
    "summary": "Aggiunge il titolario al Protocollo",
    "description": """
        Modulo per la classificazione di un documento attraverso il Protocollo
    """,
    "author": "Flosslab",
    "website": "https://www.flosslab.com",
    "license": "LGPL-3",
    "sequence": 0,
    "depends": [
        "sd_protocollo",
        "sd_dms_titolario",
        "fl_onchange_action"
    ],
    "data": [
        "data/ir_config_parameter.xml",
        "data/inherit_sd_dms_document_type.xml",

        "actions/protocollo.xml",

        "security/access/wizard.xml",

        "views/res_config_settings.xml",
        "views/sd_dms_titolario_voce_titolario.xml",
        "views/sd_protocollo_protocollo.xml",
        "views/inherit_sd_protocollo_registro_giornaliero_configurazione.xml",

        "templates/protocollo_dashboard_template.xml",

        "wizards/protocollo_carica_documento_view.xml",
        "wizards/protocollo_classifica_documento_view.xml",
        "wizards/inherit_sd_protocollo_protocollo_registra.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False
}
