from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

SELECTION_MODALITA_INVIO = [
    ("broadcast", "Broadcast")
]


class WizardProtocolloReinvioMail(models.TransientModel):
    _name = "sd.protocollo.wizard.protocollo.reinvio.mail"
    _description = "Reinvio Mail"

    modalita_invio = fields.Selection(
        string="Modalità Invio",
        selection=SELECTION_MODALITA_INVIO,
        default=SELECTION_MODALITA_INVIO[0][0],
        required=True
    )

    modalita_invio_readonly = fields.Boolean(
        string="modalita invio readonly",
        default=False
    )

    contatto_ids = fields.One2many(
        string="Contatti",
        comodel_name="sd.protocollo.wizard.protocollo.reinvio.mail.contatto",
        inverse_name="wizard_id"
    )

    motivazione = fields.Text(
        string="Motivazione",
        required=True
    )

    @api.model
    def default_get(self, fields_list):
        # si recuperano dal context gli id degli invii da reinviare
        invio_ids = self.env.context.get("invio_ids")
        if not invio_ids:
            raise ValidationError(_("There are no ids in context"))
        result = super(WizardProtocolloReinvioMail, self).default_get(fields_list)
        invio_obj = self.env["sd.protocollo.invio"]
        invio_list = invio_obj.browse(invio_ids)
        result["modalita_invio"] = invio_list[0].modalita_invio
        result["modalita_invio_readonly"] = True if len(self._fields["modalita_invio"].selection) == 1 else False
        destinatario_list = []
        for invio in invio_list:
            destinatario_list += invio.get_destinatario_to_resend_list()
        result["contatto_ids"] = self._get_contatto_ids(destinatario_list)
        return result

    def _get_contatto_ids(self, destinatario_list):
        contatto_ids = []
        for destinatario in destinatario_list:
            contatto_ids.append((0, 0, {
                "destinatario_id": destinatario.id,
                "name": destinatario.contatto_id.name,
                "email": destinatario.email
            }))
        return contatto_ids

    def action_crea_invii(self):
        if not self.contatto_ids:
            return
        invio_obj = self.env["sd.protocollo.invio"]
        invio_ids = self.env.context.get("invio_ids")
        invio_list = invio_obj.browse(invio_ids)
        # si prende il primo per recuperare i dati che sono uguali anche negli altri invii
        invio = invio_list[0]
        # si recuperano i dati dei destinatari
        destinatario_vals_list = []
        for contatto in self.contatto_ids:
            destinatario_vals_list.append({
                "email": contatto.email,
                "email_tipologia": contatto.destinatario_id.email_tipologia,
                "contatto_id": contatto.destinatario_id.contatto_id.id,
                "invio_precedente_destinatario_id": contatto.destinatario_id.id
            })
            if contatto.destinatario_id.email != contatto.email:
                invio.protocollo_id.storico_reinvio_modifica_mail(
                    nome=contatto.destinatario_id.contatto_id.name,
                    mail_before=contatto.destinatario_id.email,
                    mail_after=contatto.email,
                    mtype="pec_mail" if invio.mezzo_trasmissione_integrazione == "pec" else "email",
                    motivazione=self.motivazione
                )
        self._crea_invio_mail(destinatario_vals_list, invio)

    def _crea_invio_mail(self, destinatario_vals_list, invio):
        invio_obj = self.env["sd.protocollo.invio"]
        invio_obj.crea_invio_mail(
            invio.protocollo_id.id,
            invio.mezzo_trasmissione_id.id,
            destinatario_vals_list,
            self.modalita_invio or invio.modalita_invio,
            invio.messaggio_id.account_id.id,
            invio.messaggio_id.subject,
            invio.messaggio_id.body_html
        )


class WizardProtocolloReinvioMailContatto(models.TransientModel):
    _name = "sd.protocollo.wizard.protocollo.reinvio.mail.contatto"
    _description = "Reinvio Mail Contatto"
    # questo è un wizards on the fly
    # il readonly dei campi va inserito nella vista, altrimenti al submit del form odoo fa il raise  di un errore riferito
    # alla mancata creazione dei fields required che hanno readonly nel modello

    wizard_id = fields.Many2one(
        string="Wizard",
        comodel_name="sd.protocollo.wizard.protocollo.reinvio.mail",
        readonly=True
    )

    destinatario_id = fields.Many2one(
        string="Destinatario",
        comodel_name="sd.protocollo.invio.destinatario",
        required=True
    )

    name = fields.Char(
        string="Nome",
    )

    email = fields.Char(
        string="Email/Pec",
        required=True
    )
