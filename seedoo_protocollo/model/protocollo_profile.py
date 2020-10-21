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
    _inherit = 'mail.thread'
    _mail_flat_thread = False

    _columns = {
        'name': fields.char(size=256, string='Nome'),
        'groups_id': fields.many2many('res.groups', 'res_groups_profile_rel', 'uid', 'gid', 'Permessi'),
        'user_ids': fields.one2many('res.users', 'profile_id', 'Utenti'),
        'state': fields.selection([('enabled', 'Attivo'),('disabled', 'Disattivo')], 'Stato')
    }

    _defaults = {
        'state': 'enabled',
    }

    _order = 'name'

    def copy(self, cr, uid, id, default=None, context=None):
        profile_name = self.read(cr, uid, [id], ['name'])[0]['name']
        default.update({'name': _('%s (copy)') % profile_name})
        return super(ProtocolloProfile, self).copy(cr, uid, id, default, context)

    def write(self, cr, uid, ids, vals, context=None):
        old_profile_group_ids = {}

        if vals and vals.has_key('groups_id') and vals['groups_id']:
            for profile in self.browse(cr, uid, ids):
                old_profile_group_ids[profile.id] = profile.groups_id.ids

        super(ProtocolloProfile, self).write(cr, uid, ids, vals, context=context)

        if vals and vals.has_key('groups_id') and vals['groups_id']:
            for profile in self.browse(cr, uid, ids):
                groups_obj = self.pool.get('res.groups')
                user_ids = profile.user_ids.ids
                for user_id in user_ids:
                    old_user_group_ids = groups_obj.search(cr, uid, [
                        ('users', '=', user_id),
                        ('is_protocollo_profile', '=', True)
                    ], context=context)
                    self.associate_profile_to_user(cr, uid, profile, old_user_group_ids, user_id)

                if uid != SUPERUSER_ID:
                    old_group_ids = old_profile_group_ids[profile.id]
                    new_group_ids = profile.groups_id.ids

                    group_obj = self.pool.get('res.groups')

                    removed_group_ids = list(set(old_group_ids) - set(new_group_ids))
                    removed_group_names = []
                    for removed_group_id in removed_group_ids:
                        group = group_obj.browse(cr, uid, removed_group_id)
                        removed_group_names.append(group.name)

                    added_group_ids = list(set(new_group_ids) - set(old_group_ids))
                    added_group_names = []
                    for added_group_id in added_group_ids:
                        group = group_obj.browse(cr, uid, added_group_id)
                        added_group_names.append(group.name)

                    action_class = "history_icon update"
                    body = "<div class='%s'><ul>" % action_class
                    if removed_group_names:
                        body = body + "<li>%s: <span style='color:#990000'> %s</span></li>" % ('Permessi Eliminati', ', '.join(removed_group_names))
                    if added_group_names:
                        body = body + "<li>%s: <span style='color:#007ea6'> %s </span></li>" % ('Permessi Aggiunti', ', '.join(added_group_names))
                    body += "</ul></div>"
                    post_vars = {
                        'subject': 'Modifica Profilo',
                        'body': body,
                        'model': 'protocollo.profile',
                        'res_id': profile.id
                    }
                    self.message_post(cr, uid, profile.id, type='notification', context=context, **post_vars)

        return True

    def associate_profile_to_user(self, cr, uid, profile, old_profile_group_ids, user_id):
        group_id_value = []
        user_obj = self.pool.get('res.users')

        # (3, ID) delete the link
        delete_protocollo_group_ids = list(set(old_profile_group_ids))
        if profile:
            delete_protocollo_group_ids = list(set(old_profile_group_ids) - set(profile.groups_id.ids))
        if delete_protocollo_group_ids:
            for group_id in delete_protocollo_group_ids:
                group_id_value.append((3, group_id))

        # (4, ID) add the link
        add_protocollo_group_ids = []
        if profile:
            add_protocollo_group_ids = list(set(profile.groups_id.ids) - set(old_profile_group_ids))
        if add_protocollo_group_ids:
            for group_id in add_protocollo_group_ids:
                group_id_value.append((4, group_id))

        if group_id_value:
            user_obj.write(cr, uid, [user_id], {
                'groups_id': group_id_value
            })