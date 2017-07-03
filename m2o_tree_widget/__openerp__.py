# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Innoviu srl (<http://www.innoviu.it>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'M2O Tree Widget',
    'description': '''
This module add a tree view to many2one field, for a model
with a hierarchy

widget name=m2o_tree
options='{"all_checkable": "1",
          "parent_field": "pid"}'

default values:
- all_checkable: False
- parent_field: parent_id

This module is compatible with Odoo 8.0.
''',
    'version': '8.0.0',
    'category': 'Usability',
    'author': 'Innoviu Srl - Flosslab Srl',
    'website': 'http://www.innoviu.com - http://www.flosslab.com',
    'license': 'AGPL-3',
    'depends': ['web'],
    'data': ['base_data.xml'],
    'css': [
        'static/src/css/zTreeStyle.css',
    ],
    'demo': [],
    'qweb': ['static/src/xml/m2o_tree_widget.xml'],
    'installable': True,
    'auto_install': False,
}
