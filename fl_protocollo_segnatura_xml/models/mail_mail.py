import base64
from odoo.exceptions import ValidationError
from odoo import models,_


class Mail(models.Model):
    _inherit = "mail.mail"
    def _get_protocollo_vals(self, vals, folder_id, mezzo_trasmissione_id, archivio_id):
        vals = super(Mail, self)._get_protocollo_vals(vals, folder_id, mezzo_trasmissione_id, archivio_id)
        config_obj = self.env["ir.config_parameter"].sudo()
        protocollo_obj = self.env["sd.protocollo.protocollo"]

        # se la mail è una PEC ed è abilitata la configurazione per il parsing del file segnatura.xml allora si recupera
        # il relativo allegato della mail con nome segnatura.xml e si effettua il parsing del content
        parsed_data = {}
        segnatura_xml_parse = config_obj.get_param("sd_protocollo.segnatura_xml_parse")
        if self.pec and segnatura_xml_parse:
            for attachment in self.attachment_ids:
                if attachment.name.lower() == "segnatura.xml" and attachment.datas:
                    content = base64.b64decode(attachment.datas)
                    parsed_data = protocollo_obj.parse_segnatura_xml_to_protocollo_data(content,self.email_from)
                    break
        # la valorizzazione degli ulteriori campi del protocollo viene fatta se sono presenti dati parsati (vuol dire
        # è stato effettuato il parsing del file segnatura.xml)
        if parsed_data:
            vals["mittente_registro"] = parsed_data["mittente_registro"]
            vals["mittente_numero_protocollo"] = parsed_data["mittente_numero_protocollo"]
            vals["mittente_data_registrazione"] = parsed_data["mittente_data_registrazione"]
        # se ci sono dati parsati ed è abilitata la configurazione per il parsing dei dati del mittente allora i dati
        # del mittente del protocollo vengono recuperati dai dati parsati dalla segnatura.xml
        sender_parse = self.env["ir.config_parameter"].sudo().get_param("sd_protocollo.sender_segnatura_xml_parse")
        if "mittente" in parsed_data and parsed_data["mittente"] and sender_parse:
            # recuperare vals primo elemento del mittente
            mittente_vals = vals["mittente_ids"][0][2]
            if mittente_vals.get("pec_mail", False):
                parsed_data["mittente"]["pec_mail"] = mittente_vals["pec_mail"]
            vals["mittente_ids"][0][2].update(parsed_data["mittente"])
        return vals

    def protocollo_crea_da_mail(self, vals, folder_id, documento_tipologia, documento_attachment_id=False,storico=True):
        protocollo = super(Mail, self).protocollo_crea_da_mail(vals, folder_id, documento_tipologia,
                                                               documento_attachment_id=documento_attachment_id, storico=storico)
        config_obj = self.env["ir.config_parameter"].sudo()
        protocollo_obj = self.env["sd.protocollo.protocollo"]
        # se la mail è una PEC ed è abilitata la configurazione per il parsing del file segnatura.xml allora si recupera
        # il relativo allegato della mail con nome segnatura.xml e si effettua il parsing del content
        parsed_data = {}
        exceptions=[]
        segnatura_xml_parse = config_obj.get_param("sd_protocollo.segnatura_xml_parse")
        if self.pec and segnatura_xml_parse:
            for attachment in self.attachment_ids:
                if attachment.name.lower() == "segnatura.xml" and attachment.datas:
                    content = base64.b64decode(attachment.datas)
                    #controllo se la segnatura contiene errori
                    exceptions = protocollo_obj.validate_segnatura(content, self.attachment_ids - attachment, protocollo['res_id'])
                    break

        if len(exceptions) > 0:
            #se la segnatura contiene errori e l'utente ha abilitato la validazione della segnatura allora diventerà
            #non protocollabile se invece se la validazione non è abilitata e la segnatura contiene errori verranno
            #aggiunti dei messaggi di errore nello storico
            if config_obj.get_param("sd_protocollo.valida_segnatura_xml_ingresso"):
                self.write({
                    "protocollo_action": "non_protocollabile",
                    "protocollo_id": None,

                })
                html_errors = self._get_html_segnatura_exceptions(exceptions)
                protocollo_obj.sudo().browse(protocollo['res_id']).unlink()
                self.env.user._request_notify_message("danger", "Protocol draft creation", html_errors)
                self.storico_crea_eccezione_da_mail(exceptions)
                return {'type': 'ir.actions.act_window_close'}
            else:
                self.storico_crea_protocollo_da_mail(protocollo_obj.browse(protocollo['res_id']).numero_protocollo)
                protocollo_obj.browse(protocollo['res_id']).storico_create_errors_from_mail(exceptions)
        return protocollo


    def _get_html_segnatura_exceptions(self, exceptions):
        error_message_start = '<div><b><p>'
        error_message_start += _(
            "The following errors were found in the segnatura.xml:") + '</p></b><ul>'
        error_message_end = '</ul></div>'
        error_message = ''
        for error in exceptions:
            error_message += '<li>' + error + '</li>'
        return error_message_start + error_message + error_message_end
