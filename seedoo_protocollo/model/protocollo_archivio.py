# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import orm, fields
from openerp.tools.translate import _

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
                               WHERE pp.state != 'draft'
                                    AND pp.archivio_id = %d""" % (id)

            cr.execute(sql_query)
            result = cr.fetchall()
            count_value = result[0][0]
            res[id] = count_value
        return res

    def _archivia_protocollo_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        res = dict.fromkeys(ids, False)
        for id in ids:
            check = self.user_has_groups(cr, uid, 'seedoo_protocollo.group_archivia_protocollo')
            res[id] = check

        return res

    def _elimina_protocollo_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
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
        'archivia_protocollo_visibility': fields.function(_archivia_protocollo_visibility, type='boolean', string='Archivia protocolli'),
        'elimina_protocollo_visibility': fields.function(_elimina_protocollo_visibility, type='boolean', string='Configura ed elimina protocolli'),
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
        return {
            'name': 'PEC',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(tree_id, 'tree'), (form_id, 'form')],
            'view_id': False,
            'res_model': 'protocollo.protocollo',
            'target': 'current',
            'type': 'ir.actions.act_window',
            'context': "{'is_current_archive': False}",
            'domain': [('archivio_id', '=', context.get('archivio_id', False))]
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
