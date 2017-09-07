# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

import logging
from openerp.osv import fields, osv
from openerp.tools import (
    DEFAULT_SERVER_DATETIME_FORMAT as DSDF)
from openerp.tools.translate import _
import time
from openerp import netsvc

_logger = logging.getLogger(__name__)


class wizard(osv.TransientModel):
    """
        A wizard to manage the cancel state of protocol
    """
    _name = 'protocollo.cancel.wizard'
    _description = 'Cancel Protocol Management'

    _columns = {
        'name': fields.char(
            'Causa Cancellazione',
            required=True,
            readonly=False
        ),
        'user_id': fields.many2one(
            'res.users',
            'Responsabile',
            readonly=True
        ),
        'agent_id': fields.many2one(
            'res.users',
            'Mandante',
            readonly=False
        ),
        'date_cancel': fields.datetime(
            'Data Cancellazione',
            required=True,
            readonly=True
        ),
    }

    _defaults = {
        'user_id': lambda obj, cr, uid, context: uid,
        'agent_id': lambda obj, cr, uid, context: uid,
        'date_cancel': fields.datetime.now
    }

    def action_cancel(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids[0], context)
        if wizard.name and wizard.date_cancel:
            wf_service = netsvc.LocalService('workflow')
            wf_service.trg_validate(uid, 'protocollo.protocollo', context['active_id'], 'cancel', cr)

            protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'])
            if protocollo.type == 'in' and protocollo.pec:
                new_context = dict(context).copy()
                new_context.update({'receipt_cancel_reason': wizard.name})
                new_context.update({'receipt_cancel_author': wizard.agent_id.name})
                new_context.update({'receipt_cancel_date': wizard.date_cancel})
                self.pool.get('protocollo.protocollo').action_send_receipt(cr, uid, [protocollo.id], 'annullamento', context=new_context)

            action_class = "history_icon trash"
            body = "<div class='%s'><ul><li style='color:#990000;'><strong>Annullamento autorizzato da: %s</strong></li></ul></div>" % (action_class, wizard.agent_id.name)

            post_vars = {'subject': "Protocollo Annullato:  %s" %wizard.name,
                         'body': body,
                         'model': "protocollo.protocollo",
                         'res_id': context['active_id'],
                         }

            thread_pool = self.pool.get('protocollo.protocollo')
            thread_pool.message_post(cr, uid, context['active_id'], type="notification", context=context, **post_vars)

        return {'type': 'ir.actions.act_window_close'}
