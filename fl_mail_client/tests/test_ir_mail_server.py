from odoo.addons.fl_mail_client.tests.common import MailClientTestCommon, MailClientTestFetchmailServerCommon
from odoo.tests import tagged

message_id = "<289842783188445.1637935359.798892259597778-openerp-message-notify>"

@tagged('-standard', 'fl_mail')
class MailClientTestIrMailServer(MailClientTestCommon, MailClientTestFetchmailServerCommon):

    def test_build_email(self):
        # Build di un object email che dovrà ritrovare i bcc dalla mail.mail con message_id passato.
        mail_data = self.mail_data.copy()
        mail_data.update({
            "email_bcc": "prova1@example.com,prova2@example.com",
            "message_id": message_id
        })
        self.mail_obj.create(mail_data)

        with self.mock_mail_gateway():
            message = self.mail_client_account.ir_mail_server_id.build_email(
                email_from="sender@example.com",
                email_to="recipient@example.com",
                subject="Subject",
                body="The body of an email",
                message_id=message_id
            )
        self.assertEqual(message._headers[6][1], "prova1@example.com, prova2@example.com")
