# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

{
    "name": "Seedoo Gestione Documentale",
    "version": "8.0.1.8.13",
    "category": "Document Management",
    "summary": "Modulo Gestione Documentale",
    "sequence": "1",
    "author": "Innoviu, Flosslab",
    "website": "https://www.seedoo.it",
    "license": "AGPL-3",
    "depends": [
        "base",
        "document",
        "hr",
        "l10n_it_ipa"
    ],
    "data": [
        "security/gedoc_security.xml",
        "security/gedoc_security_rules.xml",
        "security/ir.model.access.csv",
        "data/gedoc_data.xml",
        "data/model_type.xml",
        "data/document_type.xml",
        "wizard/gedoc_base_configuration_view.xml",
        "wizard/upload_doc_wizard_view.xml",
        "view/gedoc_view.xml",
        "view/company_view.xml",
        "workflow/gedoc_dossier_workflow.xml",

        "data/instance.xml"
    ],
    "css": [
        "static/src/css/gedoc.css"
    ],
    "installable": True,
    "application": True,
    "active": False
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
