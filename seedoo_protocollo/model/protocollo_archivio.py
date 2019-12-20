# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import orm, fields
from openerp.tools.translate import _

# Procudura per la creazione degli archivi e inserimento dei relativi protocolli al suo interno. Lo scopo di tale
# procedura è quello di ridurre i tempi di esecuzione dell'algoritmo di visibilità, in quanto i protocolli all'interno
# di archivi diversi dall'archivio corrente non saranno più visibili agli utenti (a meno che non si abbia il relativo
# permesso). L'ottimizzazione è ottenuta tramite l'uso di un indice sql sulla colonna archivio_id del protocollo.
# L'idea dell'uso dell'archivio è quella di riportare i tempi dell'algoritmo di visibilità pari a quelli che si
# ottengono quando il database è vuoto o con pochi protocolli. In parte tale obiettivo è stato raggiunto, perchè le
# query eseguite SOLAMENTE nella tabella protocollo_protocollo hanno dei tempi quasi uguali a quelli del database vuoto.
# Nelle query che richiedono una JOIN della tabella protocollo_protocollo con la tabella protocollo_assegnazione, i
# tempi migliorano ma sono sempre più alti di quando il database è vuoto. Bisognerà sperimentare in futuro, quando ci
# saranno più archivi e più protocolli, se tali tempi continuano a peggiorare o rimangono comunque stabili. Per ovviare
# al problema sono state fatte anche delle prove con l'inserimento di un indice su un campo archivio_id nella tabella
# protocollo_assegnazione (quindi una sorta di archiviazione anche per i record di tale tabella), ma non sono stati
# ottenuti dei buoni risultati, anzi in alcuni casi peggiorava anche i tempi dell'algoritmo, dovendo controllare una
# ulteriore condizione.
# E' importante considerare il fatto che le prestazioni dell'algoritmo, una volta archiviati i protocolli correnti, non
# miglioreranno subito, ma ci vorrà qualche minuto (in media dovrebbero essere 5) dovuto probabilmente alla cache
# interna.
class protocollo_archivio(orm.Model):
    _name = 'protocollo.archivio'


    def _get_protocolli_archiviati_count(self, cr, uid, ids, field, arg, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        res = dict.fromkeys(ids, False)

        for id in ids:
            sql_query = """SELECT COUNT(pp.id)
                               FROM protocollo_protocollo pp
                               WHERE pp.registration_date IS NOT NULL
                                    AND pp.archivio_id = %d""" % (id)

            cr.execute(sql_query)
            result = cr.fetchall()
            count_value = result[0][0]
            res[id] = count_value
        return res

    def _configura_protocollo_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        res = dict.fromkeys(ids, False)
        for id in ids:
            check = self.user_has_groups(cr, uid, 'seedoo_protocollo.group_configurazione_archivio')
            res[id] = check

        return res

    _columns = {
        'name': fields.char('Nome', size=256, required=True),
        'aoo_id': fields.many2one('protocollo.aoo', 'AOO', required=True),
        'is_current': fields.boolean('Corrente'),
        'total': fields.function(_get_protocolli_archiviati_count, 'Numero totale protocolli', type='integer', string= 'PEC - Numero invii'),
        'configura_protocollo_visibility': fields.function(_configura_protocollo_visibility, type='boolean', string='Archivia protocolli'),
    }

    def _get_archivio_ids(self, cr, uid, is_current=True, context=None):
        archivio_ids = self.pool.get('protocollo.archivio').search(cr, uid, [('is_current', '=', is_current)], context=context)
        return archivio_ids

    def write(self, cr, uid, ids, vals, context=None):
        if 'is_current' in vals and vals['is_current']:
            archivio_current_count = self._verifica_archivio_corrente(cr, uid, vals, context)
            if archivio_current_count > 0:
                raise orm.except_orm(_('Errore'),
                     _('Archivio corrente gia\' esistente'))
        archivio_id = super(protocollo_archivio, self).write(cr, uid, ids, vals, context=context)
        return archivio_id

    def _verifica_archivio_corrente(self, cr, uid, vals, context):
        aoo_ids = self.pool.get('protocollo.aoo').search(cr, uid, [], context=context)
        archivio_obj = self.pool.get('protocollo.archivio')
        archivio_current_check = archivio_obj.search(cr, uid, [('aoo_id', '=', aoo_ids[0]), ('is_current', '=', True)], context=context)
        return len(archivio_current_check)

    def go_to_archive_action(self, cr, uid, ids, context=None):
        model_data_obj = self.pool.get('ir.model.data')
        view_form_rec = model_data_obj.get_object_reference(cr, uid, 'seedoo_protocollo', 'protocollo_protocollo_form')
        view_tree_rec = model_data_obj.get_object_reference(cr, uid, 'seedoo_protocollo', 'protocollo_protocollo_tree')
        form_id = view_form_rec and view_form_rec[1] or False
        tree_id = view_tree_rec and view_tree_rec[1] or False
        archivio_id = False
        if context and 'archivio_id' in context:
            archivio_id = context['archivio_id']
        elif len(ids) == 1:
            archivio_id = ids[0]
        return {
            'name': 'Archivio',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(tree_id, 'tree'), (form_id, 'form')],
            'view_id': False,
            'res_model': 'protocollo.protocollo',
            'target': 'current',
            'type': 'ir.actions.act_window',
            'context': "{'is_current_archive': False}",
            'domain': [('archivio_id', '=', archivio_id)]
            # 'flags': {'form': {'options': {'mode': 'view'}}}
        }


class protocollo_protocollo(orm.Model):

    _inherit = 'protocollo.protocollo'

    _columns = {
        'archivio_id': fields.many2one('protocollo.archivio', 'Archivio', required=True),
        'is_current_archive': fields.related('archivio_id', 'is_current', type='boolean', string='Archivio Corrente',
                                         readonly=True)
    }

    def _get_default_archivio_id(self, cr, uid, context=None):
        aoo_ids = self.pool.get('protocollo.aoo').search(cr, uid, [], context=context)
        if len(aoo_ids) > 0:
            archivio_ids = self.pool.get('protocollo.archivio').search(cr, uid, [('aoo_id', '=', aoo_ids[0]),
                                                                                 ('is_current', '=', True)],
                                                                       context=context)
            return archivio_ids[0]
        return False

    _defaults = {
        'archivio_id': _get_default_archivio_id,
    }
