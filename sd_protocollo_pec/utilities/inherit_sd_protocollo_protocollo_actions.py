from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging
import base64

_logger = logging.getLogger(__name__)


class SdProtocolloProtocolloActions(models.Model):
    _inherit = "sd.protocollo.protocollo"

    @api.model
    def verifica_campi_obbligatori_non_configurati(self):
        error_list = super(SdProtocolloProtocolloActions, self).verifica_campi_obbligatori_non_configurati()
        if self.tipologia_protocollo == "uscita" and self.mezzo_trasmissione_id.integrazione == "pec":
            error_list = self._verifica_campi_obbligatori_non_configurati_destinatari(error_list)
        return error_list

    @api.model
    def _verifica_campi_obbligatori_non_configurati_destinatari(self, error_list):
        for destinatario in self.destinatario_ids:
            if destinatario.is_pa or (destinatario.company_type=="person" and destinatario.parent_person_company_subject_type in ["pa", "gps"]):
                error_list = self._verifica_campi_obbligatori_non_configurati_destinatari_pa(error_list, destinatario)
            else:
                error_list = self._verifica_campi_obbligatori_non_configurati_destinatari_non_pa(error_list, destinatario)
        return error_list

    @api.model
    def _verifica_campi_obbligatori_non_configurati_destinatari_pa(self, error_list, destinatario):
        if destinatario.pec_mail_amm and destinatario.pec_mail_amm_use_in_sending:
            return error_list
        if destinatario.email_amm and destinatario.email_amm_use_in_sending:
            return error_list
        for digital_domicile in destinatario.digital_domicile_ids:
            if digital_domicile.use_in_sending:
                return error_list
        for email_address in destinatario.email_address_ids:
            if email_address.use_in_sending:
                return error_list
        if destinatario.contact_pa_pec_mail and destinatario.contact_pa_pec_mail_use_in_sending:
            return error_list
        if destinatario.contact_pa_email and destinatario.contact_pa_email_use_in_sending:
            return error_list
        error = _("Select at least one e-mail address to be used in sending for the recipient: %s") % destinatario.name
        error_list.append(error)
        return error_list

    @api.model
    def _verifica_campi_obbligatori_non_configurati_destinatari_non_pa(self, error_list, destinatario):
        if not destinatario.pec_mail and not destinatario.email:
            error = _("Insert at least the e-mail or PEC to be used in sending for the recipient: %s") % destinatario.name
            error_list.append(error)
            return error_list
        if not destinatario.pec_mail_use_in_sending and not destinatario.email_use_in_sending:
            error = _("Select at least the e-mail or PEC to be used in sending for the recipient: %s") % destinatario.name
            error_list.append(error)
            return error_list
        if destinatario.pec_mail_use_in_sending and not destinatario.pec_mail:
            error = _("Insert PEC to be used in sending for the recipient: %s") % destinatario.name
            error_list.append(error)
        if destinatario.email_use_in_sending and not destinatario.email:
            error = _("Insert e-mail to be used in sending for the recipient: %s") % destinatario.name
            error_list.append(error)
        return error_list

    def protocollo_lista_source_action(self):
        result = super(SdProtocolloProtocolloActions, self).protocollo_lista_source_action()
        if result or not self.mail_id:
            return result
        context = dict(
            self.env.context
        )
        action = self.env.ref("fl_mail_client.action_mail_mail_list_received").read()[0]
        action.update({
            "display_name": _("Mail"),
            "view_mode": "form",
            "view_type": "form",
            "views": [(action["views"][1][0], "form")],
            "res_id": self.mail_id.id
        })
        return action

    def protocollo_registra_actions(self):
        res = super().protocollo_registra_actions()
        if self.mail_id:
            self.mail_id.protocollo_action = "protocollata"
            self.mail_id.storico_mail_protocollo_action_protocollata(self.numero_protocollo)
        return res

    def protocollo_elimina_bozza_action(self):
        self.ensure_one()
        if not self.button_elimina_bozza_invisible and self.mail_id:
            self.mail_id.protocollo_action = "mail_da_protocollare"
            self.mail_id.storico_protocollo_eliminato(self.numero_protocollo)
        return super(SdProtocolloProtocolloActions, self).protocollo_elimina_bozza_action()