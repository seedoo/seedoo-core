import email
import logging
import dateutil
import pytz
import base64

try:
    from xmlrpc import client as xmlrpclib
except ImportError:
    import xmlrpclib

from odoo import models, api, tools, SUPERUSER_ID, _
from datetime import datetime
from email.message import EmailMessage
from bs4 import BeautifulSoup
import re

_logger = logging.getLogger(__name__)


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    @api.model
    def message_parse(self, message, save_original=False):
        msg_dict = super(MailThread, self).message_parse(message, save_original)

        server_received_datetime = False
        try:
            for header in message._headers:
                if header[0] == 'Received':
                    received_header = header[1]
                    received_hdr_list = received_header.split(';')
                    date_hdr = received_hdr_list[1].strip()
                    parsed_date = dateutil.parser.parse(date_hdr, fuzzy=True)
                    if parsed_date.utcoffset() is None:
                        # Naive datetime, so we arbitrarily decide to make it UTC, there's no better choice.
                        # Should not happen, as RFC2822 requires timezone offset in Date headers.
                        server_received_datetime = parsed_date.replace(tzinfo=pytz.utc)
                    else:
                        server_received_datetime = parsed_date.astimezone(tz=pytz.utc)
                    break
        except Exception:
            _logger.warning("Failed to parse 'Received' header in incoming mail with message-id %r, assuming current date/time.", msg_dict['message_id'])

        if not server_received_datetime:
            server_received_datetime = datetime.now()
        msg_dict['server_received_datetime'] = server_received_datetime.strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT)

        try:
            # Remove "base" html tag from incoming email
            soup = BeautifulSoup(msg_dict["body"], features="lxml")
            base_tags = soup.findAll("base")
            for tag in base_tags:
                tag.decompose()
            if soup:
                msg_dict["body"] = soup.prettify()
        except Exception as e:
            logging.warning("Errore nella rimozione del tag base nel parsing del messaggio: " + e)

        return msg_dict


    def _message_parse_extract_payload(self, message, save_original=False):
        """
        Extract body as HTML and attachments from the mail message.
        Il metodo viene sovrascritto per eliminare dal parsing della mail tutte le parti di contenuto che non rientrano
        nelle seguenti categorie: inline attachments, explicit attachments, text/plain, text/html. In pratica si
        commenta il caso 4. Il classico esempio di questa problematica lo si ha nel parsing del postacert.eml di una
        PEC, oltre ai vari allegati contenuti nel postacert.eml vengono aggiunti degli attachment relativi a parti del
        content non classificate.
        """
        attachments = []
        body = u''
        if save_original:
            attachments.append(self._Attachment('original_email.eml', message.as_string(), {}))

        # Be careful, content-type may contain tricky content like in the
        # following example so test the MIME type with startswith()
        #
        # Content-Type: multipart/related;
        #   boundary="_004_3f1e4da175f349248b8d43cdeb9866f1AMSPR06MB343eurprd06pro_";
        #   type="text/html"
        if message.get_content_maintype() == 'text':
            encoding = message.get_content_charset()
            body = message.get_content()
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

                filename = part.get_filename()  # I may not properly handle all charsets
                encoding = part.get_content_charset()  # None if attachment

                # 0) Inline Attachments -> attachments, with a third part in the tuple to match cid / attachment
                if filename and part.get('content-id'):
                    inner_cid = part.get('content-id').strip('><')
                    attachments.append(self._Attachment(filename, part.get_content(), {'cid': inner_cid}))
                    continue
                # 1) Explicit Attachments -> attachments
                if filename or part.get('content-disposition', '').strip().startswith('attachment'):
                    attachments.append(self._Attachment(filename or 'attachment', part.get_content(), {}))
                    continue
                # 2) text/plain -> <pre/>
                if part.get_content_type() == 'text/plain' and (not alternative or not body):
                    body = tools.append_content_to_html(body, tools.ustr(part.get_content(),
                                                                         encoding, errors='replace'), preserve=True)
                # 3) text/html -> raw
                elif part.get_content_type() == 'text/html':
                    # mutlipart/alternative have one text and a html part, keep only the second
                    # mixed allows several html parts, append html content
                    append_content = not alternative or (html and mixed)
                    html = tools.ustr(part.get_content(), encoding, errors='replace')
                    if not append_content:
                        body = html
                    else:
                        body = tools.append_content_to_html(body, html, plaintext=False)
                    # we only strip_classes here everything else will be done in by html field of mail.message
                    body = tools.html_sanitize(body, sanitize_tags=False, strip_classes=True)
                # 4) Anything else -> attachment
                ########################################################################################################
                # else:
                #     attachments.append(self._Attachment(filename or 'attachment', part.get_content(), {}))
                ########################################################################################################

        return self._message_parse_extract_payload_postprocess(message, {'body': body, 'attachments': attachments})


    @api.model
    def get_mail_values(self, message, message_parse_values, server):
        values = dict(message_parse_values)
        values.update({
            'author_id': False,
            # 'email_from': email_from,
            'model': False,
            'res_id': False,
            # 'body': body,
            # 'subject': subject or False,
            # 'message_type': message_type,
            # 'parent_id': parent_id,
            # 'subtype_id': subtype_id,
            # 'partner_ids': partner_ids,
            # 'channel_ids': channel_ids,
            # 'add_sign': add_sign,
            # 'record_name': record_name,
            'account_id': server.mail_client_account_ids[0].id,
            'direction': 'in'
        })

        self._mail_post_process_attachments(values, "attachments", "attachment_ids")
        self._mail_post_process_attachments(values, "original_attachments", "original_attachment_ids")

        headers = ''
        for header in message._headers:
            headers += '%s: %s;\r\n' % (header[0], header[1])

        values.update({
            'headers': headers,
            'body_html': values.get('body', False),
            'email_to': self._get_email_beautify(values.get('to', False)),
            'email_cc': self._get_email_beautify(values.get('cc', False)),
            'auto_delete': False,
            'notification': False,
            'state': 'incoming',
        })

        # remove computational values not stored on mail.message and avoid warnings when creating it
        for x in ('from', 'to', 'cc', 'recipients', 'in_reply_to', 'bounced_email', 'bounced_message',
                  'bounced_msg_id', 'bounced_partner', 'internal'):
            values.pop(x, None)

        return values

    def _get_email_beautify(self, mail_list):
        """
        Algoritmo per rimuovere le email duplicate all'interno del messaggio che viene ricevuto e parsato.

        L'algoritmo si occupa di fare uno split con sep="," per ricavarsi tutte le email, successivamente avviene un'operazione
        di sorting basato sulle email più lunghe, ovvero quelle contenenti anche il nome. Fatta la lista viene ciclata per ogni
        mail e viene fatta un'operazione di ricerca sulla lista dove andremo a inserire le email che ci serviranno. Se non risulta
        essere presente all'interno della lista viene aggiunta, altrimenti viene ricercato l'elemento più grande e viene lasciato in lista
        @param mail_list: stringa contenente tutte le email parsate
        @return: stringa contenente le email formattate
        """
        # Eseguo lo split e faccio il sorting dal più grande al più piccolo
        splitted_mail = sorted(mail_list.split(","), key=len, reverse=True)
        selective_mail_list = []
        for mail in splitted_mail:
            r = re.compile(".*%s" % mail)
            # verifico la presenza della mail in selective_mail_list, se non presente l'aggiungo alla lista, se presente
            # ricerco l'elemento più grande tra quelli presenti in lista e ne rimuovo il più piccolo
            current_list = list(filter(r.match, selective_mail_list))
            if not current_list:
                selective_mail_list.append(mail)
            else:
                current_list.append(mail)
                min_element = min(current_list, key=len)
                current_list.remove(min_element)
                # rimuovo l'elemnto minore da current_list e da selective_mail_list
                if min_element in selective_mail_list:
                    selective_mail_list.remove(min_element)
                # se l'elemento maggiore non è presente in selective_mail_list lo aggiungo
                if current_list[0] not in selective_mail_list:
                    selective_mail_list.append(current_list[0])
        return ", ".join(selective_mail_list)

    @api.model
    def message_process_for_mail_client(self, model, message, custom_values=None, save_original=False, strip_attachments=False, thread_id=None, server=None):
        """ Process an incoming RFC2822 email message, relying on
            ``mail.message.parse()`` for the parsing operation,
            and ``message_route()`` to figure out the target model.

            Once the target model is known, its ``message_new`` method
            is called with the new message (if the thread record did not exist)
            or its ``message_update`` method (if it did).

           :param string model: the fallback model to use if the message
               does not match any of the currently configured mail aliases
               (may be None if a matching alias is supposed to be present)
           :param message: source of the RFC2822 message
           :type message: string or xmlrpclib.Binary
           :type dict custom_values: optional dictionary of field values
                to pass to ``message_new`` if a new record needs to be created.
                Ignored if the thread record already exists, and also if a
                matching mail.alias was found (aliases define their own defaults)
           :param bool save_original: whether to keep a copy of the original
                email source attached to the message after it is imported.
           :param bool strip_attachments: whether to strip all attachments
                before processing the message, in order to save some space.
           :param int thread_id: optional ID of the record/thread from ``model``
               to which this mail should be attached. When provided, this
               overrides the automatic detection based on the message
               headers.
        """

        if not server.mail_client_account_ids:
            raise Exception(_("Inbox mail server is not associated with an account!"))

        message, message_bytes = self.get_message_to_process(message)
        
        # parse the message, verify we are not in a loop by checking message_id is not duplicated
        msg_dict = self.with_context(server_id=server.id).message_parse(message, save_original=False)

        if strip_attachments:
            msg_dict.pop('attachments', None)

        existing_msg_domain = self.get_existing_msg_domain(msg_dict, server)
        existing_msg_ids = self.env['mail.mail'].sudo().search(existing_msg_domain, limit=1)
        if existing_msg_ids:
            _logger.info('Ignored mail from %s to %s with Message-Id %s: found duplicated Message-Id during processing',
                         msg_dict.get('email_from'), msg_dict.get('to'), msg_dict.get('message_id'))
            return False

        # find possible routes for the message
        # routes = self.message_route(message, msg_dict, model, thread_id, custom_values)
        #thread_id = self._message_route_process(message, msg_dict, routes)

        values = self.get_mail_values(message, msg_dict, server)
        if save_original:
            values["original_eml"] = base64.b64encode(message_bytes)

        # new_message = self._message_create(values)
        new_message = self.env['mail.mail'].create(values)

        # # Set main attachment field if necessary
        # self._message_set_main_attachment_id(values['attachment_ids'])
        #
        # if values['author_id'] and values['message_type'] != 'notification' and not self._context.get(
        #         'mail_create_nosubscribe'):
        #     # if self.env['res.partner'].browse(values['author_id']).active:  # we dont want to add odoobot/inactive as a follower
        #     self._message_subscribe([values['author_id']])
        #
        # self._message_post_after_hook(new_message, values)
        # self._notify_thread(new_message, values)

        return new_message

    @api.model
    def get_message_to_process(self, message):
        # extract message bytes - we are forced to pass the message as binary because
        # we don't know its encoding until we parse its headers and hence can't
        # convert it to utf-8 for transport between the mailgate script and here.
        if isinstance(message, xmlrpclib.Binary):
            message = bytes(message.data)
        if isinstance(message, str):
            message = message.encode('utf-8')
        message_bytes = message
        message = email.message_from_bytes(message, policy=email.policy.SMTP)
        return message, message_bytes

    @api.model
    def _mail_post_process_attachments(self, values, attachment_key, attachment_ids_key):
        attachments = values.pop(attachment_key, [])
        attachment_ids = values.get(attachment_ids_key, [])
        # si cicla sui vari attachment per controllare che il content non sia un'istanza della classe EmailMessage
        for attachment_index in range(len(attachments)):
            attachment = attachments[attachment_index]
            if len(attachment) == 3 and isinstance(attachment[1], EmailMessage):
                attachments[attachment_index] = self._Attachment(attachment[0], attachment[1].as_string(),
                                                                 attachment[2])
        attachment_values = self._message_post_process_attachments(attachments, attachment_ids, values)
        values[attachment_ids_key] = attachment_values.get("attachment_ids", [])


    @api.model
    def get_existing_msg_domain(self, msg_dict, server):
        existing_msg_domain = [
            ("message_id", "=", msg_dict["message_id"]),
            ("fetchmail_server_id", "=", server.id),
        ]
        return existing_msg_domain