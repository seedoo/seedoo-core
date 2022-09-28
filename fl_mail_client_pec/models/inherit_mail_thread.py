# -*- coding: utf-8 -*-

import email
import logging
import xml.etree.ElementTree as ET

from odoo import models, api, tools, SUPERUSER_ID, _
from datetime import datetime, timedelta
from email.header import decode_header, Header

_logger = logging.getLogger(__name__)


class MailThread(models.AbstractModel):

    _inherit = "mail.thread"


    @api.model
    def get_mail_values(self, message, message_parse_values, server):
        values = super(MailThread, self).get_mail_values(message, message_parse_values, server)
        values.update({
            "pec": message_parse_values.get("pec", False)
        })
        return values


    @api.model
    def get_existing_msg_domain(self, msg_dict, server):
        existing_msg_domain = super(MailThread, self).get_existing_msg_domain(msg_dict, server)

        pec_type = msg_dict.get("pec_type", False)
        pec_msg_id = msg_dict.get("pec_msg_id", False)
        if pec_type and pec_type!="posta-certificata" and pec_msg_id:
            existing_msg_domain.append(("pec_msg_id", "=", pec_msg_id))
            existing_msg_domain.append(("pec_type", "=", pec_type))

            recipient_addr = msg_dict.get("recipient_addr", False)
            if recipient_addr:
                existing_msg_domain.append(("recipient_addr", "=", recipient_addr))

        return existing_msg_domain


    @api.model
    def message_parse(self, message, save_original=False):
        msg_dict = super(MailThread, self).message_parse(message, save_original)
        # parse message pec headers
        pec_headers = self._get_message_pec_headers(message, msg_dict)
        x_trasporto = pec_headers.get("X-Trasporto", False)
        x_ricevuta = pec_headers.get("X-Ricevuta", False)
        # se nessuno degli header X-Trasporto e X-Ricevuta sono presenti allora non è un messaggio PEC
        if not x_trasporto and not x_ricevuta:
            return msg_dict
        # recupero degli allegati daticert.xml, postacert.eml, smime.p7s
        daticert, postacert, original_attachments = self._get_message_pec_attachments(msg_dict)
        # parsing daticert.xml
        daticert_dict = {}
        if daticert:
            daticert_dict = self.parse_daticert(daticert)
        # parsing postacert.eml
        postacert_dict = {}
        if postacert:
            postacert_dict = super(MailThread, self).message_parse(postacert, save_original=False)
            postacert_dict["attachments"] = [attachment_data for attachment_data in postacert_dict["attachments"]]
        # recupero del server_id dal context
        server_id = self._context.get("server_id", False)
        # se il server_id è assente nel context allora il parsing del messaggio non è stato chiamato dall'algoritmo di
        # fetch delle mail inserito tramite il modulo fl_mail_client, quindi l'algoritmo di parsing si deve interrompere
        if not server_id:
            if not postacert_dict:
                return msg_dict
            # se è presente il postacert allora gli allegati del messaggio devono essere organizzati in maniera tale da
            # evitare confusione tra gli allegati della mail originale e del postacert
            msg_dict["attachments"] = postacert_dict["attachments"] + original_attachments
            return msg_dict
        # se il server_id è presente nel context allora il parsing del messaggio è stato chiamato dall'algoritmo di
        # fetch delle mail inserito tramite il modulo fl_mail_client, quindi l'algoritmo di parsing può proseguire
        server = self.env["fetchmail.server"].browse(server_id)
        # si aggiorna il dizionario dei dati parsati impostando il campo pec a True
        msg_dict["pec"] = True
        # se nei daticert è presente il valore email_from lo eliminiamo prima di aggiornare i dati parsati del messaggio
        if "email_from" in daticert_dict:
            del daticert_dict["email_from"]
        # caso di una PEC con tipologia posta-certificata o di una email inviata ad un server PEC
        if x_trasporto == "posta-certificata" or x_trasporto == "errore":
            # se è il caso di una mail inviata ad un server PEC prima di continuare la procedura di parsing si verifica
            # se è abilitata la configurazione sul server che permette di fare il fetch di una mail su un server PEC
            if x_trasporto == "errore" and not server.mail_client_fetch_emails_from_server_pec:
                raise Exception(_("Cannot fetch email from server PEC! Enable the relative configuration."))
            msg_dict.update(daticert_dict)
            if x_trasporto == "errore":
                msg_dict["pec_type"] = "errore"
            # si sovrascrivono gli attachment della mail per mostrare solo quelli contenuti nel postacert.eml mentre gli
            # allegati della busta di trasporto vengono inseriti nel campo original_attachment_ids e mostrati a parte in
            # vista
            msg_dict["original_attachments"] = original_attachments
            msg_dict["attachments"] = postacert_dict["attachments"]
            # si sovrascrive la email_from della mail per mostrare quella del postacert.eml mentre quello della busta di
            # trasporto viene inserito nel campo original_email_from e mostrato a parte in vista
            msg_dict["original_email_from"] = msg_dict["email_from"]
            msg_dict["email_from"] = postacert_dict["email_from"]
            # si sovrascrive il subject della mail per mostrare quello del postacert.eml mentre quello della busta di
            # trasporto viene inserito nel campo original_subject e mostrato a parte in vista
            msg_dict["original_subject"] = msg_dict["subject"]
            msg_dict["subject"] = postacert_dict.get("subject", "")
            # si sovrascrive il body della mail per mostrare quello del postacert.eml mentre quello della busta di
            # trasporto viene inserito nel campo original_body e mostrato a parte in vista
            msg_dict["original_body"] = msg_dict["body"]
            msg_dict["body"] = postacert_dict["body"]
            msg_dict["body_html"] = postacert_dict["body"]
            return msg_dict
        # caso di una PEC con tipologia non-accettazione
        if x_ricevuta in ["non-accettazione"]:
            daticert_dict["err_type"] = "no-dest"
        # caso di una PEC con tipologia avvenuta-consegna
        if x_ricevuta in ["avvenuta-consegna"]:
            # nel caso di un PEC di tipologia avvenuta-consegna fra gli allegati è presente anche il postacert.eml, il
            # quale viene parsato con l'algoritmo di Odoo andando ad inserire fra gli allegati della ricevuta di
            # consegna anche gli allegati del messaggio originale: per evitare questo si inseriscono solo gli allegati
            # reali, cioè il postacert.eml, daticert.xml e smime.p7s
            msg_dict["attachments"] = original_attachments
        msg_dict.update(daticert_dict)
        msg_dict["pec_type"] = x_ricevuta
        x_riferimento_messaggio_id = pec_headers.get("X-Riferimento-Message-ID", False)
        if not x_riferimento_messaggio_id:
            return msg_dict
        mail_list = self.env["mail.mail"].sudo().search([
            ("message_id", "=", x_riferimento_messaggio_id),
            ("direction", "=", "out")
        ])
        _logger.info("Found %s mail/s with Message ID: %s" % (len(mail_list), x_riferimento_messaggio_id))
        if len(mail_list) > 1:
            raise Exception(_("Too many existing mails with message_id %s") % x_riferimento_messaggio_id)
        elif len(mail_list) == 1:
            mail_parent = mail_list[0]
            msg_dict["pec_mail_parent_id"] = mail_parent.id
            _logger.info("Reconnection to mail with id %s" % mail_parent.id)
        return msg_dict


    @api.model
    def _get_message_pec_headers(self, message, msg_dict):
        pec_headers = {}
        try:
            for header in message._headers:
                if not (header[0] in ["X-Trasporto", "X-Ricevuta", "X-Riferimento-Message-ID"]):
                    continue
                pec_headers[header[0]] = header[1]
        except Exception:
            _logger.warning("Failed to parse PEC headers in message-id %r", msg_dict.get("message_id", False))
        return pec_headers


    @api.model
    def _get_message_pec_attachments(self, msg_dict):
        daticert = None
        postacert = None
        original_attachments = []
        for attachment_data in msg_dict["attachments"]:
            if attachment_data[0] == "daticert.xml":
                daticert = attachment_data[1]
                original_attachments.append(attachment_data)
            elif attachment_data[0] == "postacert.eml":
                postacert = attachment_data[1]
                original_attachments.append(attachment_data)
            elif attachment_data[0] == "smime.p7s":
                original_attachments.append(attachment_data)
        return daticert, postacert, original_attachments


    @api.model
    def message_process_for_mail_client(self, model, message, custom_values=None, save_original=False, strip_attachments=False, thread_id=None, server=None):
        message = super(MailThread, self).message_process_for_mail_client(model, message, custom_values, save_original, strip_attachments, thread_id, server)
        # se il message è False allora è stato scartato dal sistema
        if not message:
            return message
        pec_mail_parent = message.pec_mail_parent_id
        # se il message non ha pec_mail_parent allora non si tratta di una mail di notifica PEC
        if not pec_mail_parent:
            return message
        # si ricostruisce la lista dei destinatari
        email_to_list = pec_mail_parent.email_to.split(",") if pec_mail_parent.email_to else []
        email_cc_list = pec_mail_parent.email_cc.split(",") if pec_mail_parent.email_cc else []

        # ulteriore split della mail in caso ci sia un valore di questo tipo 'testpec@example.com' <testpec@example.com>
        only_email_to_list = []
        for email_to in email_to_list:
            email_splitted = email_to.split()
            if len(email_splitted) > 1:
                only_email_to_list.append(email_splitted[1][1:-1])  # [1:-1] rimozione '<' '>' nella mail
            else:
                only_email_to_list.append(email_splitted[0])
        email_to_list = only_email_to_list

        only_email_cc_list = []
        for email_cc in email_cc_list:
            email_splitted = email_cc.split()
            if len(email_splitted) > 1:
                only_email_to_list.append(email_splitted[1][1:-1])  # [1:-1] rimozione '<' '>' nella mail
            else:
                only_email_to_list.append(email_splitted[0])
        email_cc_list = only_email_cc_list

        email_list = list(set(email_to_list + email_cc_list))
        email_list = [email.strip().lower() for email in email_list]
        failure = False
        failure_reason = ""
        # si itera su tutte le notifiche associate alla mail PEC per verificare che le notifiche di avvenuta consegna
        # siano state ricevute per tutti i destinatari
        for pec_mail_child in pec_mail_parent.pec_mail_child_ids:
            recipient_addr = pec_mail_child.recipient_addr
            recipient_addr = recipient_addr.strip().lower() if recipient_addr else recipient_addr
            if pec_mail_child.pec_type == "avvenuta-consegna" and recipient_addr in email_list:
                email_list.remove(recipient_addr)
            elif pec_mail_child.pec_type != "accettazione":
                failure = True
                if pec_mail_child.failure_reason:
                    failure_reason = failure_reason + "\n\n" + pec_mail_child.failure_reason if failure_reason else pec_mail_child.failure_reason
        # se non c'è nessuna notifica di errore ma la PEC non è stata ricevuta ancora da tutti i destinatari
        # (email_list contenente ancora degli indirizzi), allora lo stato della mail PEC diventa accepted
        if not failure and email_list:
           pec_mail_parent.state = "accepted"
        # se non c'è nessuna notifica di errore e la PEC è stata ricevuta ancora da i destinatari (email_list vuota)
        # allora lo stato della mail PEC diventa received
        elif not failure and not email_list:
           pec_mail_parent.state = "received"
       # in qualsiasi altro caso lo stato della mail PEC diventa exception
        else:
           pec_mail_parent.state = "exception"
           pec_mail_parent.failure_reason = failure_reason
        return message


    @api.model
    def parse_daticert(self, daticert):
        msg_dict = {}
        root = ET.fromstring(daticert)
        cert_giorno = None
        cert_ora = None
        if "tipo" in root.attrib:
            msg_dict["pec_type"] = root.attrib["tipo"]
        if "errore" in root.attrib:
            msg_dict["err_type"] = root.attrib["errore"]
        for child in root:
            if child.tag == "intestazione":
                for child2 in child:
                    if child2.tag == "mittente":
                        msg_dict["email_from"] = child2.text
            if child.tag == "dati":
                for child2 in child:
                    if child2.tag == "identificativo":
                        msg_dict["message_id"] = child2.text
                    if child2.tag == "msgid":
                        msg_dict["pec_msg_id"] = child2.text
                    if child2.tag == "data":
                        if child2.attrib["zona"]:
                            cert_zona = child2.attrib["zona"]
                        for child3 in child2:
                            if child3.tag == "giorno":
                                cert_giorno = child3.text
                            if child3.tag == "ora":
                                cert_ora = child3.text
                    if child2.tag == "consegna":
                        msg_dict["recipient_addr"] = child2.text
                    if child2.tag == "errore-esteso":
                        msg_dict["failure_reason"] = child2.text
        if cert_giorno and cert_ora:
            date_obj = datetime.strptime(cert_giorno + " " + cert_ora, "%d/%m/%Y %H:%M:%S")
            date_obj_loc = date_obj - timedelta(hours=int(cert_zona[2:3]))
            msg_dict["cert_datetime"] = date_obj_loc
        return msg_dict

    @api.model
    def parse_daticert_recipients(self, daticert):
        msg_dict = {}
        root = ET.fromstring(daticert)
        for child in root:
            if child.tag == "intestazione":
                for child2 in child:
                    if child2.tag == "destinatari":
                        if "transmission_type" in msg_dict and msg_dict["transmission_type"]:
                            msg_dict["transmission_type"].update({
                                child2.text: child2.attrib["tipo"]
                            })
                        else:
                            msg_dict["transmission_type"] = {
                                child2.text: child2.attrib["tipo"]
                            }
        return msg_dict


    @api.model
    def decode(self, text):
        """Returns unicode() string conversion of the the given encoded smtp header text"""
        if text:
            text = decode_header(text.replace("\r", ""))
            # The joining space will not be needed as of Python 3.3
            # See https://hg.python.org/cpython/rev/8c03fe231877
            return " ".join([tools.ustr(x[0], x[1]) for x in text])