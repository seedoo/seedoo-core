# -*- coding: utf-8 -*-

# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

{
    "name": "Seedoo Dematerializzazione",
    "version": "1.0",
    "author": "Flosslab Srl",
    "website": "http://www.flosslab.com",
    "category": "Document Management",
    "summary": "Gestione documenti cartacei",
    "description": """Gestione documenti cartacei
==================================================

Aggiunge funzionalità di stampa etichetta adesiva per i protocolli, importazione documenti tramite scanner, etc.""",
    "depends": [
        "base",
        "seedoo_protocollo"
    ],
    "data": [
        'data/configurazione.xml',
        'data/cron.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'security/security_rules.xml',
        'view/importer.xml',
        'view/storico_importazione.xml',
        'view/storico_importazione_importer.xml',
        'view/storico_importazione_importer_file.xml',
        'view/res_config.xml',
        'view/protocollo.xml',
        'wizard/importa_documenti_wizard_view.xml',
        'menu/menu.xml'
    ],
    'css': ['static/src/css/dematerializzazione.css'],
    "demo": [
        'demo/dematerializzazione_importer.xml',
    ]
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
