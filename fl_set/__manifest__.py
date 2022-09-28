{
    "name": "Sets",
    "version": "14.0.2.0.0",
    "category": "Human Resources",
    "summary": "Group users",
    'description': """
        APP to group users.
    """,
    "author": "Flosslab",
    "website": "https://www.flosslab.com",
    "license": "LGPL-3",
    "sequence": 0,
    "depends": [
        "web",
        "bus",
        "fl_disable_childof_search_panel",
        "base_technical_features",
        "password_security",
        "disable_odoo_online"
    ],
    "data": [
        "security/categories.xml",
        "security/groups.xml",

        "security/access/set.xml",
        "security/access/voce_organigramma.xml",
        "security/rule/set.xml",
        "security/rule/voce_organigramma.xml",

        "actions/inherit_res_users.xml",
        "actions/set.xml",

        "views/set.xml",
        "views/inherit_res_users.xml",

        "wizards/inherit_res_config_settings.xml",

        "menu/action.xml",
        "menu/items.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
    "post_init_hook": "post_init_hook"
}
