{
    "name": "Titolario - Documents",
    "version": "14.0.2.0.0",
    "category": "Document Management",
    "summary": "Classificazione dei documenti mediante titolario",
    "description": "",
    "author": "Flosslab",
    "website": "https://www.flosslab.com",
    "license": "LGPL-3",
    "sequence": 0,
    "depends": [
        "sd_dms",
        "web",
    ],
    "data": [
        "security/access/titolario.xml",
        "security/access/voce_titolario.xml",
        "security/rule/titolario.xml",

        "actions/titolario.xml",

        "views/inherit_sd_dms_titolario.xml",
        "views/inherit_sd_dms_voce_titolario.xml",
        "views/inherit_sd_dms_document.xml",
        "views/inherit_sd_dms_document_type.xml",

        "menu/action.xml",
        "menu/items.xml",

        "wizards/inherit_res_config_settings.xml",

        "template/assets.xml",

        "data/ir_config_parameter.xml"
    ],
    "installable": True,
    "application": False,
    "auto_install": False
}
