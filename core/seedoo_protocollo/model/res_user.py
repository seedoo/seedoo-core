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