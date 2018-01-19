# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp import netsvc
from openerp.osv import orm,  fields
import logging

_logger = logging.getLogger(__name__)


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

    def message_post(self, cr, uid, thread_id, body='', subject=None, type='notification',
                     subtype=None, parent_id=False, attachments=None, context=None,
                     content_subtype='html', **kwargs):
        if context is None:
            context = {}
        msg_id = super(res_users, self).message_post(
            cr, uid, thread_id, body=body, subject=subject, type=type,
            subtype=subtype, parent_id=parent_id, attachments=attachments,
            context=context, content_subtype=content_subtype, **kwargs)
        if (context.get('main_message_id') and (context.get('pec_type') or context.get('send_error'))):
            wf_service = netsvc.LocalService("workflow")
            _logger.info('workflow: mail message trigger')
            wf_service.trg_trigger(uid, 'mail.message',
                                   context['main_message_id'], cr)
        return msg_id

    def write(self, cr, uid, ids, values, context=None):
        protocollo_profile_selected = True
        protocollo_custom_selected = False
        values_copy = values.copy()
        protocollo_permissions_reset = {}
        group_obj = self.pool.get('res.groups')
        permissions_category = self.pool['ir.model.data'].get_object(cr, uid, 'seedoo_protocollo', 'module_category_protocollo')
        profile_category = self.pool['ir.model.data'].get_object(cr, uid, 'seedoo_protocollo', 'module_protocollo_management')
        seedoo_protocollo_groups = group_obj.search(cr, uid, [('category_id', 'in', permissions_category.ids)])
        for group_item in seedoo_protocollo_groups:
            protocollo_permissions_reset['in_group_' + str(group_item)] = False

        for key, val in values.iteritems():
            if key.startswith('sel_groups_'):
                group_ids = group_obj.browse(cr, uid, val)
                if group_ids.category_id.id != profile_category.id:
                    protocollo_profile_selected = False

                if group_ids.name == 'Personalizzabile':
                    protocollo_profile_selected = False
                    protocollo_custom_selected = True

                if protocollo_profile_selected:
                    for key_ingroup, val_ingroup in values.iteritems():
                        if key_ingroup.startswith('in_group_') and key_ingroup in protocollo_permissions_reset:
                            del values_copy[key_ingroup]
            else:
                protocollo_profile_selected = False

        if protocollo_profile_selected:
            values_copy.update(protocollo_permissions_reset)
            values = values_copy
        else:
            protocollo_custom_preselected = self.user_has_groups(cr, uid, 'seedoo_protocollo.group_protocollo_user')
            if protocollo_custom_selected is False and protocollo_custom_preselected is False:
                for key, val in values.iteritems():
                    if key in protocollo_permissions_reset:
                        del values_copy[key]
                values = values_copy

        res = super(res_users, self).write(cr, uid, ids, values, context=context)

        #self.pool.get('protocollo.protocollo').clear_cache()

        return res