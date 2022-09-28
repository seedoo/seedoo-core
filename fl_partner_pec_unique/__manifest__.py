{
    "name": "Partner PEC unique",
    "version": "14.0.2.0.0",
    "category": "",
    "summary": "Adds PEC uniqueness check for the partner",
    "description": "",
    "author": "Flosslab",
    "website": "https://www.flosslab.com",
    "license": "LGPL-3",
    "sequence": 0,
    "depends": [
        "fl_partner_email_unique",
        "fl_partner_pec"
    ],
    "external_dependencies": {
    },
    "data": [
        "data/ir_config_parameter.xml",

        "views/res_config_settings.xml"
    ],
    "installable": True,
    "application": False,
    "auto_install": False
}
