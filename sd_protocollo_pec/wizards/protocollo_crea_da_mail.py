from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)

SELECTION_DOCUMENTO_TIPOLOGIA = [
    ("sd_protocollo.select_body_%s", ("testo", "Corpo del messaggio")),
    ("sd_protocollo.select_eml_%s", ("eml", "Intero messaggio (file EML)")),
    ("sd_protocollo.select_postacert_eml_%s", ("postacert", "Postacert.eml")),
    ("sd_protocollo.select_attachments_%s", ("allegato", "Allegato del messaggio")),
]


class ProtocolloCreaDaMail(models.TransientModel):
    _name = "sd.protocollo.wizard.protocollo.crea.da.mail"
    _description = "Wizard Crea da Mail"

    def get_documento_tipologia_options(self):
        options = []
        config_obj = self.env["ir.config_parameter"].sudo()
        mail = self.env["mail.mail"].browse(self.env.context.get("mail_id"))
        if not mail:
            return options

        for tipologia in SELECTION_DOCUMENTO_TIPOLOGIA:
            if config_obj.get_param(tipologia[0] % self._get_mail_type(mail.pec)):
                # In caso il fetchmail non abbia la spunta su conserva originale, "Intero messaggio (file EML)" non
                # deve essere mostrato, perchè original_eml non viene salvato.
                if tipologia[1][0] == "eml" and (not mail.fetchmail_server_id.original or not mail.original_eml):
                    continue
                options.append(tipologia[1])
        return options

    def _get_mail_type(self, pec):
        if pec:
            return "pec"
        return ""

    company_id = fields.Many2one(
        string="Azienda",
        comodel_name="res.company",
        required=False,
        default=False
    )

    company_id_invisible = fields.Boolean(
        string="Company Invisible"
    )

    protocollatore_ufficio_id = fields.Many2one(
        string="Ufficio protocollatore",
        comodel_name="fl.set.set",
        domain="[('can_used_to_protocol', '=', True)]",
        required=False,
        default=False
    )

    protocollatore_ufficio_id_invisible = fields.Boolean(
        string="Protocollatore Ufficio Invisible"
    )

    registro_id = fields.Many2one(
        string="Registro",
        comodel_name="sd.protocollo.registro",
        domain="[('can_used_to_protocol', '=', True)]",
        required=False,
        default=False
    )

    registro_id_invisible = fields.Boolean(
        string="Registro Invisible",
        default=True
    )

    documento_tipologia = fields.Selection(
        string="Documento Principale",
        selection=get_documento_tipologia_options,
        required=True,
        default=False
    )

    documento_attachment_id = fields.Many2one(
        string="Allegato del messaggio",
        comodel_name="ir.attachment",
        default=False
    )

    mail_message_id = fields.Many2one(
        string="Messaggio Associato alla Mail",
        comodel_name="mail.message"
    )

    folder_id = fields.Many2one(
        string="Cartella",
        comodel_name="sd.dms.folder",
        domain="[('company_id', '=', company_id),('perm_create', '=', True)]",
        required=False,
        default=False
    )

    folder_id_invisible = fields.Boolean(
        string="Cartella Invisible",
        default=True
    )

    riservato = fields.Boolean(
        string="Riservato"
    )

    @api.model
    def default_get(self, fields):
        result = super(ProtocolloCreaDaMail, self).default_get(fields)
        protocollo_obj = self.env["sd.protocollo.protocollo"]
        mail_obj = self.env["mail.mail"]
        mail = mail_obj.browse(self.env.context.get("mail_id"))
        if not mail:
            return result
        result["mail_message_id"] = mail.mail_message_id.id
        result["company_id"] = protocollo_obj._default_company_id()
        result["company_id_invisible"] = protocollo_obj._default_company_id_readonly()
        return result

    @api.onchange("company_id")
    def onchange_company_id(self):
        context = dict(
            self.env.context,
            company_id=self.company_id.id
        )
        self = self.with_context(context)
        default_protocollatore_ufficio_id = self.env["sd.protocollo.protocollo"]._default_protocollatore_ufficio_id()
        if default_protocollatore_ufficio_id:
            self.protocollatore_ufficio_id = default_protocollatore_ufficio_id
            self.protocollatore_ufficio_id_invisible = True
        else:
            self.protocollatore_ufficio_id = False
            self.protocollatore_ufficio_id_invisible = False

    @api.onchange("protocollatore_ufficio_id")
    def onchange_protocollatore_ufficio_id(self):
        context = dict(
            self.env.context,
            company_id=self.company_id.id
        )
        self = self.with_context(context)
        folder = self.env["sd.protocollo.cartella"].get_folder(self, "protocollo")
        self.folder_id = folder.id if folder else False
        default_registro_id = self.env["sd.protocollo.protocollo"]._default_registro_id()
        if default_registro_id:
            self.registro_id = default_registro_id
            self.registro_id_invisible = True
        else:
            self.registro_id = False
            self.registro_id_invisible = False

    @api.onchange("documento_tipologia")
    def onchange_documento_tipologia(self):
        if self.documento_tipologia:
            self.folder_id_invisible = False
        else:
            self.folder_id_invisible = True

    def get_protocollo_vals(self):
        vals = {
            "company_id": self.company_id.id,
            "protocollatore_ufficio_id": self.protocollatore_ufficio_id.id,
            "registro_id": self.registro_id.id,
            "riservato": self.riservato
        }
        return vals

    def action_crea_bozza_protocollo(self):
        self.ensure_one()
        mail_obj = self.env["mail.mail"]
        # si recupera l'istanza della mail da protocollare
        mail = mail_obj.browse(self.env.context.get("mail_id"))
        documento_attachment_id = False
        if self.documento_tipologia == "allegato":
            documento_attachment_id = self.documento_attachment_id.id
        return mail.protocollo_crea_da_mail(
            self.get_protocollo_vals(),
            self.folder_id.id,
            self.documento_tipologia,
            documento_attachment_id
        )