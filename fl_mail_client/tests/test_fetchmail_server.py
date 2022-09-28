from odoo.addons.fl_mail_client.tests.common import MailClientTestFetchmailServerCommon, MailClientTestCommon
from odoo.tests import tagged


@tagged('-standard', 'fl_mail')
class MailClientTestFetchmailServer(MailClientTestCommon, MailClientTestFetchmailServerCommon):

    def test_fetchmail_server_fetch_email(self):
        with self.mock_mail_gateway():
            mail_list = self.mail_client_account.fetchmail_server_id.fetch_mail()
        mail = mail_list[0]

        self.assertEqual(mail.state, "incoming")
        self.assertEqual(mail.subject, "Subject test email")
        self.assertEqual(mail.message_id, "<CABnXwOOycgm8VhJb_kuWn=hrOC=6CNC7m3JqB7hV-RfYbKJ-vg@mail.gmail.com>")
        self.assertEqual(mail.email_from, '"Send Mail Developers" <sendmail@flosslab.com>')
        self.assertEqual(mail.email_to, '"User 00 Test" <testuser00@flosslab.com>')
        self.assertEqual(mail.email_cc, '"User 01 Test" <testuser01@flosslab.com>')
        self.assertEqual(mail.server_received_datetime.strftime("%m/%d/%Y, %H:%M:%S"), "12/14/2021, 09:35:21")