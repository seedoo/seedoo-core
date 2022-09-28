from odoo import models, fields, api, tools, _
from odoo.exceptions import ValidationError

SELECTION_MODALITA_INVIO = [
    ("broadcast", "Broadcast")
]


class WizardProtocolloInvioMail(models.TransientModel):
    _name = "sd.protocollo.wizard.protocollo.invio.mail"
    _description = "Invio Mail"

    pec = fields.Boolean(
        string="PEC",
        readonly=True
    )

    modalita_invio = fields.Selection(
        string="Modalità Invio",
        selection=SELECTION_MODALITA_INVIO,
        default=SELECTION_MODALITA_INVIO[0][0],
        required=True
    )

    account_id = fields.Many2one(
        string="Da",
        comodel_name="fl.mail.client.account",
        domain="[('use_outgoing_server', '=', True),('pec', '=', pec)]",
        required=True,
        default=False
    )

    account_id_name = fields.Char(
        string="Da",
        readonly=True
    )

    destinatari = fields.Text(
        string="A",
        required=True,
        readonly=True
    )

    oggetto = fields.Char(
        string="Oggetto",
        required=True,
        default=False
    )

    body = fields.Html(
        string="Body",
        default=False
    )

    document_ids = fields.Many2many(
        string="Documenti",
        comodel_name="sd.dms.document",
        relation="sd_protocollo_wizard_protocollo_invio_mail_document_rel",
        column1="wizard_id",
        column2="document_id",
        readonly=True
    )

    template_id = fields.Many2one(
        string="Use template",
        comodel_name="mail.template",
        domain="[('model', '=', 'mail.thread'), ('create_uid', '=', uid)]"
    )

    modalita_invio_invisible = fields.Boolean(
        string="Modalità Invio Invisible"
    )

    body_invisible = fields.Boolean(
        string="Body Invisible"
    )

    template_id_invisible = fields.Boolean(
        string="Template invisible"
    )

    @api.model
    def get_oggetto(self, protocollo):
        oggetto = protocollo.documento_id_oggetto
        config_obj = self.env["ir.config_parameter"].sudo()
        rinomina_oggetto_mail_pec = bool(config_obj.get_param("sd_protocollo.rinomina_oggetto_mail_pec"))
        if not rinomina_oggetto_mail_pec:
            return oggetto
        oggetto = "Prot. n. %s del %s - %s" % (
            protocollo.numero_protocollo,
            self.env["fl.utility.dt"].utc_to_local(protocollo.data_registrazione).strftime("%d-%m-%Y %H:%M:%S"),
            protocollo.documento_id_oggetto
        )
        return oggetto

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        document_obj = self.env["sd.dms.document"]
        protocollo_obj = self.env["sd.protocollo.protocollo"]
        protocollo_id = self.env.context.get("protocollo_id", False)
        protocollo = protocollo_obj.browse(protocollo_id)
        res["pec"] = False
        if protocollo.mezzo_trasmissione_id.integrazione == "pec":
            res["pec"] = True
        contact_list = []
        for contact in protocollo.destinatario_ids:
            contact_list = contact_list + contact.get_email_list()
        document_data_list = document_obj.search_read([
            ("protocollo_id", "=", protocollo_id)
        ], ["id"])
        document_ids = [document_data["id"] for document_data in document_data_list]
        module_fl_mail_client_template = self.env["ir.module.module"].sudo().search([
            ("name", "=", "fl_mail_client_template"),
            ("state", "=", "installed")
        ], limit=1)
        res["account_id"] = protocollo.account_id.id if protocollo.account_id else False
        res["account_id_name"] = protocollo.account_id.with_context(display_with_email=True).name if protocollo.account_id else False
        res["oggetto"] = self.get_oggetto(protocollo)
        res["destinatari"] = ", ".join(contact_list)
        res["document_ids"] = [(6, 0, document_ids)]
        res["modalita_invio_invisible"] = True if len(self._fields['modalita_invio'].selection) == 1 else False
        res["body_invisible"] = self._get_body_visibility(res["pec"])
        res["template_id_invisible"] = False if module_fl_mail_client_template else True
        return res

    def _get_body_visibility(self, pec):
        config_obj = self.env["ir.config_parameter"].sudo()
        if pec:
            return not bool(config_obj.get_param("sd_protocollo.inserisci_testo_pec"))
        return True

    @api.onchange("oggetto")
    def _onchange_oggetto(self):
        config_obj = self.env["ir.config_parameter"].sudo()
        max_length_pec = int(config_obj.get_param("sd_protocollo.lunghezza_massima_oggetto_pec"))
        max_length_email = int(config_obj.get_param("sd_protocollo.lunghezza_massima_oggetto_mail"))
        lunghezza_oggetto = len(self.oggetto)
        if (self.pec and lunghezza_oggetto > max_length_pec) or (not self.pec and lunghezza_oggetto > max_length_email):
            raise ValidationError(_("Lunghezza massima dell'oggetto superata"))

    @api.onchange("template_id")
    def _onchange_template_id(self):
        if not self.template_id:
            return {}
        fields = ["subject", "body_html"]
        template_values = self.template_id.generate_email(False, fields)
        values = {
            "oggetto": template_values.get("subject", False),
            "body": template_values.get("body_html", False),
        }
        return {"value": values}

    def crea_invii(self):
        invio_obj = self.env["sd.protocollo.invio"]
        protocollo_obj = self.env["sd.protocollo.protocollo"]
        protocollo_id = self.env.context.get("protocollo_id", False)
        protocollo = protocollo_obj.browse(protocollo_id)
        destinatario_vals_list = []
        for contact in protocollo.destinatario_ids:
            for email_dict in contact.get_email_list(with_type=True):
                destinatario_vals_list.append({
                    "contatto_id": contact.id,
                    "email": email_dict["email"],
                    "email_tipologia": email_dict["type"]
                })
        invio_obj.crea_invio_mail(
            protocollo.id,
            protocollo.mezzo_trasmissione_id.id,
            destinatario_vals_list,
            self.modalita_invio,
            self.account_id.id,
            self.oggetto,
            self.body
        )

    def save_as_template(self):
        """ hit save as template button: current form value will be a new template attached to the current document. """
        self.ensure_one()
        model = self.env["ir.model"]._get("mail.thread")
        model_name = model.name or ''
        template_name = "%s: %s" % (model_name, tools.ustr(self.oggetto))
        values = {
            "name": template_name,
            "subject": self.oggetto or False,
            "body_html": self.body or False,
            "model_id": model.id or False,
            "auto_delete": False
        }
        template = self.env["mail.template"].create(values)
        # generate the saved template
        self.write({'template_id': template.id})
        #record.onchange_template_id_wrapper()
        context = dict(self.env.context or {})
        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_id": self.id,
            "res_model": self._name,
            "target": "new",
            "context": context,
        }