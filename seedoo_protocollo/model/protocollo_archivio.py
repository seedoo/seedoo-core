# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import orm, fields, osv

class protocollo_archivio(orm.Model):
    _name = 'protocollo.archivio'

    STATE_SELECTION = [
        ('corrente', 'Corrente'),
        ('deposito', 'Deposito'),
    ]

    _columns = {
        'name': fields.char('Nome', size=256, required=True),
        'aoo_id': fields.many2one('protocollo.aoo', 'AOO', required=True),
        'is_current': fields.boolean('Corrente', required=True)
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
