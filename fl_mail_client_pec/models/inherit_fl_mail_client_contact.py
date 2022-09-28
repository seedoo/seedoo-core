# -*- coding: utf-8 -*-

from odoo import fields, models, tools, api


class Contact(models.Model):

    _inherit = "fl.mail.client.contact"

    pec_mail = fields.Char(
        string="PEC",
        store=False
    )

    def _select(self):
        select_query = super(Contact, self)._select()
        select_query = select_query + " UNION " + """
            SELECT id*10 + 1 AS id,
                   pec_mail AS email,
                   id AS partner_id,
                   CONCAT(name, ' <', pec_mail, '>') AS name,
                   type AS type,
                   is_company AS is_company,
                   parent_id AS parent_id,
                   function AS function,
                   phone AS phone,
                   mobile AS mobile
            FROM res_partner
            WHERE active = TRUE AND 
                  pec_mail IS NOT NULL
        """
        return select_query

    @api.model
    def create(self, vals):
        contacts = super(Contact, self).create(vals)

        if len(contacts) > 1 and "account_id" in self._context:
            # se sono stati inseriti sia l'indirizzo email che l'indirizzo pec, allora verranno creati due contatti.
            # Purtroppo il widget many2many può ricevere solo un valore, quindi si controlla se l'utente ha selezionato
            # l'account con cui mandare la mail: se è un account pec allora si sceglie l'indirizzo pec, altrimenti
            # quello della mail
            email = None
            pec = None
            for contact in contacts:
                if (contact.id % 2) == 0:
                    email = contact
                else:
                    pec = contact

            account_id = self._context.get("account_id", False)
            if account_id:
                account = self.env["fl.mail.client.account"].browse(account_id)
                if account.pec:
                    return pec
                else:
                    return email

            return email

        return contacts
