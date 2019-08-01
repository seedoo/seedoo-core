# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import orm, fields, osv
from openerp.addons.mail.mail_message import decode
from openerp import api, tools
import datetime
import dateutil
import logging
import pytz

_logger = logging.getLogger(__name__)

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

    def message_parse(self, cr, uid, message, save_original=False, context=None):
        msg_dict = super(MailThread, self).message_parse(cr, uid, message, save_original, context)

        stored_date = False
        if message.get('Received'):
            try:
                received_hdr = decode(message.get('Received'))
                received_hdr_list = received_hdr.split(';')
                date_hdr = received_hdr_list[1].strip()
                parsed_date = dateutil.parser.parse(date_hdr, fuzzy=True)
                if parsed_date.utcoffset() is None:
                    # naive datetime, so we arbitrarily decide to make it
                    # UTC, there's no better choice. Should not happen,
                    # as RFC2822 requires timezone offset in Date headers.
                    stored_date = parsed_date.replace(tzinfo=pytz.utc)
                else:
                    stored_date = parsed_date.astimezone(tz=pytz.utc)
            except Exception:
                _logger.warning('Failed to parse Received header %r in incoming mail '
                                'with message-id %r, assuming current date/time.',
                                message.get('Received'), msg_dict['message_id'])
        if not stored_date:
            stored_date = datetime.datetime.now()
        msg_dict['server_received_datetime'] = stored_date.strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT)

        return msg_dict