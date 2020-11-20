# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.


{
    "name": "Seedoo Theme",
    "version": "8.0.1.8.12",
    "category": "Web",
    "summary": "Tema Grafico Piattaforma Seedoo",
    "sequence": "1",
    "author": "Agile Business Group, Flosslab",
    "website": "http://www.seedoo.it",
    "license": "AGPL-3",
    "depends": [
        "base",
        "web"
    ],
    "data": [
        "data/base_data.xml",
        "data/template_data.xml"
    ],
    "js": [
        "static/src/js/chrome.js"
    ],
    "css": [
        "static/src/css/seedoo.css"
    ],
    "qweb": [
        "static/src/xml/seedoo.xml"
    ],
    "installable": True,
    "application": True,
    "auto_install": True
}
