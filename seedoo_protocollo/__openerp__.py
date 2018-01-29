# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

{
    "name": "Seedoo Protocollo",
    "version": "8.0.1.6.0",
    "category": "Document Management",
    "summary": "Protocollo Informatico PA",
    "sequence": "1",
    "author": "Agile Business Group, Innoviu, Flosslab",
    "website": "http://www.seedoo.it",
    "license": "AGPL-3",
    "depends": [
        "base",
        "web",
        "l10n_it_pec",
        "sharedmail",
        "document",
        "hr",
        "email_template",
        "report_webkit",
        "seedoo_gedoc",
        "l10n_it_pec_messages",
        "l10n_it_ipa",
        "m2o_tree_widget",
        "web_pdf_widget",
        "web_dashboard_tile"
    ],
    "data": [
        "data/protocollo_company.xml",
        "data/protocollo_configuration.xml",
        "data/protocollo_conferma_template.xml",
        "data/protocollo_annullamento_template.xml",
        "security/protocollo_security.xml",
        "security/protocollo_visibility_security.xml",
        "security/security_rules.xml",
        "security/ir.model.access.csv",
        "data/protocollo_sequence.xml",
        "data/protocollo_aoo.xml",
        "data/protocollo_typology.xml",
        "data/protocollo_admin.xml",
        "gedoc/data/gedoc_data.xml",
        "wizard/cancel_protocollo_wizard_view.xml",
        "wizard/modify_protocollo_wizard_view.xml",
        "wizard/classifica_protocollo_wizard_view.xml",
        "wizard/fascicola_protocollo_wizard_view.xml",
        "wizard/assegna_protocollo_wizard_view.xml",
        "wizard/create_protocollo_mailpec_wizard_view.xml",
        "wizard/modify_protocollo_email_wizard_view.xml",
        "wizard/modify_protocollo_pec_wizard_view.xml",
        "wizard/carica_documenti_wizard_view.xml",
        "view/res_config.xml",
        "view/partner_view.xml",
        "view/offices_view.xml",
        "view/ir_attachment_view.xml",
        "view/protocollo_view.xml",
        "view/protocollo_sender_receiver_view.xml",
        "view/protocollo_aoo_view.xml",
        "view/mail_pec_view.xml",
        "view/sharedmail_view.xml",
        "view/contact_view.xml",
        "view/report_view.xml",
        "view/menu_item.xml",
        "gedoc/view/gedoc_view.xml",
        "wizard/create_journal_wizard_view.xml",
        "wizard/create_emergency_registry_wizard_view.xml",
        "workflow/protocollo_workflow.xml",
        "data/protocollo_report.xml",
        "menu/menu.xml",
        "data/protocollo_tile.xml",
        "view/protocollo_dashboard_view.xml",
        "view/tile.xml"
    ],
    "demo": [
        "demo/hr_delete.xml",
        "demo/protocollo_company.xml",
        "demo/protocollo_aoo.xml",
        "demo/protocollo_department.xml",
        "demo/protocollo_classification.xml",
        "demo/protocollo_dossier.xml",
        "demo/protocollo_user_employee.xml"
    ],
    "qweb": [
        "static/src/xml/base.xml",
        "static/src/xml/mail.xml"
    ],
    "css": [
        "static/src/css/protocollo.css",
        "static/src/css/protocollo_accordion.css"
    ],
    "js": [
        "static/src/js/protocollo_accordion.js"
    ],
    "installable": True,
    "application": True,
    "active": False
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
