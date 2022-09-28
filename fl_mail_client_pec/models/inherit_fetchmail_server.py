import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class FetchmailServer(models.Model):
    _inherit = "fetchmail.server"

    mail_client_account_pec = fields.Boolean(
        string="Mail Client Account PEC",
        related="mail_client_account_id.pec",
    )

    mail_client_fetch_emails_from_server_pec = fields.Boolean(
        string="Accept not PEC messages",
        default=False
    )

    def _get_log_output(self, message):
        msg_str = super(FetchmailServer, self)._get_log_output(message)
        if message.pec:
            return msg_str + " - Type '%s' - Message Id '%s'" % (message.pec_type, message.pec_msg_id)
        return msg_str
