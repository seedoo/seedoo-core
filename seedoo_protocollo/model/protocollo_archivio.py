# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import orm, fields
from openerp.tools.translate import _

class protocollo_archivio(orm.Model):
    _name = 'protocollo.archivio'

    _columns = {
        'name': fields.char('Nome', size=256, required=True),
        'aoo_id': fields.many2one('protocollo.aoo', 'AOO', required=True),
        'is_current': fields.boolean('Corrente')
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
