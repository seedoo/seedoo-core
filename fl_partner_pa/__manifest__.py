{
    "name": "Partner PA",
    "version": "14.0.2.0.0",
    "category": "",
    "summary": "Adds PA type contacts to the partner",
    "description": "",
    "author": "Flosslab",
    "website": "https://www.flosslab.com",
    "license": "LGPL-3",
    "sequence": 0,
    "depends": [
        "base",
        "fl_partner_cf",
        "fl_partner_pec"
    ],
    "data": [
        "security/access/res_partner_email_address.xml",
        "security/access/res_partner_digital_domicile.xml",

        "views/inherit_res_partner.xml",
        "views/res_partner_email_address.xml",
        "views/res_partner_digital_domicile.xml",

        "static/src/templates/web_templates.xml"
    ],
    "installable": True,
    "application": False,
    "auto_install": False
}
