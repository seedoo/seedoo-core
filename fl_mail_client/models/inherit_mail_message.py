from odoo import api, fields, models
import re


class MailMessage(models.Model):

    _inherit = "mail.message"

    # i campi direction, account_id, account_wkf_create_uid sono stati aggiunti al modello MailMessage al posto del modello MailMail per gestire la visibilità
    direction = fields.Selection(
        [("in", "In"), ("out", "Out")],
        string="Direction"
    )

    account_id = fields.Many2one(
        "fl.mail.client.account",
        string="Account",
    )

    @api.model
    def _get_reply_to(self, values):
        """
        Il metodo viene esteso in modo tale da sovrascrivere il reply_to nel caso in cui la mail sia inviata tramite
        un server in uscita configurato come client mail. Infatti, di default, il reply_to viene impostato in funzione
        del parametro di configurazione mail.catchall.domain, il quale se settato imposta il rispondi con un
        indirizzo mail che non ha niente a che vedere con il mittente del server.
        """
        if not values:
            return super(MailMessage, self)._get_reply_to(values)
        email_from = values.get("email_from", False)
        if not email_from:
            return super(MailMessage, self)._get_reply_to(values)
        email_from = self.get_parsed_email_from(email_from)
        mail_server_id = values.get("mail_server_id", False)
        if mail_server_id:
            mail_server = self.env["ir.mail_server"].sudo().browse(mail_server_id)
            if mail_server and mail_server.mail_client:
                return email_from
        account_id = values.get("account_id", False)
        if account_id:
            return email_from
        return super(MailMessage, self)._get_reply_to(values)

    @api.model
    def get_parsed_email_from(self, email_from):
        if re.findall('^"Per conto di: \S+@\S+"\\n* <[^>]+>', email_from):
            # se il mittente ha il seguente formato:
            # "Per conto di: test02@pec.flosslab.it" <posta-certificata@pec.aruba.it>
            # allora deve restituire solamente la pec contenuta all'interno (nell'esempio: test02@pec.flosslab.it)
            results = re.findall('^"Per conto di: \S+@\S+"', email_from)
            if results:
                email_from = results[0].replace('"', '').replace("Per conto di: ", "")
        return email_from

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        """ Override that adds specific access rights of mail.message, to remove
        ids uid could not see according to our custom rules. Please refer to
        check_access_rule for more details about those rules.

        Non employees users see only message with subtype (aka do not see
        internal logs).

        After having received ids of a classic search, keep only:
        - if author_id == pid, uid is the author, OR
        - uid belongs to a notified channel, OR
        - uid is in the specified recipients, OR
        - uid has a notification on the message
        - direction and account_id have a value
        - otherwise: remove the id
        """
        # Rules do not apply to administrator
        if self.env.is_superuser():
            return super(MailMessage, self)._search(
                args, offset=offset, limit=limit, order=order,
                count=count, access_rights_uid=access_rights_uid)
        # Non-employee see only messages with a subtype (aka, no internal logs)
        if not self.env['res.users'].has_group('base.group_user'):
            args = ['&', '&', ('subtype_id', '!=', False), ('subtype_id.internal', '=', False)] + list(args)
        # Perform a super with count as False, to have the ids, not a counter
        ids = super(models.Model, self)._search(
            args, offset=offset, limit=limit, order=order,
            count=False, access_rights_uid=access_rights_uid)
        if not ids and count:
            return 0
        elif not ids:
            return ids

        pid = self.env.user.partner_id.id
        author_ids, partner_ids, channel_ids, allowed_ids, message_account_ids = set([]), set([]), set([]), set([]), set([])
        model_ids = {}

        # check read access rights before checking the actual rules on the given ids
        super(MailMessage, self.with_user(access_rights_uid or self._uid)).check_access_rights('read')

        self.flush(['model', 'res_id', 'author_id', 'message_type', 'partner_ids', 'channel_ids'])
        self.env['mail.notification'].flush(['mail_message_id', 'res_partner_id'])
        self.env['mail.channel'].flush(['channel_message_ids'])
        self.env['mail.channel.partner'].flush(['channel_id', 'partner_id'])
        for sub_ids in self._cr.split_for_in_conditions(ids):
            self._cr.execute("""
                    SELECT DISTINCT m.id, m.model, m.res_id, m.author_id, m.message_type,
                                    COALESCE(partner_rel.res_partner_id, needaction_rel.res_partner_id),
                                    channel_partner.channel_id as channel_id
                    FROM "%s" m
                    LEFT JOIN "mail_message_res_partner_rel" partner_rel
                    ON partner_rel.mail_message_id = m.id AND partner_rel.res_partner_id = %%(pid)s
                    LEFT JOIN "mail_message_res_partner_needaction_rel" needaction_rel
                    ON needaction_rel.mail_message_id = m.id AND needaction_rel.res_partner_id = %%(pid)s
                    LEFT JOIN "mail_message_mail_channel_rel" channel_rel
                    ON channel_rel.mail_message_id = m.id
                    LEFT JOIN "mail_channel" channel
                    ON channel.id = channel_rel.mail_channel_id
                    LEFT JOIN "mail_channel_partner" channel_partner
                    ON channel_partner.channel_id = channel.id AND channel_partner.partner_id = %%(pid)s

                    WHERE m.id = ANY (%%(ids)s)""" % self._table, dict(pid=pid, ids=list(sub_ids)))
            for id, rmod, rid, author_id, message_type, partner_id, channel_id in self._cr.fetchall():
                if author_id == pid:
                    author_ids.add(id)
                elif partner_id == pid:
                    partner_ids.add(id)
                elif channel_id:
                    channel_ids.add(id)
                elif rmod and rid and message_type != 'user_notification':
                    model_ids.setdefault(rmod, {}).setdefault(rid, set()).add(id)

            message_account_ids = message_account_ids.union(set(self._get_mail_client_message_ids(sub_ids)))

        allowed_ids = self._find_allowed_doc_ids(model_ids)

        final_ids = author_ids | partner_ids | channel_ids | allowed_ids | message_account_ids

        if count:
            return len(final_ids)
        else:
            # re-construct a list based on ids, because set did not keep the original order
            id_list = [id for id in ids if id in final_ids]
            return id_list

    def check_access_rule(self, operation):
        """ Access rules of mail.message:
            - read: if
                - author_id == pid, uid is the author OR
                - uid is in the recipients (partner_ids) OR
                - uid has been notified (needaction) OR
                - uid is member of a listern channel (channel_ids.partner_ids) OR
                - uid have read access to the related document if model, res_id
                - direction and account_id have a value
                - otherwise: raise
            - create: if
                - no model, no res_id (private message) OR
                - pid in message_follower_ids if model, res_id OR
                - uid can read the parent OR
                - uid have write or create access on the related document if model, res_id, OR
                - direction and account_id have a value
                - otherwise: raise
            - write: if
                - author_id == pid, uid is the author, OR
                - uid is in the recipients (partner_ids) OR
                - uid is moderator of the channel and moderation_status is pending_moderation OR
                - uid has write or create access on the related document if model, res_id and moderation_status is not pending_moderation
                - direction and account_id have a value
                - otherwise: raise
            - unlink: if
                - uid is moderator of the channel and moderation_status is pending_moderation OR
                - uid has write or create access on the related document if model, res_id and moderation_status is not pending_moderation
                - direction and account_id have a value
                - otherwise: raise

        Specific case: non employee users see only messages with subtype (aka do
        not see internal logs).
        """

        if self.env.is_superuser():
            return

        if not self.ids:
            return super(MailMessage, self).check_access_rule(operation)

        ids = set(self.ids) - set(self._get_mail_client_message_ids(self.ids))

        return super(MailMessage, self.browse(ids)).check_access_rule(operation)

    @api.model
    def _get_mail_client_message_ids(self, message_ids):
        if not message_ids:
            return []
        if self.env.user.has_group("fl_mail_client.group_fl_mail_client_manager"):
            return message_ids
        else:
            return self._get_mail_client_message_check_ids(message_ids)

    # @api.model
    # def _get_mail_client_message_skip_ids(self, message_ids):
    #     """
    #     Metodo per recuperare la lista degli id dei message per gli utenti con gruppo group_fl_mail_client_administrator.
    #     Si verifica solo che il message sia associato ad una account client mail.
    #     :param message_ids:
    #     :return:
    #     """
    #     query = """
    #         SELECT DISTINCT me.id
    #         FROM mail_message me
    #         WHERE me.account_id IS NOT NULL AND
    #               me.id IN ({ids})
    #     """.format(
    #         ids=",".join(str(message_id) for message_id in message_ids)
    #     )
    #     self.env.cr.execute(query)
    #     ids = [result[0] for result in self.env.cr.fetchall()]
    #     return ids

    @api.model
    def _get_mail_client_message_check_ids(self, message_ids):
        """
        Metodo per recuperare la lista degli id dei message per tutti i restanti utenti. Devono essere restituiti tutti
        gli id dei messageper cui l'utente ha la visibilità in ingresso o in uscita per il relativo account.
        :param message_ids:
        :return:
        """
        query = """
            SELECT DISTINCT me.id
            FROM mail_message me, fl_mail_client_account_permission fmcap
            WHERE me.account_id = fmcap.account_id AND
                  fmcap.user_id = {uid} AND
                  (
                    (me.direction = 'in' AND fmcap.show_inbox_mails = TRUE) OR 
                    (me.direction = 'out' AND fmcap.show_outgoing_mails = TRUE)
                  ) AND 
                  me.id IN ({ids})
        """.format(
            uid=self.env.uid,
            ids=",".join(str(message_id) for message_id in message_ids)
        )
        self.env.cr.execute(query)
        ids = [result[0] for result in self.env.cr.fetchall()]
        return ids