{
    "name": "Fascicoli",
    "version": "14.0.2.0.0",
    "category": "Document Management",
    "summary": "Organizza i documenti in fascicoli digitali",
    "description": """
    APP per la gestione del fascicolo digitale (fascicolo, sotto-fascicolo, inserto).
    """,
    "author": "Flosslab",
    "website": "https://www.flosslab.com",
    "license": "LGPL-3",
    "sequence": 0,
    "depends": [
        "sd_dms",
        "sd_dms_titolario",
        "fl_partner_pa",
        "fl_utility"
    ],
    "data": [
        "data/inherit_ir_config_parameter.xml",

        "security/categories.xml",
        "security/groups.xml",
        "security/access/fascicolo.xml",
        "security/access/fascicolo_acl.xml",
        "security/access/fascicolo_document_acl.xml",
        "security/access/wizard.xml",
        "security/rule/fascicolo.xml",

        "menu/action.xml",
        "menu/items.xml",

        "views/fascicolo.xml",
        "views/fascicolo_acl.xml",
        "views/fascicolo_document_acl.xml",
        "views/inherit_sd_dms_document.xml",
        "views/inherit_res_partner.xml",

        "wizards/inherit_res_config_settings.xml",
        "wizards/documento_aggiungi_fascicolo.xml",
        "wizards/fascicolo_aggiungi_documento.xml",

        "actions/inherit_sd_dms_document.xml"
    ],
    "installable": True,
    "application": True,
    "auto_install": False
}
