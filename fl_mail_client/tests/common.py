from contextlib import contextmanager
from unittest.mock import patch

from odoo import SUPERUSER_ID
from odoo.addons.mail.tests.common import MailCase
from odoo.modules import get_module_resource
from odoo.tests import tagged, SavepointCase
from odoo.addons.fl_mail_client.models.inherit_fetchmail_server import FetchmailServer


@tagged('-standard', 'fl_mail')
class MailClientTestCommon(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super(MailClientTestCommon, cls).setUpClass()

        cls.res_users_obj = cls.env["res.users"]
        cls.fl_mail_client_account_obj = cls.env["fl.mail.client.account"]
        cls.fl_mail_client_account_permission_obj = cls.env["fl.mail.client.account.permission"]
        cls.fetchmail_server_obj = cls.env["fetchmail.server"]
        cls.mail_server_obj = cls.env["ir.mail_server"]
        cls.mail_obj = cls.env["mail.mail"]
        cls.mail_message_obj = cls.env["mail.message"]

        cls.admin = cls.res_users_obj.browse(SUPERUSER_ID)
        cls.user = cls.res_users_obj.create({
            "name": "MailCientTestUser0",
            "login": "mailclientTestUser0",
            "groups_id": [(4, cls.env.ref("fl_mail_client.group_fl_mail_client_user_advanced").id)]
        })

        fertchmail_server = cls.fetchmail_server_obj.create({
            "name": "FetchMailTest",
            "server_type": "imap",
            "server": "imap.gmail.com",
            "port": 993,
            "user": "test@flosslab.com",
            "password": "test@flosslab.com",
            "is_ssl": True,
            "original": True,
            "mail_client": True
        })

        cls.mail_server = cls.mail_server_obj.create({
            "name": "MailServerTest",
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 465,
            "smtp_user": "test@flosslab.com",
            "smtp_pass": "test@flosslab.com",
            "smtp_encryption": "ssl",
            "mail_client": True
        })

        cls.mail_client_account = cls.fl_mail_client_account_obj.create({
            "description": "MailClientTest",
            "email": "test01@flosslab.com",
            "fetchmail_server_id": fertchmail_server.id,
            "ir_mail_server_id": cls.mail_server.id,
        })

        cls.mail_data = {
            "account_id": cls.mail_client_account.id,
            "fetchmail_server_id": cls.mail_client_account.fetchmail_server_id.id,
            "body_html": "<p>Test</p>",
            "notification": False,
            "recipient_ids": [(4, cls.admin.partner_id.id)]
        }
        cls.mail_data.update({"direction": "in", "state": "incoming"})
        cls.incoming_mail = cls.mail_obj.create(cls.mail_data)

        cls.mail_data.update({"direction": "out", "state": "sent"})
        cls.outgoing_mail = cls.mail_obj.create(cls.mail_data)

        cls.mail_data.update({"direction": "out", "state": "sent"})
        cls.outgoing_mail2 = cls.mail_obj.create(cls.mail_data)

    def create_account_permission(self, user, account, incoming=False, outgoing=False, use_outgoing_server=False):
        return self.fl_mail_client_account_permission_obj.create({
            "user_id": user.id,
            "account_id": account.id,
            "show_inbox_mails": incoming,
            "show_outgoing_mails": outgoing,
            "use_outgoing_server": use_outgoing_server
        })

@tagged('-standard', 'fl_mail')
class MailClientTestFetchmailServerCommon(MailCase):

    @contextmanager
    def mock_mail_gateway(self, mail_unlink_sent=False, sim_error=None):
        # Estensione del metodo mock_mail_gateway originario di odoo, per inserire al suo interno una patch per il
        # fetch_mail, che, invece di fare, di norma, il fetch dal server, automaticamente si ricaverà da un file .eml
        # una mail, la quale dopo l'avvenuto parsing, come fatto dal metodo originario, restituirà un oggetto mail.mail.
        super(MailClientTestFetchmailServerCommon, self).mock_mail_gateway(mail_unlink_sent, sim_error)

        def _fetchmail_server_fetch(model, *args, **kwargs):
            # Simula il fetch di una email, e ne parsa il contenuto come avviene nel normale flusso
            MailThread = self.env['mail.thread']
            mail_list = []
            mail_data_list = self._get_original_email_eml(model)
            server = model
            additional_context = {
                "fetchmail_cron_running": True,
                "default_fetchmail_server_id": server.id
            }
            for mail_data in mail_data_list:
                mail_list.append(MailThread.with_context(**additional_context).message_process_for_mail_client(
                    server.object_id.model,
                    mail_data,
                    save_original=server.original,
                    strip_attachments=(not server.attach),
                    server=server
                ))
            return mail_list

        with patch.object(FetchmailServer, "fetch_mail", autospec=True, wraps=FetchmailServer, side_effect=_fetchmail_server_fetch) as fetchmail_server_fetch_mock:
            yield

    def _get_original_email_eml(self, server):
        mail_path = get_module_resource("fl_mail_client", "tests/static/files", "original_email.eml")
        with open(mail_path, "rb") as data:
            mail_data = data.read()
        return [mail_data]