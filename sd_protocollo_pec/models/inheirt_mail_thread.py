import base64

from odoo import models, fields, api


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    def message_process_for_mail_client(self, model, message, custom_values=None, save_original=False,
                                        strip_attachments=False, thread_id=None, server=None):
        invio_obj = self.env["sd.protocollo.invio"]
        mail_mail = super(MailThread, self).message_process_for_mail_client(model, message, custom_values, save_original, strip_attachments, thread_id, server)
        if not mail_mail or not mail_mail.pec or mail_mail.pec_type != "accettazione":
            return mail_mail

        pec_mail_parent = mail_mail.pec_mail_parent_id
        invio = invio_obj.search([("messaggio_id", "=", pec_mail_parent.id)])
        if not invio:
            return mail_mail

        daticert_file = [x for x in mail_mail.attachment_ids if x.name == "daticert.xml"]
        if not daticert_file:
            return mail_mail

        daticert = base64.b64decode(daticert_file[0].datas).decode()
        msg_dict = self.parse_daticert_recipients(daticert)

        if "transmission_type" in msg_dict:
            for mail, value in msg_dict["transmission_type"].items():
                if mail:
                    for destinatario in invio.destinatario_ids:
                        if destinatario.email == mail.lower():
                            destinatario.daticert_tipo = value

        return mail_mail

    @api.model
    def message_parse(self, message, save_original=False):
        mail_obj = self.env["mail.mail"]
        msg_dict = super(MailThread, self).message_parse(message, save_original)
        # Aggiunta del protocollo alle ricevute ricollegate alla mail principale
        if msg_dict and msg_dict.get("pec_mail_parent_id", False):
            mail = mail_obj.browse(msg_dict["pec_mail_parent_id"])
            if mail.protocollo_id:
                msg_dict.update({"protocollo_id": mail.protocollo_id.id})
        return msg_dict
