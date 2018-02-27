# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.
import sys

from openerp.osv import fields, osv


class gedoc_document(osv.Model):
    _inherit = 'gedoc.document'

    _columns = {
        'importer_id': fields.many2one('dematerializzazione.storico.importazione.importer', 'Importer', readonly=True),
        'imported': fields.boolean('Importato', readonly=True),
        'protocollo_id': fields.many2one('protocollo.protocollo', 'Protocollo', readonly=True),
        'typology_id': fields.many2one('protocollo.typology', 'Tipologia', readonly=True),
    }

    _defaults = {
        'imported': False
    }