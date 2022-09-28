# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from odoo.tools import ustr


class IrMailServer(models.Model):

    _inherit = 'ir.mail_server'

    @api.model
    def _default_mail_client(self):
        if self.env.user.has_group('fl_mail_client.group_fl_mail_client_manager'):
            return True
        return False

    mail_client = fields.Boolean(
        string="Mail Client Active",
        default=_default_mail_client
    )

    mail_client_account_ids = fields.One2many(
        "fl.mail.client.account",
        "ir_mail_server_id",
        string="Mail Client Account",
    )

    def send_email(self, message, mail_server_id=None, smtp_server=None, smtp_port=None,
                   smtp_user=None, smtp_password=None, smtp_encryption=None, smtp_debug=False,
                   smtp_session=None):
        """
        Il metodo viene esteso in modo tale da sovrascrivere il Return-Path nel caso in cui la mail sia inviata tramite
        un server in uscita configurato come client mail. Infatti, di default, il Return-Path viene impostato in
        funzione del parametro di configurazione mail.catchall.domain, il quale se settato con un dominio diverso
        rispetto al mittente della mail (smtp user del server), genera un errore in fase di invio.
        """
        if mail_server_id and self.browse(mail_server_id).mail_client:
            if message["Return-Path"]:
                del message["Return-Path"]
            message["Return-Path"] = message["From"]
        return super(IrMailServer, self).send_email(
            message,
            mail_server_id=mail_server_id,
            smtp_server=smtp_server,
            smtp_port=smtp_port,
            smtp_user=smtp_user,
            smtp_password=smtp_password,
            smtp_encryption=smtp_encryption,
            smtp_debug=smtp_debug,
            smtp_session=smtp_session
        )

    # il test connessione smtp viene sovrascritto per impostare l'email del client account nel caso in cui il server sia
    # utilizzato come mail client e associato ad un client account. Se è di tipo mail client ma non è associato a nessun
    # account allora smtp.mail non deve essere effettuato
    def test_smtp_connection(self):
        for server in self:
            smtp = False
            try:
                smtp = self.connect(mail_server_id=server.id)
                # simulate sending an email from current user's address - without sending it!
                email_from, email_to = self.env.user.email, 'noreply@odoo.com'

                if server.mail_client:
                    if server.mail_client_account_ids:
                        email_from = server.mail_client_account_ids[0].email
                    else:
                        continue

                if not email_from:
                    raise UserError(_('Please configure an email on the current user to simulate '
                                      'sending an email message via this outgoing server'))
                # Testing the MAIL FROM step should detect sender filter problems
                (code, repl) = smtp.mail(email_from)
                if code != 250:
                    raise UserError(_('The server refused the sender address (%(email_from)s) '
                                      'with error %(repl)s') % locals())
                # Testing the RCPT TO step should detect most relaying problems
                (code, repl) = smtp.rcpt(email_to)
                if code not in (250, 251):
                    raise UserError(_('The server refused the test recipient (%(email_to)s) '
                                      'with error %(repl)s') % locals())
                # Beginning the DATA step should detect some deferred rejections
                # Can't use self.data() as it would actually send the mail!
                smtp.putcmd("data")
                (code, repl) = smtp.getreply()
                if code != 354:
                    raise UserError(_('The server refused the test connection '
                                      'with error %(repl)s') % locals())
            except UserError as e:
                # let UserErrors (messages) bubble up
                raise e
            except Exception as e:
                raise UserError(_("Connection Test Failed! Here is what we got instead:\n %s") % ustr(e))
            finally:
                try:
                    if smtp:
                        smtp.close()
                except Exception:
                    # ignored, just a consequence of the previous exception
                    pass

        title = _("Connection Test Succeeded!")
        message = _("Everything seems properly set up!")
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'message': message,
                'sticky': False,
            }
        }

    def build_email(self, email_from, email_to, subject, body, email_cc=None, email_bcc=None, reply_to=False,
                    attachments=None, message_id=None, references=None, object_id=False, subtype="plain", headers=None,
                    body_alternative=None, subtype_alternative="plain"):
        email = self.env["mail.mail"].search([("message_id", "=", message_id)], limit=1)
        if not email_bcc and email and email.email_bcc:
            email_bcc = tools.email_split(email.email_bcc)
        return super(IrMailServer, self).build_email(email_from, email_to, subject, body, email_cc, email_bcc, reply_to,
                                                     attachments, message_id, references, object_id, subtype, headers,
                                                     body_alternative, subtype_alternative)