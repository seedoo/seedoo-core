# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.
import logging
from openerp import SUPERUSER_ID, api
from openerp.osv import orm, fields
from openerp.tools import GettextAlias

_logger = logging.getLogger(__name__)

_ = GettextAlias()


class ProtocolloProfile(orm.Model):
    _name = 'protocollo.profile'

    _columns = {

        'name': fields.char(size=256, string='Nome'),
        'groups_id': fields.many2many('res.groups', 'res_groups_profile_rel', 'uid', 'gid', 'Permessi'),
        'user_ids': fields.one2many('res.users', 'profile_id', 'Utenti'),
        'state': fields.selection(
            [
                ('enabled', 'Attivo'),
                ('disabled', 'Disattivo'),
            ], 'Stato'),
    }

    _defaults = {
        'state': 'enabled',
    }

    _order = 'name'

    def copy(self, cr, uid, id, default=None, context=None):
        profile_name = self.read(cr, uid, [id], ['name'])[0]['name']
        default.update({'name': _('%s (copy)')%profile_name})
        return super(ProtocolloProfile, self).copy(cr, uid, id, default, context)

    def write(self, cr, uid, ids, vals, context=None):
        super(ProtocolloProfile, self).write(cr, uid, ids, vals, context=context)

        if 'groups_id' in vals:
            user_obj = self.pool.get('res.users')
            protocollo_profile = self.browse(cr, uid, ids)
            user_ids = protocollo_profile.user_ids.ids
            for user_id in user_ids:
                user_obj.write(cr, SUPERUSER_ID, [user_id], {
                    'groups_id': [(6, 0, protocollo_profile.groups_id.ids)]
                })
        return True
