from odoo import api, fields, models, tools, _
import logging
import poplib
import datetime
import dateutil


_logger = logging.getLogger(__name__)

MAX_POP_MESSAGES = 50
MAIL_TIMEOUT = 60

# Workaround for Python 2.7.8 bug https://bugs.python.org/issue23906
poplib._MAXLINE = 65536


class FetchmailServer(models.Model):

    _inherit = "fetchmail.server"

    @api.model
    def _default_mail_client(self):
        if self.env.user.has_group("fl_mail_client.group_fl_mail_client_manager"):
            return True
        return False

    mail_client = fields.Boolean(
        string="Mail Client Active",
        default=_default_mail_client
    )

    mail_client_account_ids = fields.One2many(
        "fl.mail.client.account",
        "fetchmail_server_id",
        string="Mail Client Accounts",
    )

    mail_client_account_id = fields.Many2one(
        string="Mail Client Account",
        comodel_name="fl.mail.client.account",
        compute="_compute_mail_client_account_id",
    )

    mail_client_fetch_all = fields.Boolean(
        string="Fetch read and unread messages"
    )

    history_ids = fields.One2many(
        "fetchmail.server.history",
        "fetchmail_server_id",
        string="History",
    )

    def fetch_mail(self):
        """ WARNING: meant for cron usage only - will commit() after each email! """
        additionnal_context = {
            'fetchmail_cron_running': True
        }
        MailThread = self.env['mail.thread']
        for server in self:
            _logger.info('start checking for new emails on %s server %s', server.server_type, server.name)
            additionnal_context['default_fetchmail_server_id'] = server.id
            datetime_start = datetime.datetime.now()
            error_description = ''
            count, failed = 0, 0
            selected_inbox = None
            imap_server, pop_server = None, None
            data = []

            if server.server_type == 'imap':
                try:
                    imap_server = server.connect()
                    # Gestione della selezione della inbox dalla quale eseguire il fetch
                    try:
                        inbox_to_fetch = server._get_folder_to_fetch(server)
                        selected_inbox = imap_server.select(mailbox=inbox_to_fetch, readonly=False)
                        if selected_inbox[0] != "OK":
                            _logger.exception("Failed to select the folder: %s" % selected_inbox[1])
                            return
                    except Exception as exception_select_folder:
                        _logger.exception("Failed to select the folder: %s" % exception_select_folder)

                    # Ricerca delle mail non lette
                    result_unseen, data_unseen = imap_server.uid('search', None, '(UNSEEN)')
                    splitted_data_unseen = data_unseen[0].split()
                    data += splitted_data_unseen
                    if server.mail_client_fetch_all:
                        # Ricerca di tutte le mail lette
                        result_seen, data_seen = imap_server.uid('search', None, '(SEEN)')
                        data += data_seen[0].split()

                    for num in data:
                        current_mail_error_description = ""
                        is_unseen = num in splitted_data_unseen
                        fetched_result, fetched_data = imap_server.uid('fetch', num, '(RFC822)')
                        _logger.info("Processing mail %s (%s succeed - %s failed)" % (num, count, failed))

                        if not fetched_data:
                            _logger.info("Fetched mail %s has not returned any value" % num)
                            failed += 1
                            continue

                        # La mail viene messa come non letta in caso ci siano errori
                        if is_unseen:
                            imap_server.uid('STORE', num, '-FLAGS', '(\\Seen)')

                        try:
                            message = False
                            if server.mail_client:
                                message = MailThread.with_context(**additionnal_context).message_process_for_mail_client(server.object_id.model, fetched_data[0][1], save_original=server.original, strip_attachments=(not server.attach), server=server)
                            else:
                                MailThread.with_context(**additionnal_context).message_process(server.object_id.model, fetched_data[0][1], save_original=server.original, strip_attachments=(not server.attach))
                            # La mail viene messa come letta
                            if is_unseen:
                                imap_server.uid('STORE', num, '+FLAGS', '(\\Seen)')
                            self._log_fetched_message(message)
                        except Exception as e:
                            current_mail_error_description += self._get_mail_error_description(fetched_data[0][1], num, e)
                            error_description += current_mail_error_description
                            _logger.info('Failed to process mail from %s server %s.', server.server_type, server.name, exc_info=True)
                            failed += 1

                        # Operazioni dopo il fetch e la creazione della mail
                        errors_after_fetch = server._after_fetch(server, imap_server, num, current_mail_error_description, self._cr, is_unseen)
                        if errors_after_fetch:
                            error_description += "<li>%s</li>" % str(errors_after_fetch)
                            if not current_mail_error_description:
                                failed += 1
                            continue

                        self._cr.commit()
                        count += 1
                    count = count if count >= 0 else 0
                    _logger.info("Fetched %d email(s) on %s server %s; %d succeeded, %d failed.", count, server.server_type, server.name, (count - failed), failed)
                except Exception as e:
                    error_description += "<li>%s</li>" % str(e)
                    _logger.info("General failure when trying to fetch mail from %s server %s.", server.server_type, server.name, exc_info=True)
                finally:
                    if imap_server and selected_inbox[0] == "OK":
                        imap_server.close()
                        imap_server.logout()

            elif server.server_type == 'pop':
                try:
                    while True:
                        failed_in_loop = 0
                        num = 0
                        pop_server = server.connect()

                        (num_messages, total_size) = pop_server.stat()
                        pop_server.list()
                        for num in range(1, min(MAX_POP_MESSAGES, num_messages) + 1):
                            current_mail_error_description = ""
                            _logger.info("Processing mail %s (%s succeed - %s failed)" % (num, (num - failed_in_loop - 1), failed_in_loop))
                            (header, messages, octets) = pop_server.retr(num)
                            message = (b'\n').join(messages)
                            try:
                                fetched_message = False
                                if server.mail_client:
                                    fetched_message = MailThread.with_context(**additionnal_context).message_process_for_mail_client(server.object_id.model, message, save_original=server.original, strip_attachments=(not server.attach), server=server)
                                else:
                                    MailThread.with_context(**additionnal_context).message_process(server.object_id.model, message, save_original=server.original, strip_attachments=(not server.attach))
                                pop_server.dele(num)
                                self._log_fetched_message(fetched_message)
                            except Exception as e:
                                current_mail_error_description += self._get_mail_error_description(message, num, e)
                                error_description += current_mail_error_description
                                _logger.info('Failed to process mail from %s server %s.', server.server_type, server.name, exc_info=True)
                                failed += 1
                                failed_in_loop += 1
                            self.env.cr.commit()
                            count += 1
                        count = count if count >= 0 else 0
                        _logger.info("Fetched %d email(s) on %s server %s; %d succeeded, %d failed.", num, server.server_type, server.name, (num - failed_in_loop), failed_in_loop)
                        # Stop if (1) no more message left or (2) all messages have failed
                        if num_messages < MAX_POP_MESSAGES or failed_in_loop == num:
                            break
                        pop_server.quit()
                except Exception as e:
                    error_description += "<li>%s</li>" % str(e)
                    _logger.info("General failure when trying to fetch mail from %s server %s.", server.server_type, server.name, exc_info=True)
                finally:
                    if pop_server:
                        pop_server.quit()

            server.write({'date': fields.Datetime.now()})

            server_history_vals = {
                'fetchmail_server_id': server.id,
                'action': 'fetch',
                'result': 'error' if error_description else 'success',
                'error_description': error_description,
                'email_successed_count': count - failed,
                'email_failed_count': failed,
                'datetime_start': datetime_start,
                'datetime_end': datetime.datetime.now()
            }
            server_history_obj = self.env['fetchmail.server.history']
            server_history_obj.create(server_history_vals)

        return True

    def _log_fetched_message(self, message):
        if not message:
            return
        _logger.info(self._get_log_output(message))

    def _get_log_output(self, message):
        return "Fetched message: Id '%s'" % message.id

    def _compute_mail_client_account_id(self):
        for rec in self:
            if rec.mail_client_account_ids:
                rec.mail_client_account_id = rec.mail_client_account_ids[0].id
            else:
                rec.mail_client_account_id = False

    def _after_fetch(self, server, imap_server, num, error_description, cr, is_unseen):
        return

    def _get_folder_to_fetch(self, server):
        return "INBOX"

    def _get_mail_error_description(self, mail_message, num, exception):
        default_mail_info = "<hr/><b>MAIL %s:</b>" % str(num)
        try:
            mail_message, message_bytes = self.env["mail.thread"].get_message_to_process(
                mail_message
            )
            if mail_message.get("message-id"):
                mail_id = tools.decode_message_header(
                    mail_message, "message-id"
                )
                mail_info = "<hr/><b>MAIL %s</b>" % tools.html_escape(mail_id)
            if mail_message.get("Date"):
                mail_date = tools.decode_message_header(
                    mail_message, "Date"
                )
                mail_date_parsed = dateutil.parser.parse(mail_date, fuzzy=True)
                mail_info += "<li><b>%s</b>: %s</li>" % (
                    _("Date"), mail_date_parsed.strftime("%d-%m-%Y %H:%M:%S")
                )
            if mail_message.get("Subject"):
                mail_subject = tools.decode_message_header(
                    mail_message, "Subject"
                )
                mail_info += "<li><b>%s</b>: %s</li>" % (
                    _("Subject"), tools.html_escape(mail_subject)
                )
        except:
            mail_info = default_mail_info
        mail_error_description = mail_info + "<li><b>%s</b>: %s</li>" % (
            _("Error"), tools.html_escape(str(exception))
        )
        return mail_error_description