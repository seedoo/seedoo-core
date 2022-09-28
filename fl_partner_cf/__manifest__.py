{
    "name": "Partner CF",
    "version": "14.0.2.0.0",
    "category": "",
    "summary": "Adds the CF field to the partner",
    "description": "",
    "author": "Flosslab",
    "website": "https://www.flosslab.com",
    "license": "LGPL-3",
    "sequence": 0,
    "depends": [
        "fl_partner_vat"
    ],
    "external_dependencies": {
        "python": [
            "codicefiscale==0.9"
        ],
    },
    "data": [
        "security/ir.model.access.csv",

        "data/res.city.it.code.csv",

        "view/res_partner.xml",
        "view/res_company.xml",

        "wizard/compute_fc.xml",
        "wizard/res_config_settings.xml",

    ],
    "installable": True,
    "application": False,
    "auto_install": False
}
