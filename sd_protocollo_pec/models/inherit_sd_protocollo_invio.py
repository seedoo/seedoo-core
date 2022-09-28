import base64
import re

from odoo import models, fields, api
import datetime

SELECTION_MODALITA_INVIO = [
    ("broadcast", "Broadcast")
]

class Invio(models.Model):
    _inherit = "sd.protocollo.invio"

    modalita_invio = fields.Selection(
        string="Modalità di Invio",
        selection=SELECTION_MODALITA_INVIO,
        default=SELECTION_MODALITA_INVIO[0][0]
    )

    mezzo_trasmissione_integrazione = fields.Selection(
        string="Mezzo Trasmissione Integrazione",
        related="mezzo_trasmissione_id.integrazione"
    )

    messaggio_id = fields.Many2one(
        string="Messaggio",
        comodel_name="mail.mail"
    )

    messaggio_is_pec = fields.Boolean(
        string="È pec",
        related="messaggio_id.pec"
    )

    data_invio = fields.Datetime(
        compute="_compute_data_invio",
        store=True
    )

    # il campo ricevuta_pec_ids non può essere un related perché va in conflitto con i permessi delle mail
    ricevuta_pec_ids = fields.One2many(
        string="Ricevute Pec",
        compute="_compute_ricevuta_pec_ids",
        comodel_name="mail.mail"
    )

    undelivery_message_id = fields.Many2one(
        string="Messaggio Non Consegnato",
        comodel_name="mail.mail"
    )

    da_inviare = fields.Boolean(
        string="Da Inviare",
        compute="_compute_da_inviare",
        store=True,
        readonly=True,
        default=False
    )

    da_reinviare = fields.Boolean(
        string="Da Reinviare",
        compute="_compute_da_reinviare",
        store=True,
        readonly=True,
        default=False
    )

    da_resettare = fields.Boolean(
        string="Da Resettare",
        compute="_compute_da_resettare",
        store=True,
        readonly=True,
        default=False
    )

    def _compute_ricevuta_pec_ids(self):
        for invio in self:
            if invio.messaggio_id:
                invio.ricevuta_pec_ids = self.env["mail.mail"].search([
                    ("pec_mail_parent_id", "=", invio.messaggio_id.id)
                ])
            else:
                invio.ricevuta_pec_ids = False

    @api.depends("messaggio_id.state")
    def compute_state(self):
        super(Invio, self).compute_state()
        for rec in self:
            if rec.messaggio_id:
                rec.state = rec.messaggio_id.state
            # Al cambiamento dello state dell'invio se lo stato risulita in exception il protocollo dovrà avere
            # il protocollatore_stato in stato "lavorazione" per far vedere nella dashboard i protocolli con invii in
            # errore
            if rec.state == "exception" and rec.protocollo_id.protocollatore_stato == "lavorazione_completata":
                rec.protocollo_id.protocollatore_stato = "lavorazione"
                rec.protocollo_id.rimetti_in_lavorazione_protocollatore(self.env.uid, False)

    @api.depends("messaggio_id.sent_datetime")
    def _compute_data_invio(self):
        for rec in self:
            if rec.messaggio_id:
                rec.data_invio = rec.messaggio_id.sent_datetime

    @api.depends("mezzo_trasmissione_integrazione", "state", "ricevuta_pec_ids", "invio_successivo_ids")
    def _compute_da_reinviare(self):
        for invio in self:

            risolto = len(invio.get_destinatario_to_resend_list()) == 0

            # caso base: reinvio, con almeno una ricevuta
            caso_base = invio.mezzo_trasmissione_integrazione == "pec" and len(invio.ricevuta_pec_ids.ids)>0

            # caso 1: caso base con ricezione di una PEC in stato exception e il cui invio non possiede un invio_successivo_id
            caso1 = caso_base and not len(invio.invio_successivo_ids.ids)>0 and invio.state == "exception"

            # caso 2: caso base con ricevuta di conferma che contiene daticert con un indirizzo di tipo non certificato
            # con il parametro "risolto" (che conteggia il numero di contatti errati già risolti) a False
            caso2 = caso_base and not risolto

            invio.da_reinviare = caso1 or caso2

    @api.depends("mezzo_trasmissione_integrazione", "state", "ricevuta_pec_ids")
    def _compute_da_resettare(self):
        for invio in self:
            # caso pec: reinvio di una PEC in stato exception e senza una ricevuta (la PEC non è stata inviata per via
            # di un errore nel server)
            caso_pec = invio.mezzo_trasmissione_integrazione == "pec" and \
                       invio.state == "exception" and \
                       not invio.ricevuta_pec_ids
            invio.da_resettare = caso_pec

    @api.depends("da_reinviare", "da_resettare")
    def _compute_da_inviare(self):
        for invio in self:
            invio.da_inviare = invio.da_resettare or \
                               (invio.da_reinviare and invio.mezzo_trasmissione_integrazione == "pec")

    def get_destinatario_to_resend_list(self):
        self.ensure_one()
        destinatario_to_resend_list = []
        for ricevuta in self.ricevuta_pec_ids:
            if ricevuta.pec_type in ["errore", "errore-consegna"]:
                for destinatario in self.destinatario_ids:
                    if ricevuta.recipient_addr.strip().lower() == destinatario.email:
                        destinatario_to_resend_list.append(destinatario)
        for destinatario in self.destinatario_ids:
            if destinatario.daticert_tipo != "certificato":
                if destinatario not in destinatario_to_resend_list:
                    destinatario_to_resend_list.append(destinatario)
        for invio_successivo in self.invio_successivo_ids:
            for invio_successivo_destinatario in invio_successivo.destinatario_ids:
                if invio_successivo_destinatario.invio_precedente_destinatario_id in destinatario_to_resend_list:
                    destinatario_to_resend_list.remove(invio_successivo_destinatario.invio_precedente_destinatario_id)
        return destinatario_to_resend_list

    @api.model
    def crea_invio_mail(self, protocollo_id, mezzo_trasmissione_id, destinatario_vals_list, modalita_invio, account_id, oggetto, body):
        mezzo_trasmissione_obj = self.env["sd.protocollo.mezzo.trasmissione"]
        mail_client_obj = self.env["fl.mail.client.account"]
        mezzo_trasmissione = mezzo_trasmissione_obj.browse(mezzo_trasmissione_id)

        attachment_ids = self._check_for_attachment(protocollo_id, mezzo_trasmissione)

        invio_vals = {
            "protocollo_id": protocollo_id,
            "mezzo_trasmissione_id": mezzo_trasmissione_id,
            "mezzo_trasmissione_nome": mezzo_trasmissione.nome,
            "modalita_invio": modalita_invio
        }

        account_id = mail_client_obj.browse(account_id)
        # sostituisce tutto ciò che è più di uno spazio con lo spazio singolo
        clean_subject = re.sub('\s+', ' ', oggetto)
        messaggio_vals = {
            "email_from": account_id.email,
            "account_id": account_id.id,
            "mail_server_id": account_id.ir_mail_server_id.id,
            "state": "outgoing",
            "subject": clean_subject,
            "body_html": body,
            "direction": "out",
            "protocollo_action": "protocollata",
            "protocollo_id": protocollo_id
        }

        title_type = "Email"
        if mezzo_trasmissione.integrazione == "pec":
            title_type = "Pec Mail"
            messaggio_vals.update({
                "pec": True,
                "pec_type": "posta-certificata",
            })

        if attachment_ids:
            messaggio_vals.update({
                "attachment_ids": [(6, 0, attachment_ids)]
            })

        if modalita_invio == "broadcast":
            email_list = []
            destinatario_ids = []
            invio_precedente_ids = []
            for destinatario_vals in destinatario_vals_list:
                destinatario_ids.append((0, 0, destinatario_vals))
                email_list.append(destinatario_vals["email"])
                invio_precedente_destinatario_id = destinatario_vals.get("invio_precedente_destinatario_id", False)
                invio_precedente_id = self._get_invio_precedente_id(invio_precedente_destinatario_id)
                if not invio_precedente_id:
                    continue
                invio_precedente_ids.append((4, invio_precedente_id))
            invio_vals.update({"destinatario_ids": destinatario_ids})
            self._crea_invio_mail(invio_vals, messaggio_vals, destinatario_ids, email_list, invio_precedente_ids)

        elif modalita_invio == "unicast":
            for destinatario_vals in destinatario_vals_list:
                destinatario_ids = [(0, 0, destinatario_vals)]
                invio_vals.update({"destinatario_ids": destinatario_ids})
                invio_precedente_destinatario_id = destinatario_vals.get("invio_precedente_destinatario_id", False)
                invio_precedente_id = self._get_invio_precedente_id(invio_precedente_destinatario_id)
                self._crea_invio_mail(
                    invio_vals,
                    messaggio_vals,
                    destinatario_ids,
                    [destinatario_vals["email"]],
                    [invio_precedente_id] if invio_precedente_id else []
                )

        self.env.user._request_notify_message("success", "Invio %s" % title_type, "Invio creato con successo")

    @api.model
    def _crea_invio_mail(self, invio_vals, messaggio_vals, destinatario_ids, email_list, invio_precedente_ids):
        mail_obj = self.env["mail.mail"]
        invio_obj = self.env["sd.protocollo.invio"]
        invio_vals.update({"destinatario_ids": destinatario_ids})
        invio = invio_obj.create(invio_vals)
        messaggio_vals.update({"email_to": ", ".join(email_list)})
        invio_update_vals = {"messaggio_id": mail_obj.create(messaggio_vals).id}
        if invio_precedente_ids:
            invio_update_vals["invio_precedente_ids"] = invio_precedente_ids
        invio.write(invio_update_vals)

    @api.model
    def _get_invio_precedente_id(self, invio_precedente_destinatario_id):
        if not invio_precedente_destinatario_id:
            False
        destinatario_obj = self.env["sd.protocollo.invio.destinatario"]
        invio_precedente_destinatario = destinatario_obj.browse(invio_precedente_destinatario_id)
        return invio_precedente_destinatario.invio_id.id

    def _check_for_attachment(self, protocollo_id, mezzo_trasmissione):
        # verifica la presenza di documenti nel protocollo e crea l'attachment per ognuno.
        # return lista di ids

        protocollo_obj = self.env["sd.protocollo.protocollo"]
        protocollo = protocollo_obj.browse(protocollo_id)

        document_list = []

        documento_id = protocollo.documento_id
        allegato_ids = protocollo.allegato_ids

        if documento_id:
            document_list.append(documento_id)
        for allegato in allegato_ids:
            document_list.append(allegato)

        attachment_ids = self._get_attachment_from_document(document_list, mezzo_trasmissione)

        if attachment_ids:
            return attachment_ids
        return []

    def _get_attachment_from_document(self, document_list, mezzo_trasmissione):
        attachment_obj = self.env["ir.attachment"]

        attachment_ids = []
        for file in document_list:
            attachment_id = attachment_obj.create(
                {
                    "name": file.filename,
                    "datas": file.content,
                    "store_fname": file.filename
                })
            attachment_ids.append(attachment_id.id)
        return attachment_ids

    @api.depends("state")
    def _storico_invio(self):
        for rec in self:
            if rec.mezzo_trasmissione_integrazione == "pec":
                rec.protocollo_id.storico_invio_pec(rec.id)

    def action_reinvia_mail(self):
        self.ensure_one()
        context = dict(
            self.env.context,
            invio_ids=[self.id]
        )
        return {
            "name": "Reinvio Mail",
            "view_type": "form",
            "view_mode": "form,tree",
            "res_model": "sd.protocollo.wizard.protocollo.reinvio.mail",
            "type": "ir.actions.act_window",
            "target": "new",
            "context": context
        }

    def action_reset_mail(self):
        for rec in self:
            if rec.state == "exception":
                rec.state = "outgoing"
                rec.messaggio_id.state = "outgoing"
