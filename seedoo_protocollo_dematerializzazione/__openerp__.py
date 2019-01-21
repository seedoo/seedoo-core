# -*- coding: utf-8 -*-

# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

{
    "name": "Seedoo Protocollo Dematerializzazione",
    "version": "8.0.1.8.0",
    "category": "Document Management",
    "summary": "Gestione Documenti Analogici Protocollo",
    "sequence": "1",
    "author": "Flosslab",
    "website": "http://www.flosslab.com.",
    "license": "AGPL-3",
    "depends": [
        "base",
        "seedoo_protocollo"
    ],
    "data": [
        "data/configurazione.xml",
        "data/cron.xml",
        "security/security.xml",
        "security/security_rules.xml",
        "security/ir.model.access.csv",
        "data/profile.xml",
        "view/importer.xml",
        "view/storico_importazione.xml",
        "view/storico_importazione_importer.xml",
        "view/storico_importazione_importer_file.xml",
        "view/res_config.xml",
        "view/protocollo.xml",
        "wizard/importa_documenti_wizard_view.xml",
        "wizard/crea_protocollo_da_documento_wizard_view.xml",
        "view/gedoc_document.xml",
        "menu/menu.xml",
        "data/protocollo_tile.xml",
    ],
    "demo": [

    ],
    "css": [
        "static/src/css/dematerializzazione.css"
    ],
    "installable": True,
    "application": True,
    "active": False
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
