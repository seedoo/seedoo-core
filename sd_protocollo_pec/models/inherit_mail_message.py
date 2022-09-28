from odoo import api, fields, models
from odoo.osv.query import Query


class MailMessage(models.Model):

    _inherit = "mail.message"

    @api.model
    def _get_mail_client_message_check_ids(self, message_ids):
        """
        Il metdo deve essere esteso per aggiungere gli id dei message associati a mail che fanno parte di un flusso di
        protocollazione. Se l'utente ha visibilità del protocollo allora deve avere anche la visibilità delle relative
        mail facenti parte di tale flusso.
        :param message_ids:
        :return:
        """
        ids = super(MailMessage, self)._get_mail_client_message_check_ids(message_ids)

        protocollo_obj = self.env["sd.protocollo.protocollo"]
        alias_dict = {}
        operation = "read"
        query = Query(None, protocollo_obj._table)

        protocollo_obj._set_joins(query, alias_dict, operation)
        mail_alias = query.join(
            "sd_protocollo_protocollo",
            "id",
            "mail_mail",
            "protocollo_id",
            "mail_alias"
        )
        message_alias = query.join(
            mail_alias,
            "mail_message_id",
            "mail_message",
            "id",
            "message_alias"
        )

        protocollo_obj._set_conditions(query, alias_dict, operation)

        if message_ids:
            query.add_where("{table}.id IN ({ids})".format(
                table=message_alias,
                ids=", ".join(str(message_id) for message_id in message_ids)
            ))
        query_str, params = query.select("DISTINCT {table}.id".format(
            table=message_alias
        ))
        self.env.cr.execute(query_str, params)
        access_ids = [row[0] for row in self.env.cr.fetchall()]
        return ids + access_ids