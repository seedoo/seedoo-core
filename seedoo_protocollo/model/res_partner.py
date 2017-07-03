# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import orm
from openerp import netsvc
from openerp import SUPERUSER_ID
import logging

from openerp.osv import *

_logger = logging.getLogger(__name__)


class ResPartner(orm.Model):
    # inherit partner because PEC mails are not supposed to be associate to
    # generic models
    _inherit = "res.partner"

    def message_post(
            self, cr, uid, thread_id, body='', subject=None, type='notification',
            subtype=None, parent_id=False, attachments=None, context=None,
            content_subtype='html', **kwargs
    ):
        if context is None:
            context = {}
        msg_id = super(ResPartner, self).message_post(
            cr, uid, thread_id, body=body, subject=subject, type=type,
            subtype=subtype, parent_id=parent_id, attachments=attachments,
            context=context, content_subtype=content_subtype, **kwargs)
        if (
                    context.get('main_message_id') and
                    (
                                context.get('pec_type') or
                                context.get('send_error')
                    )
        ):
            wf_service = netsvc.LocalService("workflow")
            _logger.info('workflow: mail message trigger')
            wf_service.trg_trigger(uid, 'mail.message',
                                   context['main_message_id'], cr)
        return msg_id