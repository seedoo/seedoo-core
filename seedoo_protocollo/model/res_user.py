# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp import netsvc, SUPERUSER_ID
from openerp.osv import orm, fields
from openerp.tools.safe_eval import safe_eval
import logging

_logger = logging.getLogger(__name__)


class res_groups(orm.Model):
    _inherit = 'res.groups'

    def get_creazione_cantatti_group_id(self, cr, uid, context={}):
        model_data_obj = self.pool.get('ir.model.data')
        creazione_cantatti_group_id = model_data_obj.get_object_reference(cr, uid, 'base', 'group_partner_manager')[1]
        return creazione_cantatti_group_id

    def get_protocollo_profile_category_ids(self, cr, uid, context={}):
        model_data_obj = self.pool.get('ir.model.data')
        category_documentale_id = model_data_obj.get_object_reference(cr, uid, 'seedoo_gedoc', 'module_gedoc_category')[1]
        category_protocollo_id = model_data_obj.get_object_reference(cr, uid, 'seedoo_protocollo', 'module_category_protocollo')[1]
        category_sharedmail_id = model_data_obj.get_object_reference(cr, uid, 'sharedmail', 'sharedmail')[1]
        category_pec_id = model_data_obj.get_object_reference(cr, uid, 'l10n_it_pec_messages', 'module_l10n_it_pec_messages')[1]
        category_ids = [category_documentale_id, category_protocollo_id, category_sharedmail_id, category_pec_id]
        return category_ids

    def _is_protocollo_profile(self, cr, uid, ids, name, arg, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        category_ids = self.get_protocollo_profile_category_ids(cr, uid, context)
        creazione_cantatti_group_id = self.get_creazione_cantatti_group_id(cr, uid, context)
        reads = self.read(cr, uid, ids, ['category_id'])
        res = []
        for record in reads:
            category_id = record['category_id'][0]
            is_protocollo_profile = False
            if record['id']==creazione_cantatti_group_id or (category_id and category_id in category_ids):
                is_protocollo_profile = True
            res.append((record['id'], is_protocollo_profile))
        return res

    def _is_protocollo_profile_search(self, cr, uid, obj, name, args, domain=None, context=None):
        ids = self.search(cr, uid, [('category_id', 'in', self.get_protocollo_profile_category_ids(cr, uid, context))])
        ids.append(self.get_creazione_cantatti_group_id(cr, uid, context))
        return [('id', 'in', ids)]

    _columns = {
        'is_protocollo_profile': fields.function(_is_protocollo_profile, fnct_search=_is_protocollo_profile_search, type='boolean', string='Profilo Seedoo Protocollo')
    }



class res_users(orm.Model):
    _inherit = 'res.users'

    _columns = {
        'profile_id': fields.many2one('protocollo.profile', 'Seedoo')
    }

    def _get_default_action_id(self, cr, uid, context=None):
        action = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'seedoo_protocollo', 'protocollo_dashboard_act')
        if action:
            return action[1]
        return False

    _defaults = {
        'action_id': _get_default_action_id
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
            _logger.debug('workflow: mail message trigger')
            wf_service.trg_trigger(uid, 'mail.message',
                                   context['main_message_id'], cr)
        return msg_id

    def create(self, cr, uid, vals, context=None):
        new_context = dict(context or {})
        icp = self.pool.get('ir.config_parameter')
        if safe_eval(icp.get_param(cr, SUPERUSER_ID, 'auth_signup.disable_email_create_user', 'False')):
            new_context['no_reset_password'] = True
        user_id = super(res_users, self).create(cr, uid, vals, context=new_context)
        if vals and vals.has_key('profile_id') and vals['profile_id']:
            profile_obj = self.pool.get('protocollo.profile')
            profile = profile_obj.browse(cr, uid, vals['profile_id'])
            groups_obj = self.pool.get('res.groups')
            old_user_group_ids = groups_obj.search(cr, uid, [
                ('users', '=', user_id),
                ('is_protocollo_profile', '=', True)
            ], context=context)
            profile_obj.associate_profile_to_user(cr, uid, profile, old_user_group_ids, user_id)
        return user_id

    def write(self, cr, uid, ids, vals, context=None):
        old_user_group_ids = {}

        if vals and vals.has_key('profile_id'):
            groups_obj = self.pool.get('res.groups')
            for id in ids:
                old_user_group_ids[id] = groups_obj.search(cr, uid, [
                    ('users.id', '=', id),
                    ('is_protocollo_profile', '=', True)
                ], context=context)

        result = super(res_users, self).write(cr, uid, ids, vals, context=context)

        if vals and vals.has_key('profile_id'):
            profile = None
            profile_obj = self.pool.get('protocollo.profile')
            if vals['profile_id']:
                profile = profile_obj.browse(cr, uid, vals['profile_id'])
            for id in ids:
                profile_obj.associate_profile_to_user(cr, uid, profile, old_user_group_ids[id], id)

        return result