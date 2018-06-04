# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp import netsvc, SUPERUSER_ID
from openerp.osv import orm, fields
from openerp.tools.safe_eval import safe_eval
import logging

_logger = logging.getLogger(__name__)
# TODO verifica con Peruzzu
class res_groups(orm.Model):
    _inherit = 'res.groups'

    _columns = {
        'is_protocollo_profile': fields.boolean('Profilo Seedoo Protocollo')
    }

    _defaults = {
        'is_protocollo_profile': False
    }



class res_users(orm.Model):
    _inherit = 'res.users'

    def _get_protocollo_group(self, cr, uid, ids, name, args, context=None):
        result = {}
        if not ids:
            return result
        result = dict.fromkeys(ids, False)
        # TODO verifica con Peruzzu se rimane utilizzare id e non nome
        cr.execute(
            "SELECT g.name from res_groups g WHERE g.id in (SELECT MAX(gr.id) from ir_module_category cat JOIN res_groups  gr ON cat.id = gr.category_id JOIN res_groups_users_rel rgu ON rgu.gid = gr.id where cat.name = 'Seedoo Protocollo' AND is_protocollo_profile=True AND rgu.uid IN %s)",(tuple(ids),))
        res = cr.fetchone()
        if res:
            result[ids[0]] = res[0]
        return result

    _columns = {
        'group': fields.function(_get_protocollo_group, type='char', size=256, string='Gruppo Protocollo', readonly=1),
        'profile_id': fields.many2one('protocollo.profile', 'Profilo Seedoo Protocollo')
    }

    
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

    def create(self, cr, uid, vals, context=None):
        new_context = dict(context or {})
        icp = self.pool.get('ir.config_parameter')
        if safe_eval(icp.get_param(cr, uid, 'auth_signup.disable_email_create_user', 'False')):
            new_context['no_reset_password'] = True
        user_id = super(res_users, self).create(cr, uid, vals, context=new_context)
        if vals and vals.has_key('profile_id') and vals['profile_id']:
            profile_obj = self.pool.get('protocollo.profile')
            profile = profile_obj.browse(cr, uid, vals['profile_id'])
            profile_obj.associate_profile_to_user(cr, uid, profile, [], user_id)
        return user_id

    def write(self, cr, uid, ids, vals, context=None):
        old_user_group_ids = {}

        if vals and vals.has_key('profile_id'):
            for user in self.browse(cr, uid, ids):
                if user and user.profile_id and user.profile_id.groups_id:
                    old_user_group_ids[user.id] = user.profile_id.groups_id.ids
                else:
                    old_user_group_ids[user.id] = []

        result = super(res_users, self).write(cr, uid, ids, vals, context=context)

        if vals and vals.has_key('profile_id'):
            profile = None
            profile_obj = self.pool.get('protocollo.profile')
            if vals['profile_id']:
                profile = profile_obj.browse(cr, uid, vals['profile_id'])
            for user in self.browse(cr, uid, ids):
                profile_obj.associate_profile_to_user(cr, uid, profile, old_user_group_ids[user.id], user.id)

        return result

    # TODO verifica con Peruzzu
    # def write(self, cr, uid, ids, values, context=None):
    #     protocollo_profile_selected = True
    #     protocollo_custom_selected = False
    #     values_copy = values.copy()
    #     protocollo_permissions_reset = {}
    #     group_obj = self.pool.get('res.groups')
    #     permissions_category = self.pool['ir.model.data'].get_object(cr, uid, 'seedoo_protocollo', 'module_category_protocollo')
    #     profile_category = self.pool['ir.model.data'].get_object(cr, uid, 'seedoo_protocollo', 'module_protocollo_management')
    #     seedoo_protocollo_groups = group_obj.search(cr, uid, [('category_id', 'in', permissions_category.ids)])
    #     for group_item in seedoo_protocollo_groups:
    #         protocollo_permissions_reset['in_group_' + str(group_item)] = False
    #
    #     for key, val in values.iteritems():
    #         if key.startswith('sel_groups_'):
    #             group_ids = group_obj.browse(cr, uid, val)
    #             if group_ids.category_id.id != profile_category.id:
    #                 protocollo_profile_selected = False
    #
    #             if group_ids.name == 'Personalizzabile':
    #                 protocollo_profile_selected = False
    #                 protocollo_custom_selected = True
    #
    #             if protocollo_profile_selected:
    #                 for key_ingroup, val_ingroup in values.iteritems():
    #                     if key_ingroup.startswith('in_group_') and key_ingroup in protocollo_permissions_reset:
    #                         del values_copy[key_ingroup]
    #
    #         else:
    #             protocollo_profile_selected = False
    #
    #     if protocollo_profile_selected:
    #         values_copy.update(protocollo_permissions_reset)
    #         values = values_copy
    #     elif protocollo_custom_selected:
    #         # for key, val in values.iteritems():
    #         #     if key in protocollo_permissions_reset:
    #         #         del values_copy[key]
    #         values = values_copy
    #     else:
    #         protocollo_profile_preselected = self._get_protocollo_group(cr, uid, ids, "", "", context=None)
    #         if len(protocollo_profile_preselected) > 0:
    #             protocollo_custom_preselected = True if "Personalizzabile" in protocollo_profile_preselected.values() else False
    #             if protocollo_custom_preselected is False:
    #                 values.update(protocollo_permissions_reset)
    #
    #     res = super(res_users, self).write(cr, uid, ids, values, context=context)
    #
    #     #self.pool.get('protocollo.protocollo').clear_cache()
    #
    #     return res