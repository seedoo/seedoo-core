{
    "name": "E-mail client",
    "version": "14.0.2.0.0",
    "category": "Discuss",
    "summary": "Receive and send e-mail",
    'description': """
            APP to use e-mail message.
        """,
    "author": "Flosslab",
    "website": "https://www.flosslab.com",
    "license": "LGPL-3",
    "sequence": 0,
    "depends": [
        "fl_mimetypes",
        "fl_partner_email",
        "base_technical_features",
        "password_security",
        "disable_odoo_online",
        "fl_feature_enterprise",
    ],
    "data": [
        "security/categories.xml",
        "security/groups.xml",

        "security/access/account.xml",
        "security/access/account_permission.xml",
        "security/access/contact.xml",
        "security/access/inherit_fetchmail_server.xml",
        "security/access/fetchmail_server_history.xml",
        "security/access/inherit_ir_mail_server.xml",
        "security/access/inherit_mail_mail.xml",
        "security/access/inherit_ir_module_module.xml",
        "security/access/inherit_ir_cron.xml",

        "security/rules/inherit_mail_mail.xml",

        "wizards/inherit_mail_compose_message.xml",
        "wizards/inherit_res_config_settings.xml",

        "templates/assets.xml",

        "views/contact.xml",
        "views/inherit_fetchmail_server.xml",
        "views/inherit_ir_mail_server.xml",
        "views/inherit_ir_attachment.xml",

        "views/inherit_mail_mail.xml",
        "actions/inherit_mail_mail.xml",

        "views/account.xml",
        "views/account_permission.xml",

        "menu/actions.xml",
        "menu/items.xml",

        "static/src/templates/web_templates.xml"
    ],
    "qweb": [
        'static/src/components/discuss_sidebar/discuss_sidebar.xml',
        'static/src/components/mail_list/mail_list.xml',
        'static/src/components/mail/mail.xml',
        'static/src/components/thread_view/thread_view.xml',
        'static/src/components/thread_icon/thread_icon.xml',
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
    "post_init_hook": "post_init_hook"
}
