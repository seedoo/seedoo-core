# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import orm, fields


class ProtocolloProfile(orm.Model):
    _name = 'protocollo.profile'

    _columns = {

        'name': fields.char(size=256, string='Nome'),
        'category_id': fields.many2one('ir.module.category', 'Categoria'),
        'groups_id': fields.many2many('res.groups', 'res_groups_profile_rel', 'uid', 'gid', 'Gruppi'),
        'employees': fields.many2many('hr.employee', 'res_employees_profile_rel', 'gid', 'uid', 'Dipendenti'),
        'state': fields.selection(
            [
                ('enabled', 'Attivo'),
                ('disabled', 'Disattivo'),
            ], 'Stato'),
    }

    _defaults = {
        'state': 'enabled'
    }

    def write(self, cr, uid, ids, vals, context=None):
        super(ProtocolloProfile, self).write(cr, uid, ids, vals, context=context)
        protocollo_profile = self.browse(cr, uid, ids)

        employees_list = [protocollo_profile.employees]

        for employee in employees_list:
            if employee.user_id:
                self.pool.get('res.users').write(cr, uid, [employee.user_id.id], {
                    'groups_id': [(6, 0, protocollo_profile.groups_id.ids)]
                })
        return True
