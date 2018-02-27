# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import orm, fields

class dematerializzazione_storico_importazione_importer_file(orm.Model):
    _name = 'dematerializzazione.storico.importazione.importer.file'

    ESITO_SELECTION = [('ok', 'OK'), ('errore', 'Errore')]

    _columns = {
        'name': fields.char('Nome File', char=256, required=True),
        'esito': fields.selection(ESITO_SELECTION, 'Esito', select=True),
        'errore': fields.text('Errore'),
        'storico_importazione_importer_id': fields.many2one('dematerializzazione.storico.importazione.importer', 'Storico Importazione Sorgenti', ondelete='cascade'),
        'protocollo_id': fields.many2one('protocollo.protocollo', 'Protocollo associato', ondelete='set null'),
        'document_id': fields.many2one('gedoc.document', 'Documento associato', ondelete='set null'),
    }