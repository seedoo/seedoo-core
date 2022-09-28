import datetime

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.fields import Datetime

SELECTION_STATE = [
    ("bozza", "Bozza"),
    ("registrato", "Registrato"),
    ("annullato", "Annullato")
]

SELECTION_PROTOCOLLATORE_STATO = [
    ("lavorazione", "In lavorazione"),
    ("lavorazione_completata", "Lavorazione completata")
]

SELECTION_TIPOLOGIA_REGISTRAZIONE = [
    ("normale", "Normale"),
    ("emergenza", "Emergenza")
]

SELECTION_TIPOLOGIA_PROTOCOLLO = [
    ("ingresso", "Ingresso"),
    ("uscita", "Uscita")
]


class Protocollo(models.Model):
    _name = "sd.protocollo.protocollo"
    _inherit = ["mail.thread", "fl.security"]
    _rec_name = "anno_numero_protocollo"
    _description = "Protocollo"

    # se si modificano i campi dell'ordinamento di default è necessario aggiornare il relativo indice definito nell'init
    _order = "data_registrazione DESC, id DESC"

    @api.model
    def _default_company_id(self):
        return self.env.company.id

    @api.model
    def _default_company_id_readonly(self):
        if self.env["res.company"].get_selected_company_ids(count=True) == 1:
            return True
        return False

    @api.model
    def _default_protocollatore_ufficio_id(self):
        set_ids = self.env["fl.set.set"].search([("can_used_to_protocol", "=", True)]).ids
        if len(set_ids) == 1:
            return set_ids[0]
        return False

    @api.model
    def _default_protocollatore_ufficio_id_readonly(self):
        if self._default_protocollatore_ufficio_id():
            return True
        return False

    @api.model
    def _default_registro_id(self):
        registro_ids = self.env["sd.protocollo.registro"].search([("can_used_to_protocol", "=", True)]).ids
        if len(registro_ids) == 1:
            return registro_ids[0]
        return False

    @api.model
    def _default_registro_id_readonly(self):
        if self._default_registro_id():
            return True
        return False

    @api.model
    def _default_tipologia_registrazione_invisible(self):
        registro_ids = self.env["sd.protocollo.registro.emergenza"].search([("can_used_to_protocol", "=", True)]).ids
        if len(registro_ids) == 0:
            return True
        return False

    @api.model
    def _default_archivio_id(self):
        archivio_ids = self.env["sd.protocollo.archivio"].search([("can_used_to_protocol", "=", True)]).ids
        if len(archivio_ids) == 1:
            return archivio_ids[0]
        return False

    @api.model
    def _default_user_tipologia_protocollo(self, tipologia):
        if tipologia:
            for selection_tuple_value in self._get_user_tipologia_protocollo_selection():
                if tipologia == selection_tuple_value[0]:
                    return tipologia
        return False

    numero_protocollo = fields.Char(
        string="Protocollo N.",
        readonly=True
    )

    anno_numero_protocollo = fields.Char(
        string="Anno Numero Protocollo",
        readonly=True
    )

    anno = fields.Integer(
        string="Anno",
        readonly=True
    )

    active = fields.Boolean(
        string="Active",
        default=True
    )

    state = fields.Selection(
        string="Stato",
        selection=SELECTION_STATE,
        default=SELECTION_STATE[0][0],
        index=True
    )

    data_registrazione = fields.Datetime(
        string="Data Registrazione",
        readonly=True
    )

    company_id = fields.Many2one(
        string="Azienda",
        comodel_name="res.company",
        required=True,
        default=_default_company_id
    )

    company_id_readonly = fields.Boolean(
        string="Company readonly",
        compute="_compute_company_id_readonly",
        default=_default_company_id_readonly
    )

    create_date = fields.Datetime(
        string="Create Date",
        readonly=True
    )

    create_uid = fields.Many2one(
        string="User Creatore del Protocollo",
        comodel_name="res.users",
        readonly=True,
    )

    protocollatore_id = fields.Many2one(
        string="Protocollatore",
        comodel_name="res.users",
        required=True,
        readonly=True,
        default=lambda self: self.env.user,
        index=True
    )

    protocollatore_name = fields.Char(
        string="Nome protocollatore",
        readonly=True
    )

    protocollatore_ufficio_id = fields.Many2one(
        string="Ufficio protocollatore",
        comodel_name="fl.set.set",
        domain="[('can_used_to_protocol', '=', True)]",
        required=True
    )

    protocollatore_ufficio_id_readonly = fields.Boolean(
        string="Ufficio protocollatore readonly",
        compute="_compute_protocollatore_ufficio_id_readonly"
    )

    protocollatore_ufficio_name = fields.Char(
        string="Nome ufficio protocollatore",
        readonly=True
    )

    registro_id = fields.Many2one(
        string="Registro",
        comodel_name="sd.protocollo.registro",
        domain="[('can_used_to_protocol', '=', True)]",
        required=True
    )

    registro_id_readonly = fields.Boolean(
        string="Registro",
        compute="_compute_registro_id_readonly"
    )

    archivio_id = fields.Many2one(
        string="Archivio",
        comodel_name="sd.protocollo.archivio",
        required=True,
        readonly=True,
        index=True
    )

    protocollatore_stato = fields.Selection(
        string="Stato protocollatore",
        selection=SELECTION_PROTOCOLLATORE_STATO,
        default=SELECTION_PROTOCOLLATORE_STATO[0][0],
        readonly=True,
        index=True
    )

    tipologia_registrazione = fields.Selection(
        string="Tipologia Registrazione",
        selection=SELECTION_TIPOLOGIA_REGISTRAZIONE,
        default=SELECTION_TIPOLOGIA_REGISTRAZIONE[0][0]
    )

    tipologia_registrazione_invisible = fields.Boolean(
        string="Tipologia Registrazione Invisible",
        compute="_compute_tipologia_registrazione_invisible"
    )

    is_reply = fields.Boolean(
        string="Protocollo generato tramite la funzionalità rispondi",
        default=False
    )

    def _get_user_tipologia_protocollo_selection(self):
        user = self.env.user
        selection_tipologia_protocollo = []

        # Utente attuale ha il permesso di creare protocolli in ingresso verrà aggiunta alla selection la voce "ingresso"
        if user.has_group("sd_protocollo.group_sd_protocollo_crea_protocollo_ingresso"):
            selection_tipologia_protocollo.append(("ingresso", "Ingresso"))
        # Utente attuale ha il permesso di creare protocolli in uscita verrà aggiunta alla selection la voce "uscita"
        if user.has_group("sd_protocollo.group_sd_protocollo_crea_protocollo_uscita"):
            selection_tipologia_protocollo.append(("uscita", "Uscita"))
        return selection_tipologia_protocollo

    user_tipologia_protocollo = fields.Selection(
        string="Tipologia",
        selection=lambda self: self._get_user_tipologia_protocollo_selection(),
        default=lambda self: self._default_user_tipologia_protocollo(self.tipologia_protocollo),
        store=False
    )

    tipologia_protocollo = fields.Selection(
        string="Tipologia",
        selection=SELECTION_TIPOLOGIA_PROTOCOLLO,
        compute="_compute_tipologia_protocollo",
        store=True
    )

    tipologia_protocollo_readonly = fields.Boolean(
        string="Readonly tipologia protocollo",
        compute="_compute_tipologia_protocollo_readonly"
    )

    mezzo_trasmissione_id = fields.Many2one(
        string="Mezzo Trasmissione",
        comodel_name="sd.protocollo.mezzo.trasmissione",
        domain="[('can_used_to_protocol','=',True)]",
    )

    mezzo_trasmissione_icon = fields.Char(
        string="Mezzo Trasmissione Icon",
        related="mezzo_trasmissione_id.icon",
    )

    mezzo_trasmissione_icon_color = fields.Char(
        string="Mezzo Trasmissione Icon Color",
        related="mezzo_trasmissione_id.icon_color",
    )

    mezzo_trasmissione_nome = fields.Char(
        string="Mezzo Trasmissione Nome"
    )

    mezzo_trasmissione_id_readonly = fields.Boolean(
        string="MezzoTrasmissione Readonly",
        compute="_compute_mezzo_trasmissione_id_readonly"
    )

    mezzo_trasmissione_id_invisible = fields.Boolean(
        string="MezzoTrasmissione Invisible",
        compute="_compute_mezzo_trasmissione_id_invisible"
    )

    riservato = fields.Boolean(
        string="Riservato",
        default=False
    )

    riservato_readonly = fields.Boolean(
        string="Riservato Readonly",
        compute="_compute_riservato_readonly"
    )

    data_ricezione = fields.Datetime(
        string="Data Ricezione"
    )

    data_ricezione_invisible = fields.Boolean(
        string="Data Ricezione Invisible",
        compute="_compute_data_ricezione_invisible"
    )

    data_ricezione_required = fields.Boolean(
        string="Data Ricezione Required",
        compute="_compute_data_ricezione_required"
    )

    data_ricezione_readonly = fields.Boolean(
        string="Data Ricezione Readonly",
        compute="_compute_data_ricezione_readonly"
    )

    documento_id = fields.Many2one(
        string="Documento",
        comodel_name="sd.dms.document",
    )

    documento_id_content = fields.Binary(
        string="Documento",
        compute="_compute_documento_id_data",
        inverse="_inverse_documento_id_data"
    )

    documento_id_filename = fields.Char(
        string="Nome File",
        compute="_compute_documento_id_data",
        inverse="_inverse_documento_id_data"
    )

    documento_id_oggetto = fields.Text(
        string="Oggetto",
        compute="_compute_documento_id_data",
        inverse="_inverse_documento_id_data"
    )

    documento_id_document_type_id = fields.Many2one(
        string="Tipologia documento",
        comodel_name="sd.dms.document.type",
        domain=[("registration_type", "=", "protocol")],
        compute="_compute_documento_id_data",
        inverse="_inverse_documento_id_data"
    )

    documento_id_cartella_id = fields.Many2one(
        string="Cartella",
        comodel_name="sd.dms.folder",
        domain="[('company_id', '=', company_id),('perm_create', '=', True)]",
        compute="_compute_documento_id_data",
        inverse="_inverse_documento_id_data"
    )

    documento_id_impronta = fields.Char(
        string="Impronta",
        compute="_compute_documento_id_data"
    )

    # il campo dovrebbe essere chiamato documento_id_mimetype ma, per poter funzionare il widget di anteprima del file
    # usato nel form, il campo deve essere chiamato mimetype altrimenti nel form non trova il relativo campo
    mimetype = fields.Char(
        string="Type",
        related="documento_id.mimetype",
        readonly=True
    )

    documento_id_content_required = fields.Boolean(
        string="Documento Content Required",
        compute="_compute_documento_id_content_required"
    )

    documento_id_content_readonly = fields.Boolean(
        string="Documento Content Readonly",
        compute="_compute_documento_id_content_readonly"
    )

    documento_id_oggetto_required = fields.Boolean(
        string="Documento Oggetto Required",
        compute="_compute_documento_id_oggetto_required"
    )

    documento_id_oggetto_readonly = fields.Boolean(
        string="Documento Oggetto Readonly",
        compute="_compute_documento_id_oggetto_readonly"
    )

    documento_id_document_type_id_required = fields.Boolean(
        string="Tipo Documento Required",
        compute="_compute_documento_id_document_type_id_required"
    )

    documento_id_document_type_id_readonly = fields.Boolean(
        string="Tipo Documento Readonly",
        compute="_compute_documento_id_document_type_id_readonly"
    )

    documento_id_cartella_id_readonly = fields.Boolean(
        string="Documento Cartella Readonly",
        compute="_compute_documento_id_cartella_id_readonly"
    )

    emergenza_numero_protocollo = fields.Char(
        string="Numero Protocollo in Emergenza",
    )

    emergenza_data_registrazione = fields.Datetime(
        string="Data Registrazione Emergenza"
    )

    registro_giornaliero_id = fields.Many2one(
        string="Registro Giornaliero",
        comodel_name="sd.protocollo.registro.giornaliero"
    )

    mittente = fields.Char(
        string="Nominativo mittente",
        readonly=True,
        compute="_compute_mittente",
        store=True
    )

    mittente_interno_id = fields.Many2one(
        string="Mittente interno",
        comodel_name="fl.set.voce.organigramma",
        domain=[("parent_active", "=", True)],
        readonly=True
    )

    mittente_interno_nome = fields.Char(
        string="Nominativo mittente interno",
        readonly=True
    )

    mittente_interno_utente_id = fields.Many2one(
        string="User Mittente Interno",
        comodel_name="res.users",
        compute="_compute_mittente_user_set_id",
        store=True
    )

    mittente_interno_utente_id_email = fields.Char(
        string="Email",
        related="mittente_interno_utente_id.email"
    )

    mittente_interno_utente_id_pec_mail = fields.Char(
        string="Pec Mail",
        related="mittente_interno_utente_id.pec_mail"
    )

    mittente_interno_ufficio_id = fields.Many2one(
        string="Ufficio Mittente Interno",
        comodel_name="fl.set.set",
        compute="_compute_mittente_user_set_id",
        store=True
    )

    mittente_interno_ufficio_id_set_type = fields.Selection(
        string="Mittente interno uffcio tipologia",
        related="mittente_interno_ufficio_id.set_type"
    )

    mittente_ids = fields.Many2many(
        string="Mittenti",
        related="documento_id.sender_ids",
        readonly=True
    )

    mittente_invisible = fields.Boolean(
        string="Mittente Invisibile",
        compute="_compute_mittente_invisible",
        store=False
    )

    mittente_interno_id_invisible = fields.Boolean(
        string="Mittente Interno Invisible",
        compute="_compute_mittente_interno_id_invisible"
    )

    mittente_numero_protocollo = fields.Char(
        string="Numero Protocollo Mittente"
    )

    mittente_data_registrazione = fields.Date(
        string="Data Registrazione Mittente"
    )

    mittente_registro = fields.Char(
        string="Registro Mittente"
    )

    mittente_nome = fields.Char(
        string="Nome Mittente"
    )

    destinatari = fields.Char(
        string="Lista destinatari",
        readonly=True,
        compute="_compute_destinatari",
        store=True
    )

    destinatario_ids = fields.Many2many(
        string="Destinatari",
        related="documento_id.recipient_ids",
        readonly=True
    )

    altro_soggetto_ids = fields.Many2many(
        string="Altri Soggetti",
        related="documento_id.other_subjects_ids",
        readonly=True
    )

    altro_soggetto = fields.Char(
        string="Lista altri soggetti",
        readonly=True,
        compute="_compute_altro_soggetto",
        store=True
    )

    assegnazione_ids = fields.One2many(
        string="Assegnatari",
        comodel_name="sd.protocollo.assegnazione",
        inverse_name="protocollo_id",
        required=True,
        readonly=True
    )

    assegnazione_parent_ids = fields.One2many(
        string="Assegnatari parent",
        comodel_name="sd.protocollo.assegnazione",
        inverse_name="protocollo_id",
        domain=[("parent_id", "=", False)],
        readonly=True
    )

    assegnazione_competenza_ids = fields.One2many(
        string="Assegnazioni Competenza",
        comodel_name="sd.protocollo.assegnazione",
        inverse_name="protocollo_id",
        domain=[("parent_id", "=", False), ("tipologia", "=", "competenza")],
        readonly=True
    )

    assegnazione_conoscenza_ids = fields.One2many(
        string="Assegnazioni Conoscenza",
        comodel_name="sd.protocollo.assegnazione",
        inverse_name="protocollo_id",
        domain=[("parent_id", "=", False), ("tipologia", "=", "conoscenza")],
        readonly=True
    )

    da_assegnare = fields.Boolean(
        string="Da Assegnare",
        compute="_compute_da_assegnare",
        store=True,
        readonly=True,
        default=False
    )

    da_inviare = fields.Boolean(
        string="Da Inviare",
        compute="_compute_da_inviare",
        store=True,
        readonly=True,
        default=False
    )

    allegato_ids = fields.One2many(
        string="Allegati",
        comodel_name="sd.dms.document",
        inverse_name="protocollo_id",
        domain=lambda self: [("id", "!=", self.documento_id.id)],
        readonly=True
    )

    allegato_count = fields.Integer(
        "# Allegati",
        compute="_compute_allegato_count",
    )

    invio_ids = fields.One2many(
        string="Invii",
        comodel_name="sd.protocollo.invio",
        inverse_name="protocollo_id",
        readonly=True,
    )

    source_count = fields.Integer(
        "# Source",
        compute="_compute_source_count",
    )

    field_invisible = fields.Boolean(
        string="Field Invisile",
        compute="_compute_protocollo_attrs",
        readonly=True
    )

    field_required = fields.Boolean(
        string="Field Required",
        compute="_compute_protocollo_attrs",
        readonly=True
    )

    field_readonly = fields.Boolean(
        string="Field Required",
        compute="_compute_protocollo_attrs",
        readonly=True
    )

    acl_ids = fields.Many2many(
        string="Acl",
        related="documento_id.acl_ids",
        readonly=False
    )

    system_acl_ids = fields.Many2many(
        string="System Acl",
        related="documento_id.system_acl_ids",
        readonly=True
    )

    inherit_acl_ids = fields.Many2many(
        string="Acl inherited",
        related="documento_id.inherit_acl_ids"
    )

    imported_other_software = fields.Boolean(
        string="Imported from other software"
    )

    # data_registrazione_da = fields.Date(
    #     string="Registrato dal",
    #     default=lambda a, *k: {}.strftime('%m-%d-%Y 00:00:00'),
    #     store=False
    # )
    #
    # data_registrazione_in = fields.Date(
    #     string="Registrato il",
    #     default=lambda a, *k: {}.strftime('%m-%d-%Y 00:00:00'),
    #     store=False
    # )
    #
    # data_registrazione_a = fields.Date(
    #     string="Registrato fino al",
    #     default=lambda a, *k: {}.strftime('%m-%d-%Y 00:00:00'),
    #     store=False
    # )
    #
    # data_ricezione_da = fields.Date(
    #     string="Ricevuto dal",
    #     default=lambda a, *k: {}.strftime('%m-%d-%Y 00:00:00'),
    #     store=False
    # )
    #
    # data_ricezione_in = fields.Date(
    #     string="Ricevuto il",
    #     default=lambda a, *k: {}.strftime('%m-%d-%Y 00:00:00'),
    #     store=False
    # )
    #
    # data_ricezione_a = fields.Date(
    #     string="Ricevuto fino al",
    #     default=lambda a, *k: {}.strftime('%m-%d-%Y 00:00:00'),
    #     store=False
    # )

    def init(self):
        # inserimento dell'indice utilizzato nella ricerca della tree e kanban view: è importante inserire sia il l'id
        # che il campo usato nella property _order per definire l'ordinamento di default usato nel modello: i due campi
        # in questione verranno utilizzati nella query di ricerca di visibilità
        sd_protocollo_protocollo_id_data_registrazione_index = "sd_protocollo_protocollo_id_data_registrazione_index"
        self.env.cr.execute("""
            SELECT indexname FROM pg_indexes WHERE indexname = '%s'
        """ % sd_protocollo_protocollo_id_data_registrazione_index)
        if not self.env.cr.fetchone():
            self.env.cr.execute("""
                CREATE INDEX %s ON sd_protocollo_protocollo USING btree (id, data_registrazione)
            """ % sd_protocollo_protocollo_id_data_registrazione_index)
        sd_protocollo_protocollo_data_registrazione_id_index = "sd_protocollo_protocollo_data_registrazione_id_index"
        self.env.cr.execute("""
            SELECT indexname FROM pg_indexes WHERE indexname = '%s'
        """ % sd_protocollo_protocollo_data_registrazione_id_index)
        if not self.env.cr.fetchone():
            self.env.cr.execute("""
                CREATE INDEX %s ON sd_protocollo_protocollo USING btree (data_registrazione, id)
            """ % sd_protocollo_protocollo_data_registrazione_id_index)

    @api.model
    def create(self, vals_list):
        res = super(Protocollo, self).create(vals_list)
        for rec in res:
            if not vals_list.get("numero_protocollo", False):
                bozza_name = "bozza %s" % rec.id
                rec.sudo().write({
                    "numero_protocollo": bozza_name,
                    "anno_numero_protocollo": bozza_name
                })
            if rec.documento_id and not rec.documento_id.protocollo_id:
                rec.documento_id.write({"protocollo_id": rec.id})
            self.aggiorna_acl("creazione", rec.id)
            # Scrittura su storico dell'avvenuta creazione della bozza
            res.storico_crea_bozza(self.env.context.get("from_module", False))
        return res

    def write(self, vals):
        context = dict(self.env.context)
        if "documento_id_content" in vals:
            context["update_documento_id_content"] = True
        if "documento_id_oggetto" in vals:
            context["update_documento_id_oggetto"] = True
        old_riservato_val_dict = {}
        for rec in self:
            old_riservato_val_dict[rec.id] = rec.riservato
        result = super(Protocollo, self.with_context(context)).write(vals)
        # se si sta salvando il document type per il documento principale del protocollo si controlla se i relativi
        # allegati non lo contengono in modo da aggiornalo anche su di essi
        for rec in self:
            if "riservato" in vals and old_riservato_val_dict[rec.id] != rec.riservato:
                self.aggiorna_acl("riservato", rec.id)
            document_type_id = vals.get("documento_id_document_type_id", False)
            if not document_type_id:
                continue
            for allegato in rec.allegato_ids:
                if allegato.document_type_id:
                    continue
                allegato.write({"document_type_id": document_type_id})
        return result

    def copy(self, default=None):
        self.ensure_one()
        values = self.get_protocol_default_value()
        default = dict(default or {})
        default["active"] = True
        default["company_id"] = values["company_id"]
        default["protocollatore_id"] = self.env.user.id
        default["protocollatore_name"] = self.env.user.name
        default["protocollatore_ufficio_id"] = values["protocollatore_ufficio"].id
        default["protocollatore_ufficio_name"] = False
        default["protocollatore_stato"] = "lavorazione"
        default["registro_id"] = values["registro_id"]
        default["archivio_id"] = values["archivio_id"]
        default["data_registrazione"] = False
        default["anno"] = False
        default["anno_numero_protocollo"] = False
        default["numero_protocollo"] = False
        default["is_reply"] = False
        default["tipologia_registrazione"] = "normale"
        default["tipologia_protocollo"] = self.tipologia_protocollo
        default["data_ricezione"] = False
        default["documento_id"] = False
        default["documento_id_content"] = False
        default["documento_id_oggetto"] = self.documento_id_oggetto
        default["documento_id_document_type_id"] = self.documento_id_document_type_id.id
        default["documento_id_cartella_id"] = values["folder"].id
        default["state"] = "bozza"
        default["emergenza_numero_protocollo"] = False
        default["emergenza_data_registrazione"] = False
        default["registro_giornaliero_id"] = False
        record = super(Protocollo, self).copy(default=default)
        return record

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        search_date_list = ["data_registrazione", "data_ricezione"]
        for i, condition in enumerate(domain):
            if condition[0] in search_date_list and condition[1] == "=":
                condition[1] = ">="
                date_time = datetime.datetime.strptime(condition[2], "%Y-%m-%d %H:%M:%S") + datetime.timedelta(days=1)
                date_time = date_time.strftime("%Y-%m-%d %H:%M:%S")
                domain.insert(i-1, "&")
                domain.insert(i+1, [condition[0], "<=", date_time])
                break
        return super(Protocollo, self).search_read(
            domain=domain,
            fields=fields,
            offset=offset,
            limit=limit,
            order=order
        )

    def get_protocol_default_value(self):
        company_id = self._default_company_id()
        context = dict(
            self.env.context,
            company_id=company_id
        )
        self = self.with_context(context)
        set_list = self.env["fl.set.set"].search([("can_used_to_protocol", "=", True)])
        if len(set_list) == 0:
            raise ValidationError(_("You don't have an office enable to protocol!"))
        if self.protocollatore_ufficio_id.id in set_list.ids:
            protocollatore_ufficio = self.protocollatore_ufficio_id
        else:
            protocollatore_ufficio = set_list[0]
        self = self.with_context(self._get_copy_context(protocollatore_ufficio))
        registro_ids = self.env["sd.protocollo.registro"].search([("can_used_to_protocol", "=", True)]).ids
        if len(registro_ids) == 0:
            raise ValidationError(_("You don't have a register enable to protocol!"))
        if self.registro_id.id in registro_ids:
            registro_id = self.registro_id.id
        else:
            registro_id = registro_ids[0]
        archivio_ids = self.env["sd.protocollo.archivio"].search([("can_used_to_protocol", "=", True)]).ids
        if len(archivio_ids) == 0:
            raise ValidationError(_("You don't have an archive enable to protocol!"))
        if self.archivio_id.id in archivio_ids:
            archivio_id = self.archivio_id.id
        else:
            archivio_id = archivio_ids[0]
        folder = self.env["sd.protocollo.cartella"].get_folder(self, "protocollo")
        if not folder:
            raise ValidationError(_("You don't have a folder to save documents protocol!"))

        return {
            "company_id": company_id,
            "protocollatore_ufficio": protocollatore_ufficio,
            "registro_id": registro_id,
            "archivio_id": archivio_id,
            "registro_ids": registro_ids,
            "archivio_ids": archivio_ids,
            "folder": folder
        }

    @api.model
    def _get_copy_context(self, protocollatore_ufficio):
        return self.env.context

    # sovrascrive il metodo di mail.thread per evitare che venga creato il messaggio di storico nella creazione del
    # record. Si è preferito usare questa soluzione rispetto all'inserimento nel context del valore mail_create_nolog
    # uguale True perché quest'ultimo impediva la visualizzazione dei successivi messaggi di storico all'interno della
    # vista form del protocollo, anche se i messaggi di storico venivano comunque creati
    def _creation_message(self):
        return ""

    @api.onchange("user_tipologia_protocollo")
    def _compute_tipologia_protocollo(self):
        for rec in self:
            tipologia_protocollo = False
            # la tipologia del protocollo non può essere cambiata una volta registrato il protocollo
            if not rec.tipologia_protocollo or (rec.tipologia_protocollo and rec.state == "bozza"):
                tipologia_protocollo = rec.user_tipologia_protocollo
            rec.tipologia_protocollo = tipologia_protocollo

    @api.onchange("mezzo_trasmissione_id")
    def _default_data_ricezione(self):
        self.ensure_one()
        if not self.data_ricezione and self.tipologia_protocollo == "ingresso":
            self.data_ricezione = Datetime.now()

    @api.onchange("protocollatore_ufficio_id", "tipologia_protocollo")
    def _default_mittente_interno_id(self):
        self.ensure_one()
        voce_organigramma_obj = self.env["fl.set.voce.organigramma"]

        tipologia = self._get_tipologia_mittente_id()

        if self.protocollatore_ufficio_id and self.state == "bozza" and self.tipologia_protocollo in tipologia:
            mittente_interno = False
            ufficio_id = voce_organigramma_obj.search([("ufficio_id", "=", self.protocollatore_ufficio_id.id)]).id
            if ufficio_id:
                mittente_interno = voce_organigramma_obj.search(
                    [("parent_id", "=", ufficio_id), ("utente_id", "=", self.protocollatore_id.id)]
                )
            if mittente_interno:
                self.mittente_interno_id = mittente_interno.id
                self.mittente_interno_nome = mittente_interno.nome

    def _get_tipologia_mittente_id(self):
        return ["uscita"]

    @api.constrains("data_ricezione")
    def constrains_data_ricezione(self):
        if not self.data_ricezione:
            return

        if self.tipologia_protocollo != "ingresso":
            return

        if self.data_ricezione and self.state != "bozza":
            if self.data_ricezione and self.data_registrazione and self.data_ricezione > self.data_registrazione:
                raise ValidationError(_("The receipt date entered cannot be greater than the registration date"))
        if self.data_ricezione > Datetime.now():
            raise ValidationError(_("The date of receipt cannot be greater than the current date"))

    @api.depends("documento_id")
    def _compute_documento_id_data(self):
        for protocollo in self:
            documento = protocollo.documento_id
            cartella = self.env["sd.protocollo.cartella"].get_folder(protocollo, "protocollo")
            cartella_id = cartella.id if cartella else False
            protocollo.documento_id_content = documento.content if documento else False
            protocollo.documento_id_filename = documento.filename if documento else False
            protocollo.documento_id_oggetto = documento.subject if documento else False
            protocollo.documento_id_impronta = documento.checksum if documento else False
            protocollo.documento_id_document_type_id = documento.document_type_id.id if documento else False
            protocollo.documento_id_cartella_id = documento.folder_id.id if documento else cartella_id

    def _get_documento_values(self, protocollo):
        documento = protocollo.documento_id
        filename = protocollo.documento_id_filename if protocollo.documento_id_filename else documento.filename
        if not filename:
            filename = "Documento Protocollo"
        # il content del documento deve essere aggiornato solo se effettivamente è stato modificato. Per stabilirlo si è
        # valorizzato nel context il campo update_documento_id_content all'interno del metodo write solo nel caso in cui
        # il campo documento_id_content sia stato modificato. Questo controllo non può essere fatto all'interno di
        # questo metodo perché è usato in comune con gli altri campi, di conseguenza non si riesce a stabilire quando il
        # campo documento_id_content arriva vuoto perchè è stato rimosso il file oppure perchè non è stato modificato.
        # Negli altri due campi documento_id_oggetto e documento_id_cartella_id questo problema non succede perché sono
        # sempre obbligatori
        documento_id_content = documento.content
        if protocollo.documento_id_content or self.env.context.get("update_documento_id_content", False):
            documento_id_content = protocollo.documento_id_content
        documento_id_oggetto = documento.subject
        if protocollo.documento_id_oggetto or self.env.context.get("update_documento_id_oggetto", False):
            documento_id_oggetto = protocollo.documento_id_oggetto
        documento_id_cartella_id = documento.folder_id.id
        if protocollo.documento_id_cartella_id:
            documento_id_cartella_id = protocollo.documento_id_cartella_id.id
        documento_id_document_type_id = documento.document_type_id.id
        if protocollo.documento_id_document_type_id:
            documento_id_document_type_id = protocollo.documento_id_document_type_id.id
        return {
            "protocollo_id": protocollo.id,
            "filename": filename,
            "content": documento_id_content,
            "subject": documento_id_oggetto,
            "folder_id": documento_id_cartella_id,
            "document_type_id": documento_id_document_type_id
        }

    def _inverse_documento_id_data(self):
        for protocollo in self:
            vals = self._get_documento_values(protocollo)
            if not protocollo.documento_id:
                self.env["sd.dms.document"].with_context(tipologia_documento_protocollo="documento").create(vals)
            else:
                protocollo.documento_id.write(vals)

    @api.depends("mittente_interno_id")
    def _compute_mittente_user_set_id(self):
        for protocollo in self:
            if protocollo.mittente_interno_id:
                protocollo.mittente_interno_ufficio_id = protocollo.mittente_interno_id.ufficio_id.id
                protocollo.mittente_interno_utente_id = protocollo.mittente_interno_id.utente_id.id

    def _compute_documento_id_content_required(self):
        for protocollo in self:
            # il content di un documento è obbligatorio nei seguenti casi:
            # - caso 1: l'utente corrente non ha il group group_sd_protocollo_registra_protocollo_senza_documento
            # caso1 = not self.env.user.has_group("sd_protocollo.group_sd_protocollo_registra_protocollo_senza_documento")
            caso1 = False
            protocollo.documento_id_content_required = caso1

    def _compute_documento_id_content_readonly(self):
        for protocollo in self:
            # il content di un documento di un protocollo deve essere in sola lettura nei seguenti casi:
            # - caso 1: il protocollo è registrato e il content del documento è valorizzato
            # - caso 2: l'utente corrente non è il protocollatore
            # - caso 3: l'utente corrente è il protocollatore con stato lavorazione_completata
            caso1 = protocollo.state != "bozza" and protocollo.documento_id_content
            caso2 = self.env.uid != protocollo.protocollatore_id.id
            caso3 = self.env.uid == protocollo.protocollatore_id.id and \
                    protocollo.protocollatore_stato == "lavorazione_completata"
            protocollo.documento_id_content_readonly = caso1 or caso2 or caso3

    def _compute_documento_id_oggetto_required(self):
        for protocollo in self:
            # l'oggetto di un documento di un protocollo deve essere obbligatorio nei seguenti casi
            # - caso 1: il protocollo è in stato registrato o annullato
            caso1 = protocollo.state in ["registrato", "annullato"]
            protocollo.documento_id_oggetto_required = caso1

    def _compute_documento_id_oggetto_readonly(self):
        for protocollo in self:
            # l'oggetto di un documento di un protocollo deve essere in sola lettura nei seguenti casi
            # - caso 1: il protocollo è annullato
            # - caso 2: il protocollo è registrato ed è stato inviato
            # - caso 3: l'utente corrente non è il protocollatore e non ha profilo manager
            # - caso 4: l'utente corrente è il protocollatore con stato lavorazione_completata
            caso1 = protocollo.state == "annullato"
            caso2 = protocollo.state == "registrato" and len(protocollo.invio_ids.ids) > 0
            caso3 = self.env.uid != protocollo.protocollatore_id.id and \
                    not self.env.user.has_group("sd_protocollo.group_sd_protocollo_manager")
            caso4 = self.env.uid == protocollo.protocollatore_id.id and \
                    protocollo.protocollatore_stato == "lavorazione_completata"
            protocollo.documento_id_oggetto_readonly = caso1 or caso2 or caso3 or caso4

    def _compute_documento_id_cartella_id_readonly(self):
        for protocollo in self:
            protocollo.documento_id_cartella_id_readonly = protocollo.documento_id_content_readonly

    def _compute_documento_id_document_type_id_required(self):
        for protocollo in self:
            # la tipologia di un documento di un protocollo deve essere obbligatorio nei seguenti casi
            # - caso 1: il protocollo è in stato registrato o annullato
            caso1 = protocollo.state in ["registrato", "annullato"]
            protocollo.documento_id_document_type_id_required = caso1

    def _compute_documento_id_document_type_id_readonly(self):
        for protocollo in self:
            # l'oggetto di un documento di un protocollo deve essere readonly nei seguenti casi
            # - caso 1: il protocollo è in stato registrato o annullato
            caso1 = protocollo.state in ["registrato", "annullato"]
            protocollo.documento_id_document_type_id_readonly = caso1

    def _compute_mezzo_trasmissione_id_readonly(self):
        for protocollo in self:
            # il mezzo di trasmissione deve essere in sola lettura nei seguenti casi
            # - caso 1: il protocollo è in stato annullato
            # - caso 2: l'utente corrente non è il protocollatore e non ha profilo manager
            # - caso 3: l'utente corrente è il protocollatore con stato lavorazione_completata
            # - caso 4: protocollo è in uscita e sono presenti 1 o più invii
            caso1 = protocollo.state == "annullato"
            caso2 = self.env.uid != protocollo.protocollatore_id.id and \
                    not self.env.user.has_group("sd_protocollo.group_sd_protocollo_manager")
            caso3 = self.env.uid == protocollo.protocollatore_id.id and \
                    protocollo.protocollatore_stato == "lavorazione_completata"
            caso4 = protocollo.tipologia_protocollo == "uscita" and protocollo.invio_ids
            protocollo.mezzo_trasmissione_id_readonly = bool(caso1 or caso2 or caso3 or caso4)

    @api.depends("tipologia_protocollo")
    def _compute_mezzo_trasmissione_id_invisible(self):
        for protocollo in self:
            # il mezzo di trasmissione non devo poter essere visto quando:
            # il protocollo non è ne in uscita che in ingresso
            if protocollo.tipologia_protocollo in ["uscita", "ingresso"]:
                protocollo.mezzo_trasmissione_id_invisible = False
                return
            protocollo.mezzo_trasmissione_id_invisible = True

    @api.onchange("state")
    def _compute_riservato_readonly(self):
        for protocollo in self:
            # - l'utente corrente non ha il gruppo group_sd_protocollo_protocollazione_riservata
            # - il protocollo non è in stato bozza
            protocollo.riservato_readonly = \
                not self.env.user.has_group("sd_protocollo.group_sd_protocollo_protocollazione_riservata") or \
                not protocollo.state == "bozza"

    @api.onchange("tipologia_protocollo")
    def _compute_data_ricezione_invisible(self):
        for protocollo in self:
            protocollo.data_ricezione_invisible = protocollo.tipologia_protocollo != "ingresso"

    @api.onchange("tipologia_protocollo")
    def _compute_data_ricezione_required(self):
        for protocollo in self:
            # la data di ricezione deve essere obbligatorio nei seguenti casi
            # - caso 1: il campo è impostato come obbligatorio nelle impostazioni e il protocollo è in ingresso e il
            #           protocollo è stato registrato
            config_obj = self.env["ir.config_parameter"].sudo()
            required_data = config_obj.get_param("sd_protocollo.required_data_ricezione")
            caso1 = required_data and protocollo.tipologia_protocollo == "ingresso" and protocollo.data_registrazione
            protocollo.data_ricezione_required = caso1

    def _compute_data_ricezione_readonly(self):
        for protocollo in self:
            # la data di ricezione deve essere in sola lettura nei seguenti casi
            # - caso 1: il protocollo è in stato annullato
            # - caso 2: l'utente corrente non è il protocollatore, non ha profilo manager e non è un admin
            # - caso 3: l'utente corrente è il protocollatore con stato lavorazione_completata
            caso1 = protocollo.state == "annullato"
            caso2 = self.env.uid != protocollo.protocollatore_id.id and \
                    not self.env.user.has_group("sd_protocollo.group_sd_protocollo_manager") and \
                    not self.env.user.has_group("sd_protocollo.group_sd_protocollo_administrator")
            caso3 = self.env.uid == protocollo.protocollatore_id.id and \
                    self.protocollatore_stato == "lavorazione_completata"
            protocollo.data_ricezione_readonly = caso1 or caso2 or caso3

    @api.depends("data_registrazione", "assegnazione_competenza_ids")
    def _compute_da_assegnare(self):
        for protocollo in self:
            da_assegnare = True
            if protocollo.assegnazione_competenza_ids:
                da_assegnare = False
            protocollo.da_assegnare = da_assegnare

    @api.depends("data_registrazione", "invio_ids")
    def _compute_da_inviare(self):
        for protocollo in self:
            da_inviare = False
            if protocollo.data_registrazione and protocollo.tipologia_protocollo == "uscita" and not protocollo.invio_ids:
                da_inviare = True
            protocollo.da_inviare = da_inviare

    @api.depends("state")
    def _compute_protocollo_attrs(self):
        for rec in self:
            rec.field_invisible = True
            rec.field_required = True
            rec.field_readonly = False
            if rec.state not in ["bozza"]:
                rec.field_readonly = True

    def _compute_company_id_readonly(self):
        for protocollo in self:
            default_value = self._default_company_id_readonly()
            protocollo.company_id_readonly = default_value or protocollo.data_registrazione

    @api.onchange("company_id")
    def onchange_company_id(self):
        context = dict(
            self.env.context,
            company_id=self.company_id.id
        )
        self = self.with_context(context)
        self.protocollatore_ufficio_id = self._default_protocollatore_ufficio_id()
        self._compute_protocollatore_ufficio_id_readonly()
        self.mezzo_trasmissione_id = False

    @api.onchange("protocollatore_ufficio_id")
    def onchange_protocollatore_ufficio_id(self):
        context = dict(
            self.env.context,
            company_id=self.company_id.id
        )
        self = self.with_context(context)
        self.registro_id = self._default_registro_id()
        self.archivio_id = self._default_archivio_id()
        self._compute_registro_id_readonly()
        self._compute_tipologia_registrazione_invisible()
        if not self.documento_id:
            self.documento_id_cartella_id = self.env["sd.protocollo.cartella"].get_folder(self, "protocollo")

    def _compute_protocollatore_ufficio_id_readonly(self):
        for protocollo in self:
            default_value = self._default_protocollatore_ufficio_id_readonly()
            protocollo.protocollatore_ufficio_id_readonly = default_value or protocollo.data_registrazione

    def _compute_registro_id_readonly(self):
        for protocollo in self:
            default_value = self._default_registro_id_readonly()
            protocollo.registro_id_readonly = default_value or protocollo.data_registrazione

    def _compute_tipologia_registrazione_invisible(self):
        for protocollo in self:
            default_value = self._default_tipologia_registrazione_invisible()
            protocollo.tipologia_registrazione_invisible = default_value or protocollo.data_registrazione

    def _compute_tipologia_protocollo_readonly(self):
        for protocollo in self:
            protocollo.tipologia_protocollo_readonly = True if protocollo.state not in ["bozza"] else False

    @api.onchange("tipologia_protocollo")
    def _onchange_tipologia_protocollo(self):
        protocollo = self.browse(self._origin.id)
        if self.tipologia_protocollo == "uscita":
            if protocollo.documento_id:
                for contatto in protocollo.documento_id.sender_ids:
                    contatto.unlink()
            protocollo.write({
                "mittente_numero_protocollo": False,
                "mittente_data_registrazione": False,
                "data_ricezione": False,
            })
            self.tipologia_protocollo = "uscita"

        if self.tipologia_protocollo == "ingresso":
            protocollo.write({
                "mittente_interno_id": False,
                "mittente_interno_nome": False
            })
        self._compute_mittente_invisible()
        self._compute_mittente_interno_id_invisible()

    def get_filename_documento_protocollo(self, filename, tipologia_documento):
        self.ensure_one()
        fl_utility_obj = self.env["fl.utility.dt"]
        data_corrente = fl_utility_obj.local_to_utc(datetime.datetime.now()).strftime("%Y-%m-%d")
        return "%s_%s_%s_%s_%s" % ("Prot", str(self.numero_protocollo), data_corrente, tipologia_documento, filename)

    @api.depends("allegato_ids")
    def _compute_allegato_count(self):
        for protocollo in self:
            protocollo.allegato_count = len(protocollo.allegato_ids.ids)

    def _compute_source_count(self):
        for protocollo in self:
            protocollo.source_count = 0

    @api.depends("mittente_ids", "mittente_interno_id", "mittente_interno_id.parent_id")
    def _compute_mittente(self):
        for rec in self:
            if rec.mittente_ids:
                mittente = rec.mittente_ids[0].display_name
            elif rec.mittente_interno_id:
                mittente_list = rec._get_mittente_interno_display_name()
                mittente = ", ".join(mittente_list)
            else:
                mittente = False
            rec.mittente = mittente

    def _get_mittente_interno_display_name(self):
        return [self.mittente_interno_id.nome]

    def _compute_mittente_invisible(self):
        for protocollo in self:
            protocollo.mittente_invisible = True if protocollo.tipologia_protocollo == "uscita" else False

    def _compute_mittente_interno_id_invisible(self):
        for protocollo in self:
            # visibilità mittente_interno_id se:
            # - caso1: mittente interno non è popolato
            # - caso2: protocollo non è in ingresso
            caso1 = False if protocollo.mittente_interno_id else True
            caso2 = protocollo.tipologia_protocollo == "ingresso"

            protocollo.mittente_interno_id_invisible = caso1 or caso2

    @api.depends("destinatario_ids")
    def _compute_destinatari(self):
        for rec in self:
            destinatari = ""
            if rec.destinatario_ids:
                destinatari = "; ".join([x.display_name for x in rec.destinatario_ids])
            rec.destinatari = destinatari

    @api.depends("altro_soggetto_ids")
    def _compute_altro_soggetto(self):
        for rec in self:
            altro_soggetto = ""
            if rec.altro_soggetto:
                altro_soggetto = "; ".join([x.name for x in rec.altro_soggetto_ids])
            rec.altro_soggetto = altro_soggetto

    def _get_local_date(self, data, string=False, format="%d-%m-%Y %H:%M:%S"):
        dt_utility = self.env["fl.utility.dt"].sudo()
        timezone = self.env["ir.config_parameter"].sudo().get_param("sd_protocollo.timezone")
        if not timezone:
            timezone = "Europe/Rome"
        dt = dt_utility.utc_to_local(data, timezone)
        if dt:
            if not string:
                return dt
            return dt.strftime(format)
        return False

    @api.constrains("company_id", "mittente_interno_id", "assegnazione_ids")
    def _check_protocollo_validity(self):
        for protocollo in self:
            check_company = self._check_company_protocollo(protocollo)
            if check_company:
                return self._raise_error_message(check_company)

    def _check_company_protocollo(self, protocollo):
        mittente = protocollo.mittente_interno_id.ufficio_id
        if mittente and mittente.company_id != protocollo.company_id:
            return "Verificare la company del mittente:\nla company del mittente deve essere uguale a quella del " \
                   "protocollo"

        for assegnazione in protocollo.assegnazione_ids:

            if assegnazione.assegnatario_id.ufficio_id:
                if assegnazione.assegnatario_id.ufficio_id.company_id != protocollo.company_id:
                    return "Verificare la company dell'assegnatario:\nla company dell'assegnatario deve " \
                           "essere uguale a quella del protocollo"

        # Controllo company cartella documento sia uguale a quella selezionata  nel protocollo
        if protocollo.documento_id_cartella_id and protocollo.documento_id_cartella_id.company_id != protocollo.company_id:
            return "Verificare la company della cartella del documento:\nla company della cartella del documento " \
                   "deve essere uguale a quella del protocollo"

        # Controllo company cartella allegati sia uguale a quella selezionata nel protocollo
        for allegati in protocollo.allegato_ids:
            if allegati.folder_id.company_id != protocollo.company_id:
                return "Verificare la company della cartella degli allegati:\nla company della cartella degli allegati " \
                       "deve essere uguale a quella del protocollo"

    def _raise_error_message(self, message=None):
        if not message:
            message = "Verificare la company"
        raise ValidationError(_(message))

    ####################################################################################################################
    # Security
    ####################################################################################################################

    @api.model
    def skip_security(self):
        result = super(Protocollo, self).skip_security()
        result = result or self.env.user.has_group("sd_protocollo.group_sd_protocollo_superadmin")
        return result

    # Il metodo _set_acl_joins viene esteso per aggiungere un ulteriore join tra la tabella del protocollo e la tabella
    # del documento. Infatti, il protocollo pur implementando la classe security non utilizza delle acl sue ma usa
    # quelle definite nel documento a lui associato.
    @api.model
    def _set_acl_joins(self, query, alias_dict, join_prefix, inherit):
        table_security_alias = query.join(
            self._table,
            "documento_id",
            self._get_security_table(),
            "id",
            join_prefix
        )
        alias_dict[self._get_security_table()] = table_security_alias
        super(Protocollo, self)._set_acl_joins(query, alias_dict, join_prefix, inherit)

    @api.model
    def _get_security_table(self):
        return "sd_dms_document"

    @api.model
    def _get_security_column(self):
        return "protocollo_id"

    @api.model
    def _get_security_model(self):
        return "sd.dms.document"

    @api.model
    def _get_security_inherit_table(self):
        return "sd_dms_folder"

    def export_data(self, fields_to_export):
        # Questa function viene richiamata tramite l'esportazione dei record (csv/xlsx), non fa altro che passare
        # un context export_document_data che andrà a disabilitare il compute del campo content in fase di esportazione
        if "content" not in fields_to_export:
            context = dict(
                self.env.context,
                export_document_data=True
            )
            self.env.context = context

        return super(Protocollo, self).export_data(fields_to_export)