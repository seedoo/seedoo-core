from odoo.addons.fl_mail_client.tests.common import MailClientTestCommon
from odoo.tests import tagged, users
from odoo.tools import mute_logger


@tagged('-standard', 'fl_mail')
class MailClientTestAccount(MailClientTestCommon):

    @mute_logger("odoo.models.unlink")
    @users("mailclientTestUser0")
    def test_account_permission(self):
        # Test lettura email in ingresso da account senza permessi
        mail_id = self.mail_obj.with_user(self.env.user).search([("id", "=", self.incoming_mail.id)]).id
        self.assertFalse(mail_id)

        # Creazione permessi incoming email
        account_permission = self.create_account_permission(self.env.user, self.mail_client_account, True)

        # Test lettura email in ingresso da account con permessi
        mail_id = self.mail_obj.with_user(self.env.user).search([("id", "=", self.incoming_mail.id)]).id
        self.assertTrue(isinstance(mail_id, int))
        account_permission.unlink()

        # Test lettura email da account in uscita senza permessi
        mail_id = self.mail_obj.with_user(self.env.user).search([("id", "=", self.outgoing_mail.id)]).id
        self.assertFalse(mail_id)

        # Creazione permessi outgoing email
        account_permission = self.create_account_permission(self.env.user, self.mail_client_account, False, True)

        # Test lettura email da account in uscita senza permessi
        mail_id = self.mail_obj.with_user(self.env.user).search([("id", "=", self.outgoing_mail.id)]).id
        self.assertTrue(isinstance(mail_id, int))
        account_permission.unlink()

        