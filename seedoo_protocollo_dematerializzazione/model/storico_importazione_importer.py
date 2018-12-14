# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import orm, fields
from importer import TIPOLOGIA_SELECTION

class dematerializzazione_storico_importazione_importer(orm.Model):
    _name = 'dematerializzazione.storico.importazione.importer'

    ESITO_SELECTION = [('ok', 'OK'), ('errore', 'Errore')]

    _columns = {
        'name': fields.char('Nome Importer', char=80, required=True),
        'tipologia_importazione': fields.selection(TIPOLOGIA_SELECTION, 'Tipologia Importazione', select=True, required=True),
        'indirizzo': fields.char('IP/Hostname', char=256, required=True),
        'cartella': fields.char('Condivisione', char=256, required=True),
        'percorso': fields.char('Percorso', char=256, required=True),
        'esito': fields.selection(ESITO_SELECTION, 'Esito', select=True),
        'errore': fields.text('Errore'),
        'storico_importazione_id': fields.many2one('dematerializzazione.storico.importazione', 'Storico Importazione', ondelete='cascade'),
        'storico_importazione_importer_file_ids': fields.one2many(
            'dematerializzazione.storico.importazione.importer.file',
            'storico_importazione_importer_id',
            'Storico Importazione File'),
    }