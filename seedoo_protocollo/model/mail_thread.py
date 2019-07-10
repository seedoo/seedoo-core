# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import orm, fields, osv
from openerp.addons.mail.mail_message import decode

def decode_header(message, header, separator=' '):
    return separator.join(map(decode, filter(None, message.get_all(header, []))))

class MailThread(orm.Model):
    _inherit = 'mail.thread'

    def message_route(self, cr, uid, message, message_dict, model=None, thread_id=None, custom_values=None, context=None):
        if context and context.has_key('fetchmail_server_id') and context['fetchmail_server_id']:
            fetchmail_server_obj = self.pool.get('fetchmail.server')
            fetchmail_server = fetchmail_server_obj.browse(cr, uid, context['fetchmail_server_id'])

            delivered_to = decode_header(message, 'Delivered-To')
            if not delivered_to:
                delivered_to_header = ('Delivered-To', fetchmail_server.user)
                message._headers.append(delivered_to_header)

        return super(MailThread, self).message_route(cr, uid, message, message_dict, model, thread_id, custom_values, context)
