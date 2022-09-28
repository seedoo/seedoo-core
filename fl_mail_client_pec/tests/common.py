from odoo.addons.fl_mail_client.tests.common import MailClientTestCommon
from odoo.tests import tagged


@tagged('-standard', 'fl_mail')
class MailClientPecTestCommon(MailClientTestCommon):

    @classmethod
    def setUpClass(cls):
        super(MailClientPecTestCommon, cls).setUpClass()

        fertchmail_server_pec = cls.fetchmail_server_obj.create({
            "name": "FetchMailTestPec",
            "server_type": "imap",
            "server": "imap.gmail.com",
            "port": 993,
            "user": "test@flosslab.com",
            "password": "test@flosslab.com",
            "is_ssl": True,
            "original": True,
            "mail_client": True,
            "mail_client_account_pec": True
        })

        cls.mail_client_account_pec = cls.fl_mail_client_account_obj.create({
            "description": "MailClientPecTest",
            "email": "test@flosslab.com",
            "fetchmail_server_id": fertchmail_server_pec.id,
            "ir_mail_server_id": cls.mail_server.id,
            "pec": True
        })
