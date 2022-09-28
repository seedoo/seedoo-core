{
    "name": "Partner VAT",
    "version": "14.0.2.0.0",
    "category": "",
    "summary": "Adds the VAT field to the partner",
    "description": "",
    "author": "Flosslab",
    "website": "https://www.flosslab.com",
    "license": "LGPL-3",
    "sequence": 0,
    "depends": [
        "base_setup"
    ],
    "external_dependencies": {
        "python": [
            "vatnumber"
        ],
    },
    "data": [
        "views/res_company.xml",
        "views/res_partner.xml",

        "wizard/res_config_settings.xml"
    ],
    "installable": True,
    "application": False,
    "auto_install": False
}
