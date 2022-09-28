from odoo.addons.fl_mail_client.tests.common import MailClientTestFetchmailServerCommon
from odoo.addons.fl_mail_client_pec.tests.common import MailClientPecTestCommon
from odoo.modules import get_module_resource
from odoo.tests import tagged


@tagged('-standard', 'fl_mail')
class MailClienPectTestFetchmailServerPec(MailClientPecTestCommon, MailClientTestFetchmailServerCommon):

    def _get_original_email_eml(self, server):
        if not server.mail_client_account_pec:
            return super(MailClienPectTestFetchmailServerPec, self)._get_original_email_eml(server)
        file_dict = ["accettazione.eml", "conferma.eml", "mancata_consegna.eml"]
        file_data_dict = []
        for file in file_dict:
            mail_path = get_module_resource("fl_mail_client_pec", "tests/static/files", file)
            with open(mail_path, "rb") as data:
                file_data_dict.append(data.read())
        return file_data_dict

    def test_fetchmail_server_fetch_pec(self):
        # Mail utilizzata per ricollegare la ricevuta di accettazione e conferma.
        outgoing_mail = self.outgoing_mail
        outgoing_mail.update({
            "pec": True,
            "email_to": "test01@pec.flosslab.it",
            "message_id": "<R43XS7$8A2B712B1EC45527B69E94AB60B8CA07@pec.it>"})

        # Mail utilizzata per ricollegare la ricevuta di mancata consegna.
        outgoing_mail2 = self.outgoing_mail2
        outgoing_mail2.update({
            "pec": True,
            "message_id": "<R43YMM$D7F793DD43B6B427D6C13182BD067782@pec.it>"})

        with self.mock_mail_gateway():
            mail_list = self.mail_client_account_pec.fetchmail_server_id.fetch_mail()

        accettazione, conferma, errore = mail_list[0], mail_list[1], mail_list[2]

        # Controlle cambiamenti avvenuti per via della ricezione delle ricevute di conferma e accettazione
        self.assertEqual(outgoing_mail.state, "received")
        self.assertEqual(len(outgoing_mail.pec_mail_child_ids.ids), 2)

        # ACCETTAZIONE (outgoing_mail)
        self.assertTrue(accettazione.pec)
        self.assertEqual(accettazione.state, "incoming")
        self.assertEqual(accettazione.pec_type, "accettazione")
        self.assertEqual(accettazione.pec_mail_parent_id.id, outgoing_mail.id)
        self.assertFalse(accettazione.recipient_addr)
        self.assertEqual(accettazione.resized_subject, "ACCETTAZIONE: Subject test prova pec")
        self.assertEqual(accettazione.cert_datetime.strftime("%m/%d/%Y, %H:%M:%S"), "12/14/2021, 13:36:08")

        # AVVENUTA CONSEGNA (outgoing_mail)
        self.assertTrue(conferma.pec)
        self.assertEqual(conferma.state, "incoming")
        self.assertEqual(conferma.pec_type, "avvenuta-consegna")
        self.assertEqual(conferma.pec_mail_parent_id.id, outgoing_mail.id)
        self.assertEqual(conferma.recipient_addr, "test01@pec.flosslab.it")
        self.assertEqual(conferma.resized_subject, "CONSEGNA: Subject test prova pec")
        self.assertEqual(conferma.cert_datetime.strftime("%m/%d/%Y, %H:%M:%S"), "12/14/2021, 13:36:08")

        # Controlle cambiamenti avvenuti per via della ricezione della ricevuta mancata consegna
        self.assertEqual(outgoing_mail2.state, "exception")
        self.assertEqual(len(outgoing_mail2.pec_mail_child_ids.ids), 1)
        self.assertEqual(outgoing_mail2.failure_reason, "5.1.1 - Aruba Pec S.p.A. - indirizzo non valido")

        # MANCATA CONSEGNA (outgoing_mail2)
        self.assertTrue(errore.pec)
        self.assertEqual(errore.state, "incoming")
        self.assertEqual(errore.pec_type, "errore-consegna")
        self.assertEqual(errore.failure_reason, "5.1.1 - Aruba Pec S.p.A. - indirizzo non valido")
        self.assertEqual(errore.pec_mail_parent_id.id, outgoing_mail2.id)
        self.assertEqual(errore.recipient_addr, "provaprova@pec.flosslab.it")
        self.assertEqual(errore.resized_subject, "AVVISO DI MANCATA CONSEGNA: prova")
        self.assertEqual(errore.cert_datetime.strftime("%m/%d/%Y, %H:%M:%S"), "12/14/2021, 13:54:32")
