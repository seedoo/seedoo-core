# Copyright 2020-2022 Flosslab S.r.l.
# Copyright 2017-2019 MuK IT GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Documents",
    "version": "14.0.2.0.0",
    "category": "Document Management",
    "summary": "Create, organize documents",
    "description": """
        APP to document management system.
    """,
    "author": "Flosslab",
    "website": "https://www.flosslab.com",
    "license": "LGPL-3",
    "sequence": 0,
    "depends": [
        "fl_mimetypes",
        "fl_fields_file",
        "fl_acl",
        "fl_set",
        "fl_partner_pa",
        "fl_web_preview",
        "fl_widget_ztree",
        "fl_load_only_children_search_panel",
        "fl_tooltip_search_panel",
        # "fl_focus_first_tab",
        "fl_utility",
        "web_notify",
        "mail",
        "base_location_geonames_import",
        "fl_feature_enterprise"
    ],
    "external_dependencies": {
        "bin": [
            "soffice"
        ]
    },
    "data": [
        "data/storage.xml",
        "data/folder.xml",
        "data/document_type.xml",

        "security/categories.xml",
        "security/groups.xml",

        "security/access/category.xml",
        "security/access/document.xml",
        "security/access/document_type.xml",
        "security/access/folder.xml",
        "security/access/storage.xml",
        "security/access/tag.xml",
        "security/access/acl.xml",
        "security/access/folder_acl.xml",
        "security/access/document_acl.xml",
        "security/access/contact.xml",
        "security/access/contact_digital_domicile.xml",
        "security/access/contact_email_address.xml",
        "security/access/wizard.xml",
        "security/rule/category.xml",
        "security/rule/document.xml",
        "security/rule/folder.xml",
        "security/rule/storage.xml",

        "template/assets/folder_kanban.xml",
        "actions/folder.xml",
        "actions/document.xml",

        "views/storage.xml",
        "views/document.xml",
        "views/document_type.xml",
        "views/folder.xml",
        "views/folder_acl.xml",
        "views/document_acl.xml",
        "views/category.xml",
        "views/contact.xml",
        "views/contact_digital_domicile.xml",
        "views/contact_email_address.xml",
        "views/res_partner.xml",
        "views/inherit_res_users.xml",

        "menu/action.xml",
        "menu/items.xml",

        "wizard/inherit_res_config_settings.xml",
        "wizard/document_add_contact.xml",

        "static/src/templates/web_templates.xml"
    ],
    "installable": True,
    "post_init_hook": "post_init_hook",
    "application": True,
    "auto_install": False
}
