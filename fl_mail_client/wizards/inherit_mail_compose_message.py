import logging

from odoo import api, fields, models, tools, _


_logger = logging.getLogger(__name__)

SELECTION_MESSAGE_TYPE_ADD = [
    ("email", "Email")
]


class MailComposeMessage(models.TransientModel):

    _inherit = "mail.compose.message"

    account_id = fields.Many2one(
        "fl.mail.client.account",
        string="From",
        domain="[('use_outgoing_server', '=', True)]"
    )

    message_type = fields.Selection(
        selection_add=SELECTION_MESSAGE_TYPE_ADD,
        ondelete={"email": "cascade"}
    )

    email_ids = fields.Many2many(
        "fl.mail.client.contact",
        "mail_compose_message_contact_rel",
        "wizard_id",
        "contact_id",
        string="To"
    )

    email_cc_ids = fields.Many2many(
        "fl.mail.client.contact",
        "mail_compose_message_contact_cc_rel",
        "wizard_id",
        "contact_id",
        string="Cc"
    )

    email_bcc_ids = fields.Many2many(
        "fl.mail.client.contact",
        "mail_compose_message_contact_bcc_rel",
        "wizard_id",
        "contact_id",
        string="Bcc"
    )

    @api.model
    def default_get(self, fields):
        result = super(MailComposeMessage, self).default_get(fields)
        if self._context.get("mail_compose_message", False):
            result["model"] = "mail.thread"
            result["message_type"] = "email"
            result["subtype_id"] = False
        return result

    @api.onchange('account_id')
    def _onchange_account_id(self):
        if self.account_id:
            self.mail_server_id = self.account_id.ir_mail_server_id.id

    def get_mail_values(self, res_ids):
        results = super(MailComposeMessage, self).get_mail_values(res_ids)
        if self._context.get("mail_compose_message", False):
            for res_id in res_ids:
                results[res_id]["account_id"] = self.account_id.id
                results[res_id]["notification"] = False
                results[res_id]["direction"] = "out"
                results[res_id]["email_from"] = tools.formataddr((self.account_id.description, self.account_id.email))
                results[res_id]["reply_to"] = tools.formataddr((self.account_id.description, self.account_id.email))
                # valorizzazione del campo partner_ids, anche se non viene usato, per evitare che dia errore in validazione
                results[res_id]["partner_ids"] = [contact.partner_id.id for contact in self.email_ids]
                results[res_id]["state"] = "outgoing"
        return results

    def send_mail(self, auto_commit=False):
        context = dict(self._context or {})
        # i campi email_to, email_cc, email_bcc non possono essere inseriti nel metodo get_mail_values perché tale
        # metodo viene usato solamente per recuperare i valori dei campi del modello mail.message, mentre i campi
        # email_to, email_cc, email_bcc sono contenuti nel modello mail.mail. Per aggirare il problema passiamo tali
        # valori tramite context e li recuperiamo nel metodo create del modello mail.mail, inserendoli all'interno del
        # dizionario dei values
        if self._context.get("mail_compose_message", False):
            if self.email_ids:
                context["mail_compose_message_email_to"] = ",".join([contact.email for contact in self.email_ids])
            if self.email_cc_ids:
                context["mail_compose_message_email_cc"] = ",".join([contact.email for contact in self.email_cc_ids])
            if self.email_bcc_ids:
                context["mail_compose_message_email_bcc"] = ",".join([contact.email for contact in self.email_bcc_ids])
            #`inseriamo nel context anche il valore mail_auto_delete a False in maniera tale che le mail inviate tramite
            # il wizard di mail compose non siano eliminate dopo l'invio. Infatti odoo di default elimina tali mail per
            # evitare che ci sia un carico indesiderato/imprevisto sul DB
            context["mail_auto_delete"] = False
            context["mail_notify_force_send"] = False
            context["mail_notify_author"] = True
        return super(MailComposeMessage, self.with_context(context)).send_mail(auto_commit)