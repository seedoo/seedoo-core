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
import email

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

    # Estensione del metodo per fare il fetch delle email con un content type diverso da mixed: le email in questione
    # sono prive di body e contengono solamente l'allegato, pertanto il relativo content type coincide con quello del
    # file inviato. Ad esempio se verrà inviata una mail con content type application/pdf, il contenuto deve essere
    # parsato per inserirlo come allegato del messaggio.
    # Il codice del metodo è stato recuperato dalla versione 12 di odoo dove la problematica è stata gestita.
    def _message_extract_payload(self, message, save_original=False):
        """Extract body as HTML and attachments from the mail message"""
        attachments = []
        body = u''
        if save_original:
            attachments.append(('original_email.eml', message.as_string()))

        # Be careful, content-type may contain tricky content like in the
        # following example so test the MIME type with startswith()
        #
        # Content-Type: multipart/related;
        #   boundary="_004_3f1e4da175f349248b8d43cdeb9866f1AMSPR06MB343eurprd06pro_";
        #   type="text/html"
        if message.get_content_maintype() == 'text':
            encoding = message.get_content_charset()
            body = message.get_payload(decode=True)
            body = tools.ustr(body, encoding, errors='replace')
            if message.get_content_type() == 'text/plain':
                # text/plain -> <pre/>
                body = tools.append_content_to_html(u'', body, preserve=True)
        else:
            alternative = False
            mixed = False
            html = u''
            for part in message.walk():
                if part.get_content_type() == 'multipart/alternative':
                    alternative = True
                if part.get_content_type() == 'multipart/mixed':
                    mixed = True
                if part.get_content_maintype() == 'multipart':
                    continue  # skip container
                # part.get_filename returns decoded value if able to decode, coded otherwise.
                # original get_filename is not able to decode iso-8859-1 (for instance).
                # therefore, iso encoded attachements are not able to be decoded properly with get_filename
                # code here partially copy the original get_filename method, but handle more encoding
                filename=part.get_param('filename', None, 'content-disposition')
                if not filename:
                    filename=part.get_param('name', None)
                if filename:
                    if isinstance(filename, tuple):
                        # RFC2231
                        filename=email.utils.collapse_rfc2231_value(filename).strip()
                    else:
                        filename=decode(filename)
                encoding = part.get_content_charset()  # None if attachment
                # 1) Explicit Attachments -> attachments
                if filename or part.get('content-disposition', '').strip().startswith('attachment'):
                    attachments.append((filename or 'attachment', part.get_payload(decode=True)))
                    continue
                # 2) text/plain -> <pre/>
                if part.get_content_type() == 'text/plain' and (not alternative or not body):
                    body = tools.append_content_to_html(body, tools.ustr(part.get_payload(decode=True),
                                                                         encoding, errors='replace'), preserve=True)
                # 3) text/html -> raw
                elif part.get_content_type() == 'text/html':
                    # mutlipart/alternative have one text and a html part, keep only the second
                    # mixed allows several html parts, append html content
                    append_content = not alternative or (html and mixed)
                    html = tools.ustr(part.get_payload(decode=True), encoding, errors='replace')
                    if not append_content:
                        body = html
                    else:
                        body = tools.append_content_to_html(body, html, plaintext=False)
                # 4) Anything else -> attachment
                else:
                    attachments.append((filename or 'attachment', part.get_payload(decode=True)))
        return body, attachments