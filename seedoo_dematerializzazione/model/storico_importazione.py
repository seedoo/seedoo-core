# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import orm, fields

class dematerializzazione_storico_importazione(orm.Model):
    _name = 'dematerializzazione.storico.importazione'

    MODALITA_SELECTION = [('cron', 'Cron'), ('manuale', 'Manuale')]
    ESITO_SELECTION = [('ok', 'OK'), ('errore', 'Errore')]

    def _model_name_get_fnc(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for record in self.browse(cr, uid, ids, context=context):
            name = 'Importazione del ' + record.inizio
            res[record.id] = name
        return res

    def _model_numero_file_importati_get_fnc(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for record in self.browse(cr, uid, ids, context=context):
            count = 0
            for storico_importazione_importer in record.storico_importazione_importer_ids:
                for storico_file in storico_importazione_importer.storico_importazione_importer_file_ids:
                    if storico_file.esito == 'ok':
                        count = count + 1
            res[record.id] = count
        return res

    def _model_numero_file_errore_get_fnc(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for record in self.browse(cr, uid, ids, context=context):
            count = 0
            for storico_importazione_importer in record.storico_importazione_importer_ids:
                for storico_file in storico_importazione_importer.storico_importazione_importer_file_ids:
                    if storico_file.esito == 'errore':
                        count = count + 1
            res[record.id] = count
        return res

    _columns = {
        'name': fields.function(_model_name_get_fnc, type='char', string='Nome', store=True),
        'inizio': fields.datetime('Inizio'),
        'fine': fields.datetime('Fine'),
        'modalita': fields.selection(MODALITA_SELECTION, 'Modalità', select=True),
        'esito': fields.selection(ESITO_SELECTION, 'Esito', select=True),
        'numero_file_importati': fields.function(_model_numero_file_importati_get_fnc, type='integer', string='File Importati'),
        'numero_file_errore': fields.function(_model_numero_file_errore_get_fnc, type='integer', string='File in Errore'),
        'storico_importazione_importer_ids': fields.one2many(
            'dematerializzazione.storico.importazione.importer',
            'storico_importazione_id',
            'Storico Importazione Sorgenti'),
    }

    _order = 'inizio desc'