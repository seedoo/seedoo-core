from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.osv.query import Query
from odoo.modules.module import get_module_resource
from odoo.exceptions import ValidationError
import base64
import re

SELECTION_PROTOCOLLO_ACTION = [
    ("mail_da_protocollare", "Protocol to do"),   # Protocollo non esistente
    ("bozza_da_protocollare", "Protocol draft"),  # Protocollo esistente in stato bozza
    ("protocollata", "Protocol done"),            # Protocollo esistente in stato registrato
    ("non_protocollata", "Protocol not done"),    # Da non protocollare
    ("non_protocollabile", "Protocol not to do")  # Non protocollare
]


class Mail(models.Model):
    _inherit = "mail.mail"

    protocollo_action = fields.Selection(
        string="Protocol action state",
        selection=SELECTION_PROTOCOLLO_ACTION,
        default="non_protocollabile"
    )

    protocollo_id = fields.Many2one(
        string="Protocol",
        comodel_name="sd.protocollo.protocollo"
    )

    protocollo_in_id = fields.Many2one(
        string="Protocol from mail",
        comodel_name="sd.protocollo.protocollo"
    )

    protocollo_restore_mail_id = fields.Many2one(
        string="Original mail",
        comodel_name="mail.mail"
    )

    def write(self, vals):
        result = super(Mail, self).write(vals)
        # se si sta aggiornando protocollo_action si notifica la modifica della mail per aggiornare la dashboard
        state = vals.get("protocollo_action", None)
        if not state:
            return result
        self.notify_partners({"event": "mailupdated"})
        return result

    def send(self, auto_commit=False, raise_exception=False):
        # Storico di avvenuto invio della e-mail/pec
        invio_obj = self.env["sd.protocollo.invio"]
        res = super().send(auto_commit, raise_exception)
        for mail in self:
            invio = invio_obj.search([("messaggio_id", "=", mail.id)])
            if invio:
                invio.protocollo_id.storico_invio_mail(invio, mail.state)
        return res

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # se la chiave protocollo_action è già presente nei vals non c'è bisogno di valorizzarla
            if "protocollo_action" in vals:
                continue
            # devono essere segnate come da protocollare le mail che rientrano nei seguenti casi
            # - caso 1: le mail in ingresso
            # - caso 2: le mail in ingresso su un account PEC
            # - caso 3: le PEC in ingresso con pec_type posta-certificata o errore (le ricevute delle PEC non sono protocollabili)
            is_direction_in = True if ("direction" in vals and vals["direction"] == "in") else False
            is_pec = True if ("pec" in vals and vals["pec"]) else False
            is_posta_semplice = True if (not ("pec_type" in vals) or vals["pec_type"] == False) else False
            is_posta_certificata = True if ("pec_type" in vals and vals["pec_type"] in ["posta-certificata", "errore"]) else False
            caso1 = is_direction_in and not is_pec
            caso2 = is_direction_in and is_pec and is_posta_semplice
            caso3 = is_direction_in and is_pec and is_posta_certificata
            if caso1 or caso2 or caso3:
                vals["protocollo_action"] = "mail_da_protocollare"
        return super().create(vals_list)

    def protocollo_crea_da_mail(self, vals, folder_id, documento_tipologia, documento_attachment_id=False, storico=True):
        self.ensure_one()
        if self.protocollo_id:
            raise ValidationError("La mail è stata già protocollata!")
        protocollo_obj = self.env["sd.protocollo.protocollo"]
        company_id = vals.get("company_id", False)
        mezzo_trasmissione_id = self.with_context(company_id=company_id)._get_mezzo_trasmissione_id()
        if not mezzo_trasmissione_id:
            raise ValidationError("Mezzo di trasmissione non trovato!")
        archivio_id = protocollo_obj.with_context(company_id=company_id)._default_archivio_id()
        if not archivio_id:
            raise ValidationError("Archivio corrente non trovato!")
        # recupero dei vals per la creazione del protocollo
        vals = self._get_protocollo_vals(vals, folder_id, mezzo_trasmissione_id, archivio_id)
        allegato_vals_list = []
        allegato_vals = {
            "filename": "original_email.eml",
            "content": self.original_eml,
            "subject": False,
            "folder_id": folder_id
        }
        # Il file eml verrà caricato come documento principale se presente "l'original_eml" e la tipologia è "eml"
        # altrimenti l'original_eml verrà caricato come allegato
        if self.original_eml and documento_tipologia == "eml":
            vals["documento_id_filename"] = "original_email.eml"
            vals["documento_id_content"] = self.original_eml
            vals["documento_id_oggetto"] = self.subject
            vals["documento_id_cartella_id"] = folder_id
        elif documento_tipologia == "postacert" and self.original_attachment_ids:
            postacert_file = [x for x in self.original_attachment_ids if x.name == "postacert.eml"]
            if postacert_file:
                postacert_file = postacert_file[0]
            vals["documento_id_filename"] = "postacert.eml"
            vals["documento_id_content"] = postacert_file.datas
            vals["documento_id_oggetto"] = self.subject
            vals["documento_id_cartella_id"] = folder_id
        elif self.original_eml:
            allegato_vals_list.append(allegato_vals)
        # il body della mail deve essere caricato come documento principale se il documento da caricare è il corpo del
        # messaggio altrimenti deve essere caricato come allegato del protocollo
        company = self.env["res.company"].browse(company_id)
        body_pdf_content = self._get_body_pdf_content(company)
        body_pdf_content_encode = base64.b64encode(body_pdf_content) if body_pdf_content else ""
        if documento_tipologia == "testo":
            vals["documento_id_filename"] = "mailbody.pdf"
            vals["documento_id_content"] = body_pdf_content_encode
            vals["documento_id_oggetto"] = False
            vals["documento_id_cartella_id"] = folder_id
        else:
            allegato_vals_list.append({
                "filename": "mailbody.pdf",
                "content": body_pdf_content_encode,
                "subject": False,
                "folder_id": folder_id
            })
        # si cicla su ogni allegato della mail per caricarli nei documenti del protocollo
        for attachment in self.attachment_ids:
            # un allegato della mail deve essere caricato come documento principale se il documento da caricare è un
            # allegato e l'allegato corrente è l'allegato selezionato nei restanti casi l'allegato della mail deve
            # essere caricato come allegato anche nel protocollo
            if documento_tipologia == "allegato" and attachment.id == documento_attachment_id:
                vals["documento_id_filename"] = attachment.name
                vals["documento_id_content"] = attachment.datas
                vals["documento_id_oggetto"] = False
                vals["documento_id_cartella_id"] = folder_id
            else:
                allegato_vals_list.append({
                    "filename": attachment.name,
                    "content": attachment.datas,
                    "subject": False,
                    "folder_id": folder_id
                })
        # recupero del mittente
        mittente_ids = vals.pop("mittente_ids") if "mittente_ids" in vals else []
        # creazione del protocollo e del documento associato ad esso
        protocollo = protocollo_obj.with_context(
            from_module=_("Communications"),
            tipologia_documento_protocollo="documento").create(vals)
        # salvataggio del mittente nel documento del protocollo e aggiornamento del producer
        protocollo.documento_id.write({
            "sender_ids": mittente_ids,
            "producer": "Metafora"
        })
        # creazione degli allegati al protocollo
        for allegato_vals in allegato_vals_list:
            allegato_vals["protocollo_id"] = protocollo.id
            self.env["sd.dms.document"].create(allegato_vals)
        # salvataggio del protocollo_id e dello stato bozza_da_protocollare nella mail da cui è stato creato il protocollo
        self.write({
            "protocollo_id": protocollo.id,
            "protocollo_in_id": protocollo.id,
            "protocollo_action": "bozza_da_protocollare"
        })
        for mail in self.pec_mail_child_ids:
            if not mail.protocollo_id:
                mail.protocollo_id = protocollo.id
        if storico:
            self.storico_crea_protocollo_da_mail(protocollo.numero_protocollo)
        return {
            "name": "Protocollo",
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form,tree",
            "res_model": "sd.protocollo.protocollo",
            "res_id": protocollo.id,
            "target": "current",
            "context": {"active_id": protocollo.id, "active_ids": [protocollo.id]}
        }

    def _get_body_pdf_content(self, company_id):
        report_mail_template = self.env.ref("sd_protocollo_pec.report_sd_protocollo_pec_mail_mail_qweb")
        pdf_mail_mail = report_mail_template.sudo().with_context(company_id=company_id)._render_qweb_pdf([self.id])[0]
        return pdf_mail_mail

    def _get_utc_to_local_date(self):
        utilities_obj = self.env["fl.utility.dt"]
        timezone = self.env["ir.config_parameter"].sudo().get_param("sd_protocollo.timezone")
        data_ricezione = utilities_obj.utc_to_local(self.date, timezone).strftime("%d-%m-%Y %H:%M:%S")
        return data_ricezione

    def _get_document_list(self):
        documet_list = []
        for document in self.attachment_ids:
            file = "file_%s.svg" % document.name.split(".")[-1]
            image_path = "/sd_dms/static/src/img/thumbnails/%s" % file
            resource = get_module_resource("sd_dms", "static/src/img/thumbnails", file)
            if not resource:
                image_path = "sd_dms/static/src/img/thumbnails/file_unkown.svg"
            documet_list.append((image_path, document.name))
        return documet_list

    def get_call_wizard_condition(self, call_action=False):
        context = dict(self.env.context, mail_id=self.id, mail_ids=[self.id])
        wizard_action = {
            "name": "Crea Bozza Protocollo",
            "view_type": "form",
            "views": [(False, "form")],
            "res_model": "sd.protocollo.wizard.protocollo.crea.da.mail",
            "type": "ir.actions.act_window",
            "target": "new",
            "context": context
        }

        # TODO: quando il field riservato gestirà l'aggiornamento delle acl, il wizard verrà aperto secondo le
        #       condizioni sotto riportate
        return wizard_action if call_action else True

        wizard_obj = self.env["sd.protocollo.wizard.protocollo.crea.da.mail"].with_context(mail_id=self.id)
        documento_tipologia_options = wizard_obj.get_documento_tipologia_options()

        # se per la mail c'è più di una tipologia di documento che si può protocollare allora si deve usare il wizard
        if len(documento_tipologia_options) != 1:
            return wizard_action if call_action else True
        documento_tipologia = documento_tipologia_options[0][0]

        # se l'unica tipologia di documento da protocollare sono gli allegati allora si deve usare il wizard
        if documento_tipologia == "allegato":
            return wizard_action if call_action else True

        # se è attiva la multicompany si deve usare il wizard
        company_ids = self.env["res.company"].get_selected_company_ids()
        if len(company_ids) == 0 or len(company_ids) > 1:
            return wizard_action if call_action else True
        wizard = wizard_obj.create({"documento_tipologia": documento_tipologia})
        wizard.onchange_company_id()
        wizard.onchange_protocollatore_ufficio_id()

        # se l'utente corrente può protocollare con più di un ufficio allora si deve usare il wizard
        if not wizard.protocollatore_ufficio_id:
            return wizard_action if call_action else True

        # se l'utente è abilitato a più di un registro allora si deve usare il wizard
        if not wizard.registro_id:
            return wizard_action if call_action else True

        # se non è stata impostata la cartella di default per i documenti del protocollo allora si deve usare il wizard
        if not wizard.folder_id:
            return wizard_action if call_action else False
        return wizard.action_crea_bozza_protocollo() if call_action else False

    def protocollo_crea_da_mail_action(self):
        self.ensure_one()
        return self.get_call_wizard_condition(True)

    def non_protocollare_mail_action(self):
        for mail in self:
            mail.protocollo_action = "non_protocollata"
            mail.storico_mail_protocollo_action_non_protocollata()

    def ripristina_da_non_protocollata_action(self):
        for mail in self:
            mail.protocollo_action = "mail_da_protocollare"
            mail.storico_ripristina_per_protocollazione_mail()


    def ripristina_da_protocollata_action(self):
        for mail in self:
            default_values = {
                "state": "incoming",
                "protocollo_action": "mail_da_protocollare",
                "protocollo_id": False,
                "protocollo_restore_mail_id": mail.id
            }
            new_mail = mail.copy(default=default_values)
            mail.storico_ripristina_da_protocollata_mail()
            new_mail.storico_creata_da_ripristino()

    @api.model
    def _get_mezzo_trasmissione_id(self):
        self.ensure_one()
        domain = [("can_used_to_protocol", "=", True)]
        if self.pec:
            domain.append(("integrazione", "=", "pec"))
        mezzo_trasmissione = self.env["sd.protocollo.mezzo.trasmissione"].search(domain, limit=1)
        if mezzo_trasmissione:
            return mezzo_trasmissione.id
        return False

    def _get_protocollo_vals(self, vals, folder_id, mezzo_trasmissione_id, archivio_id):
        # vengono inizializzati i primi valori da utilizzare nella creazione del protocollo
        vals["protocollatore_id"] = self.env.uid
        vals["tipologia_protocollo"] = "ingresso"
        vals["data_ricezione"] = self.server_received_datetime if self.server_received_datetime else self.date
        vals["mezzo_trasmissione_id"] = mezzo_trasmissione_id
        vals["archivio_id"] = archivio_id
        vals["mail_id"] = self.id
        vals["documento_id_cartella_id"] = folder_id
        vals["tipologia_protocollo"] = "ingresso"
        # creazione del mittente del protocollo
        mittente_vals = self._get_mittente_vals()
        vals["mittente_ids"] = [(0, 0, mittente_vals)]
        return vals

    def _get_mittente_vals(self):
        self.ensure_one()
        is_pec = self.pec
        mittente_email = self.email_from
        mittente_name = ""
        # nel caso di una mail inviata ad un indirizzo pec allora il mittente deve essere considerato come un indirizzo email
        if self.pec and self.pec_type == "errore":
            is_pec = False
        if re.findall('^"Per conto di: \S+@\S+"\\n* <[^>]+>', self.email_from):
            # se il mittente ha il seguente formato:
            # "Per conto di: test02@pec.flosslab.it" <posta-certificata@pec.aruba.it>
            # allora deve restituire solamente la pec contenuta all'interno (nell'esempio: test02@pec.flosslab.it)
            results = re.findall('^"Per conto di: \S+@\S+"', self.email_from)
            if results:
                mittente_email = results[0].replace('"', '').replace("Per conto di: ", "")
                mittente_name = ""
        elif re.findall("<[^>]+>", self.email_from):
            # se il mittente ha il seguente formato:
            # Nome Cognome <test02@pec.flosslab.it>
            # allora deve restituire Nome Cognome come name e l'indirizzo test02@pec.flosslab.it come email
            results = re.findall("<[^>]+>", self.email_from)
            mittente_email = results[0].strip("<>")
            mittente_name = self.email_from.replace(results[0], "").replace("\"", "").strip()
        # altrimenti si ricerca fra i domicili digitali se esiste un mittente con la stessa indirizzo email/PEC. In
        # questo caso si ricerca prima nel domicilio digitale e poi solo dopo nei partner per dare precedenza ed
        # associare al mittente la relativa AOO del domicilio digitale. Infatti potrebbe esistere un partner con la
        # stessa pec mail (la PA associata alla AOO) e se si ricercasse come primo step nei partner l'associazione
        # verrebbe fatta alla PA
        domain = [("email_address", "=", mittente_email), ("aoo_id", "!=", False)]
        digital_domicile = self.env["res.partner.digital.domicile"].search(domain, limit=1)
        if digital_domicile:
            # se esite un domicilio digitale con lo stesso indirizzo si copiano i valori della AOO per creare il contatto
            mittente = self.env["sd.dms.contact"].get_values_partner_contact(digital_domicile.aoo_id, partner_values=False)
            mittente["typology"] = "sender"
            return mittente
        # altrimenti si ricerca fra i partner se esiste un mittente con la stessa indirizzo email/PEC
        domain = ["|", ("pec_mail", "=", mittente_email), ("email", "=", mittente_email)]
        partner = self.env["res.partner"].search(domain, limit=1)
        if partner:
            # se esite un partner con lo stesso indirizzo si copiano i relativi valori per creare il contatto
            mittente = self.env["sd.dms.contact"].get_values_partner_contact(partner, partner_values=False)
            mittente["typology"] = "sender"
            return mittente
        # altrimenti si ricerca fra gli altri indirizzi se esiste un mittente con la stessa indirizzo email/PEC
        domain = [("email_address", "=", mittente_email), ("partner_id", "!=", False)]
        email_address = self.env["res.partner.email.address"].search(domain, limit=1)
        if email_address:
            # se esite un altro indirizzo con lo stesso indirizzo si copiano i valori del partner per creare il contatto
            mittente = self.env["sd.dms.contact"].get_values_partner_contact(email_address.partner_id, partner_values=False)
            mittente["typology"] = "sender"
            return mittente
        # altrimenti se la mail è una PEC si creano i valori per un contatto con indirizzo PEC
        if is_pec:
            mittente = {
                "typology": "sender",
                "company_type": "person",
                "name": mittente_name,
                "pec_mail": mittente_email
            }
            return mittente
        # altrimenti si creano i valori per un contatto con indirizzo email
        mittente = {
            "typology": "sender",
            "company_type": "person",
            "name": mittente_name,
            "email": mittente_email
        }
        return mittente

    def _get_mail_format_fields(self):
        fields_list = super(Mail, self)._get_mail_format_fields()
        fields_to_append = ["protocollo_action"]
        # se l'utente corrente è il SUPERUSER_ID allora è in esecuzione il cron del fetch, quindi non ha senso andare a
        # recuperare il campo button_crea_bozza_protocollo_invisible perché la relativa visibilità deve essere calcolata
        # in funzione dell'utente che visualizza la mail (il recupero del valore verrà fatto mediante una chiamata
        # inserita nel frontend - file messaging_notification_handler.js)
        if self.env.uid != SUPERUSER_ID:
            fields_to_append.extend([
                "button_crea_bozza_protocollo_invisible",
                "button_non_protocollare_invisible",
                "button_ripristina_da_non_protocollata_invisible",
                "button_ripristina_da_protocollata_invisible"
            ])

        fields_list.extend(fields_to_append)
        return fields_list

    # @api.model
    # def _get_mail_client_mail_check_ids(self, mail_ids):
    #     """
    #     Il metdo deve essere esteso per aggiungere gli id delle mail che fanno parte di un flusso di protocollazione. Se
    #     l'utente ha visibilità del protocollo allora deve avere anche la visibilità delle relative mail facenti parte di
    #     tale flusso.
    #     :param mail_ids:
    #     :return:
    #     """
    #     ids = super(Mail, self)._get_mail_client_mail_check_ids(mail_ids)
    #
    #     protocollo_obj = self.env["sd.protocollo.protocollo"]
    #     alias_dict = {}
    #     operation = "read"
    #     query = Query(None, protocollo_obj._table)
    #
    #     protocollo_obj._set_joins(query, alias_dict, operation)
    #     mail_alias = query.join(
    #         "sd_protocollo_protocollo",
    #         "id",
    #         "mail_mail",
    #         "protocollo_id",
    #         "mail_alias"
    #     )
    #
    #     protocollo_obj._set_conditions(query, alias_dict, operation)
    #
    #     if mail_ids:
    #         query.add_where("{table}.id IN ({ids})".format(
    #             table=mail_alias,
    #             ids=", ".join(str(mail_id) for mail_id in mail_ids)
    #         ))
    #     query_str, params = query.select("DISTINCT {table}.id".format(
    #         table=mail_alias
    #     ))
    #     self.env.cr.execute(query_str, params)
    #     access_ids = [row[0] for row in self.env.cr.fetchall()]
    #     return ids + access_ids

    ####################################################################################################################
    # Algoritmo di verifica acl
    ####################################################################################################################

    @api.model
    def _set_joins(self, query, alias_dict, operation="read"):
        super(Mail, self)._set_joins(query, alias_dict, operation)
        protocollo_alias = query.left_join(
            "mail_mail",
            "protocollo_id",
            "sd_protocollo_protocollo",
            "id",
            "spp"
        )
        documento_alias = query.left_join(
            protocollo_alias,
            "id",
            "sd_dms_document",
            "protocollo_id",
            "sdd"
        )
        alias_dict["sd_protocollo_protocollo"] = protocollo_alias
        alias_dict["sd_dms_document"] = documento_alias
        self.env["sd.dms.document"]._set_joins(query, alias_dict, operation)

    @api.model
    def _get_conditions(self, alias_dict, operation):
        conditions = super(Mail, self)._get_conditions(alias_dict, operation)
        conditions.append(self._get_permission_protocollo_mail_client_account_conditions(alias_dict, operation))
        return conditions

    # Restituisce la condizione per verificare che l'utente corrente abbia un permesso sul protocollo legato alla mail
    @api.model
    def _get_permission_protocollo_mail_client_account_conditions(self, alias_dict, operation):
        conditions = self.env["sd.dms.document"]._get_conditions(alias_dict, operation)
        return """mail_mail.protocollo_id IS NOT NULL AND (({conditions}))""".format(
            conditions=") OR (".join(conditions)
        )