{
    "name": "Fascicoli - Protocollo",
    "version": "14.0.2.0.0",
    "category": "Document Management",
    "summary": "Aggiunge i Fascicoli al Protocollo",
    "description": """
        Fascicolazione di un documento attraverso il Protocollo
    """,
    "author": "Flosslab",
    "website": "https://www.flosslab.com",
    "license": "LGPL-3",
    "sequence": 0,
    "depends": [
        "sd_protocollo_titolario",
        "sd_fascicolo"
    ],
    "data": [
        "data/inherit_ir_config_parameter.xml",

        "actions/inherit_sd_protocollo_protocollo.xml",
        
        "security/access/wizard.xml",

        "views/inherit_sd_protocollo_protocollo.xml",

        "templates/protocollo_dashboard_template.xml",

        "wizards/inherit_res_config_settings.xml",
        "wizards/protocollo_fascicola.xml",
        "wizards/documento_disassocia_fascicolo.xml",

        "static/src/templates/web_templates.xml"

    ],
    "installable": True,
    "application": False,
    "auto_install": False
}
