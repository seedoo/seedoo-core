from odoo import fields, models, api, _


class WizardProtocolloRegistra(models.TransientModel):
    _name = "sd.protocollo.wizard.protocollo.registra"
    _description = "Wizard Protocollo Registra"

    mittente = fields.Text(
        string="Mittente",
        readonly=True
    )

    destinatari = fields.Text(
        string="Destinatari",
        readonly=True
    )

    assegnatari_competenza = fields.Text(
        string="Assegnatari competenza",
        readonly=True
    )

    assegnatari_conoscenza = fields.Text(
        string="Assegnatari conoscenza",
        readonly=True
    )

    data_ricezione = fields.Datetime(
        string="Data ricezione",
        readonly=True
    )

    @api.model
    def default_get(self, fields):
        res = super(WizardProtocolloRegistra, self).default_get(fields)

        protocollo_obj = self.env["sd.protocollo.protocollo"]
        protocollo = protocollo_obj.browse(self.env.context.get("protocollo_id"))

        separator = "\n"
        mittente_list = [mittente.name for mittente in protocollo.mittente_ids]
        if protocollo.mittente_interno_id:
            mittente_list.append(protocollo.mittente_interno_id.nome)
        destinataro_list = [destinataro.name for destinataro in protocollo.destinatario_ids]
        assegna_comp_list = [assegnazione.assegnatario_nome for assegnazione in protocollo.assegnazione_competenza_ids]
        assegna_con_list = [assegnazione.assegnatario_nome for assegnazione in protocollo.assegnazione_conoscenza_ids]

        res["mittente"] = separator.join(mittente_list) if mittente_list else False
        res["destinatari"] = separator.join(destinataro_list) if destinataro_list else False
        res["assegnatari_competenza"] = separator.join(assegna_comp_list) if assegna_comp_list else False
        res["assegnatari_conoscenza"] = separator.join(assegna_con_list) if assegna_con_list else False
        res["data_ricezione"] = protocollo.data_ricezione
        return res

    def action_confirm(self):
        protocollo_id = self.env.context.get("protocollo_id")
        errors = self.env["sd.protocollo.protocollo"].browse(protocollo_id).registra()
        protocollo = self.env["sd.protocollo.protocollo"].browse(protocollo_id)
        success_message_list = self._get_success_message_list(protocollo, errors)
        success_message = self._get_html_message(success_message_list)
        if success_message:
            self.env.user._request_notify_message("success", "Esito Registrazione", success_message)
        error_message_list = self._get_error_message_list(protocollo, errors)
        error_message = self._get_html_message(error_message_list)
        if error_message:
            self.env.user._request_notify_message("danger", "Attenzione!", error_message)

    def _get_success_message_list(self, protocollo, errors):
        message_list = []
        settings_timezone = self.env["ir.config_parameter"].sudo().get_param("sd_protocollo.timezone")
        user_timezone = self._context.get("tz", False)
        if not user_timezone:
            user_timezone = settings_timezone
        data_registrazione = self.env["fl.utility.dt"].utc_to_local(
            protocollo.data_registrazione, user_timezone
        ).strftime("%d-%m-%Y %H:%M:%S")
        message_list.append("Protocollo %s del %s registrato correttamente" % (
            protocollo.numero_protocollo,
            data_registrazione
        ))
        if not errors.get("segnatura_pdf") and protocollo.documento_id.mimetype == "application/pdf" and\
                protocollo._get_config_inserisci_segnatura_pdf():
            message_list.append("Segnatura PDF generata correttamente")
        return message_list

    def _get_error_message_list(self, protocollo, errors):
        message_list = []
        for error in errors:
            message_list.append(errors[error])
        return message_list

    def _get_html_message(self, message_list):
        if not message_list:
            return ""
        html_message = "<ul>"
        for message in message_list:
            html_message += "<li>%s</li>" % message
        html_message += "</ul>"
        return html_message
