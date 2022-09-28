import base64

from odoo import models


class ProtocolloInvio(models.Model):
    _inherit = "sd.protocollo.invio"

    def _check_for_attachment(self, protocollo_id, mezzo_trasmissione):
        attachment_ids = super(ProtocolloInvio, self)._check_for_attachment(protocollo_id, mezzo_trasmissione)
        attachment_segnatura_xml = self._get_attachment_from_segnatura_xml(protocollo_id, mezzo_trasmissione.id)
        if attachment_segnatura_xml:
            attachment_ids.append(attachment_segnatura_xml)
        return attachment_ids

    def _get_attachment_from_segnatura_xml(self, protocollo_id, mezzo_trasmissione_id):
        config_obj = self.env["ir.config_parameter"].sudo()
        protocollo = self.env["sd.protocollo.protocollo"].browse(protocollo_id)
        mezzo_trasmissione = self.env["sd.protocollo.mezzo.trasmissione"].browse(mezzo_trasmissione_id)
        attachment_obj = self.env["ir.attachment"]

        pec_param = config_obj.get_param("sd_protocollo.segnatura_xml_invia_pec", False)
        email_param = config_obj.get_param("sd_protocollo.segnatura_xml_invia_email", False)
        segnatura_xml = protocollo.segnatura_xml
        # Se è presente la segnatura e il parametro per inviare la segnatura è attivo creo l'attachment
        if segnatura_xml and (pec_param and mezzo_trasmissione.integrazione == "pec") or (
                email_param and mezzo_trasmissione.integrazione == "peo"):
            content = base64.b64encode(segnatura_xml.encode())
            return attachment_obj.create({
                "name": "Segnatura.xml",
                "datas": content,
                "store_fname": "Segnatura.xml"
            }).id
        return False

    def _update_segnatura_xml_before_invio(self, protocollo_id, account_ids, invio_precedente_ids):
        protocollo = self.env["sd.protocollo.protocollo"].browse(protocollo_id)
        mail_client_obj = self.env["fl.mail.client.account"]
        if len(account_ids) == 1:
            account = mail_client_obj.browse(account_ids[0])
            mail_list = []
            for invio in protocollo.invio_ids:
                # scarto se presente l'invio precedente e verifico che l'invio non abbia un invio successivo
                if invio_precedente_ids and invio.id not in invio_precedente_ids or not invio_precedente_ids:
                    if not invio.invio_successivo_ids:
                        mail_list.append(invio.messaggio_id.email_from)
            mail_list.append(account.email)
        else:
            mail_list = []
            for mail_id in account_ids:
                mail_list.append(mail_client_obj.browse(mail_id).email)
        protocollo.aggiorna_segnatura_xml(mail_list)

    # Invio misto: aggiornamento della segnatura prima che vengano creati gli invii
    def _crea_invii(self, mezzi_gestiti_dict):
        mail_client_obj = self.env["fl.mail.client.account"]
        mail_list = []
        protocollo_id = False
        for mezzo_trasmissione_id in mezzi_gestiti_dict.keys():
            arguments = mezzi_gestiti_dict[mezzo_trasmissione_id]
            protocollo_id = arguments["protocollo_id"]
            if "account_id" in arguments:
                account = mail_client_obj.browse(arguments["account_id"])
                if account.pec and mail_list:
                    temp = mail_list[0]
                    mail_list[0] = arguments["account_id"]
                    mail_list[1] = temp
                else:
                    mail_list.append(arguments["account_id"])

        self._update_segnatura_xml_before_invio(protocollo_id, mail_list, False)

        return super(ProtocolloInvio, self)._crea_invii(mezzi_gestiti_dict)
