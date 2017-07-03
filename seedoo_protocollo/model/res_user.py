# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import orm,  fields


class res_users(orm.Model):
    _inherit = 'res.users'

    # def get_user_offices(self, cr, uid, context=None):
    #     cr.execute("select department_id \
    #                 from \
    #                 hr_department_collaborator \
    #                 where name = %d" % uid)
    #     return [ids[0] for ids in cr.fetchall()]
    
    def get_users_from_group(self, cr, uid, group, context=None):
        group_obj = self.pool.get('res.groups')
        manager_group_ids = group_obj.search(cr, uid, [('name', '=', group)])
        if len(manager_group_ids) == 1:
            manager_group = group_obj.browse(cr, uid, manager_group_ids[0])
            return manager_group.users
        #todo add exception