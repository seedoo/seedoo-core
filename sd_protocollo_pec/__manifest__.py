{
    "name": "PEC - Protocollo",
    "version": "14.0.2.0.0",
    "category": "Document Management",
    "summary": "Aggiunge la gestione della PEC al Protocollo",
    "description": "",
    "author": "Flosslab",
    "website": "https://www.flosslab.com",
    "license": "LGPL-3",
    "sequence": 0,
    "depends": [
        "sd_protocollo",
    ],
    "data": [
        "data/inherit_ir_config_parameter.xml",
        "data/inherit_mezzo_trasmissione.xml",

        "actions/mail_mail.xml",

        "security/groups.xml",
        "security/access/wizard.xml",

        "views/inherit_mail_mail.xml",
        "views/inherit_sd_dms_contact.xml",
        "views/inherit_sd_dms_contact_digital_domicile.xml",
        "views/inherit_sd_dms_contact_email_address.xml",
        "views/inherit_sd_protocollo_invio.xml",
        "views/inherit_sd_protocollo_invio_destinatario.xml",
        "views/inherit_sd_protocollo_mezzo_trasmissione.xml",
        "views/inherit_sd_protocollo_protocollo.xml",

        "templates/assets.xml",
        "templates/protocollo_dashboard_template.xml",
        "templates/mail_mail.xml",
        "templates/inherit_header_footer_template.xml",

        "reports/mail_mail.xml",

        "wizards/protocollo_crea_da_mail_view.xml",
        "wizards/protocollo_invio_mail_view.xml",
        "wizards/protocollo_reinvio_mail_view.xml",
        "wizards/inherit_res_config_settings.xml",
        "wizards/inherit_sd_dms_wizard_document_add_contact.xml",
        "wizards/inherit_sd_protocollo_wizard_protocollo_registra.xml",
    ],
    "qweb": [
        "static/src/components/mail/mail.xml"
    ],
    "installable": True,
    "application": False,
    "auto_install": False
}
