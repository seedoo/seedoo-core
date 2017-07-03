# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

{
    'name': "Sedoo Theme",
    'author': "Agile Business Group",
    'category': "Web",
    'sequence': 15,
    'website': "http://www.agilebg.com",
    'summary': 'Seedoo WEB Theme',
    'description': """
Seedoo Theme
============
This module add base theme for seedoo, like color , image and others
    """,
    'version': "1.0",
    'depends': [
        'base', 'web'
    ],
    'data': ['base_data.xml'],
    'js': [
        'static/src/js/chrome.js',
    ],
    'css': [
        'static/src/css/seedoo.css',
    ],
    'qweb': [
        'static/src/xml/seedoo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': True,
}
