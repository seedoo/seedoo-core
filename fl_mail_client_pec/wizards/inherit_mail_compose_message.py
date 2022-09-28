import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class MailComposeMessage(models.TransientModel):

    _inherit = "mail.compose.message"

    account_pec = fields.Boolean(
        string="PEC",
        default=False
    )

    @api.onchange('account_id')
    def _onchange_account_id(self):
        super(MailComposeMessage, self)._onchange_account_id()
        if self.account_id:
            self.account_pec = self.account_id.pec
            if self.account_id.pec:
                self.email_bcc_ids = False

    def send_mail(self, auto_commit=False):
        context = dict(self._context or {})
        # i campi pec, pec_type non possono essere inseriti nel metodo get_mail_values perché tale metodo viene usato
        # solamente per recuperare i valori dei campi del modello mail.message, mentre i campi pec, pec_type sono
        # contenuti nel modello mail.mail. Per aggirare il problema passiamo tali valori tramite context e li
        # recuperiamo nel metodo create del modello mail.mail, inserendoli all'interno del dizionario dei values
        if self._context.get("mail_compose_message", False):
            if self.account_id and self.account_id.pec:
                context["pec"] = True
                context["pec_type"] = "posta-certificata"
        return super(MailComposeMessage, self.with_context(context)).send_mail(auto_commit)