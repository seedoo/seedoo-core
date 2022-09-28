{
    "name": "E-mail client - PEC Support",
    "version": "14.0.2.0.0",
    "category": "Discuss",
    "summary": "PEC extension for e-mail client",
    "description": "",
    "author": "Flosslab",
    "website": "https://www.flosslab.com",
    "license": "LGPL-3",
    "sequence": 0,
    "depends": [
        "fl_mail_client",
        "fl_partner_pec",
    ],
    "data": [
        "actions/inherit_mail_mail.xml",

        "views/inherit_fl_mail_client_contact.xml",
        "views/inherit_fl_mail_client_account.xml",
        "views/inherit_mail_mail.xml",
        "views/inherit_fetchmail_server.xml",

        "menu/actions.xml",
        "menu/items.xml",

        "static/src/templates/web_templates.xml",

        "wizards/inherit_mail_compose_message_view.xml",
    ],
    "qweb": [
        'static/src/components/discuss_sidebar/discuss_sidebar.xml'
    ],
    "installable": True,
    "application": False,
    "auto_install": False
}
