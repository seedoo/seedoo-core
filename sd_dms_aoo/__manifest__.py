{
    "name": "AOO - Documents",
    "version": "14.0.2.0.0",
    "category": "Document Management",
    "summary": "Adds AOO on storage",
    "description": "",
    "author": "Flosslab",
    "website": "https://www.flosslab.com",
    "license": "LGPL-3",
    "sequence": 0,
    "depends": [
        "sd_dms",
        "fl_set_pa"
    ],
    "data": [
        "views/inherit_sd_dms_storage.xml",

        "wizards/inherit_res_config_settings.xml"
    ],
    "installable": True,
    "application": False,
    "auto_install": False
}
