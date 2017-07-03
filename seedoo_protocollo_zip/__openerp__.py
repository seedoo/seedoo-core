# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

{
    'name': 'Seedoo Protocollo Zip',
    'version': '1.0',
    'author': 'Innoviu',
    'category': 'Document Management',
    'sequence': 23,
    'summary': 'Gestione Protocollo Informatico',
    'description': """
Downloads of all the attachment of a protocol in zip format

    """,
    'author': 'Innoviu Srl',
    'website': 'http://www.innoviu.com',
    'depends': [
        'seedoo_protocollo',
        ],
    'data': [
        'wizard/create_zip_wizard_view.xml',
        'view/protocollo_zip_view.xml'
        ],
    'demo': [],
    'update_xml': [],
    'installable': True,
    'application': True,
    'active': False,
}
