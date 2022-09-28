from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

SELECTION_STATE = [
    ("bozza", "Draft"),
    ("aperto", "Open"),
    ("chiuso", "Close")
]

SELECTION_TIPOLOGIA = [
    ("fascicolo", "Dossier"),
    ("sottofascicolo", "Sub-Dossier"),
    ("inserto", "Insert")
]

SELECTION_CATEGORIA = [
    ("affare", "Deal"),
    ("attivita", "Activity"),
    ("persona_fisica", "Physical Person"),
    ("persona_giuridica", "Legal Person"),
    ("procedimento", "Administrative Procedure"),
]


class Fascicolo(models.Model):
    _name = "sd.fascicolo.fascicolo"
    _inherit = ["mail.thread", "fl.security"]
    _description = "Fascicolo"
    _rec_name = "nome"
    _order = "nome asc, id asc"

    _parent_field = "parent_id"
    _parent_model = "sd.fascicolo.fascicolo"


    nome = fields.Char(
        string="Nome",
        required=True,
        compute="_compute_nome",
        store=True
    )

    codice_sequenza = fields.Integer(
        string="Sequence Code",
        compute="_compute_sequence_code",
        store=True
    )

    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        default=lambda self: self.env.company.id
    )

    state = fields.Selection(
        string="Stato",
        selection=SELECTION_STATE,
        default=SELECTION_STATE[0][0],
        readonly=True
    )

    oggetto = fields.Char(
        string="Oggetto",
        required=True
    )

    voce_titolario_id = fields.Many2one(
        string="Classificazione",
        comodel_name="sd.dms.titolario.voce.titolario",
        domain="[('titolario_id.active','=',True), ('titolario_id.state','=',True), ('parent_active', '=', True)]"
    )

    parent_voce_titolario_id = fields.Many2one(
        string="Parent Classificazione",
        comodel_name="sd.dms.titolario.voce.titolario",
        related="parent_id.voce_titolario_id"
    )

    parent_codice_sequenza = fields.Integer(
        string="Parent Sequence Code",
        related="parent_id.codice_sequenza"
    )

    tipologia = fields.Selection(
        string="Tipologia",
        selection=SELECTION_TIPOLOGIA,
        default=SELECTION_TIPOLOGIA[0][0],
        required=True
    )

    categoria = fields.Selection(
        string="Categoria",
        selection=SELECTION_CATEGORIA,
        required=True
    )

    anno = fields.Char(
        string="Anno",
        readonly=True
    )

    data_apertura = fields.Datetime(
        string="Data Apertura",
        readonly=True
    )

    data_chiusura = fields.Datetime(
        string="Data Chiusura",
        readonly=True
    )

    parent_id_domain = fields.Char(
        string="Parent domain",
        compute="_compute_parent_id_domain",
        readonly=True
    )

    parent_id = fields.Many2one(
        string="Padre",
        comodel_name="sd.fascicolo.fascicolo",
        ondelete="cascade",
        domain="[('tipologia', '=', parent_id_domain),('company_id', '=', company_id)]"
    )

    child_ids = fields.One2many(
        string="Child",
        comodel_name="sd.fascicolo.fascicolo",
        inverse_name="parent_id",
        readonly=True
    )

    sottofascicolo_child_ids = fields.One2many(
        string="Sottofascicolo Figli",
        comodel_name="sd.fascicolo.fascicolo",
        inverse_name="parent_id",
        domain="[('tipologia', '=', 'sottofascicolo'), ('company_id', '=', company_id)]",
        readonly=True
    )

    inserto_child_ids = fields.One2many(
        string="Inserto Figli",
        comodel_name="sd.fascicolo.fascicolo",
        inverse_name="parent_id",
        domain="[('tipologia', '=', 'inserto'), ('company_id', '=', company_id)]",
        readonly=True
    )

    partner_ids = fields.Many2many(
        string="Partner",
        comodel_name="res.partner",
        relation="sd_fascicolo_fascicolo_soggetto_coinvolto_rel",
        column1="fascicolo_id",
        column2="partner_id"
    )

    documento_ids = fields.Many2many(
        string="Documenti",
        comodel_name="sd.dms.document",
        relation="sd_fascicolo_fascicolo_sd_dms_document_rel",
        domain="[('company_id', '=', company_id)]",
        column1="fascicolo_id",
        column2="documento_id"
    )

    documento_ids_count = fields.Integer(
        string="# Documents",
        compute="_compute_documento_ids_count",
    )

    nome_fascicolo = fields.Char(
        string="Nome Fascicolo"
    )

    edificio = fields.Char(
        string="Edificio"
    )

    piano = fields.Char(
        string="Piano"
    )

    stanza = fields.Char(
        string="Stanza"
    )

    posizione = fields.Char(
        string="Posizione"
    )

    acl_ids = fields.Many2many(
        string="Acl",
        comodel_name="sd.fascicolo.fascicolo.acl",
        relation="sd_fascicolo_fascicolo_acl_rel",
        column1="fascicolo_id",
        column2="acl_id",
        domain=[("create_system", "=", False)],
    )

    system_acl_ids = fields.Many2many(
        string="System Acl",
        comodel_name="sd.fascicolo.fascicolo.acl",
        relation="sd_fascicolo_fascicolo_acl_rel",
        column1="fascicolo_id",
        column2="acl_id",
        domain=[("create_system", "=", True)],
        readonly=True
    )

    inherit_acl_ids = fields.Many2many(
        string="Inherit Acl",
        comodel_name="sd.fascicolo.fascicolo.acl",
        relation="sd_fascicolo_fascicolo_acl_inherit_rel",
        column1="fascicolo_id",
        column2="acl_id",
        readonly=True
    )

    sottofascicolo_count = fields.Integer(
        "# Sottofascicoli",
        compute="_compute_sottofascicolo_count",
    )

    inserto_count = fields.Integer(
        "# Inserti",
        compute="_compute_inserto_count",
    )

    amministrazione_titolare_ids = fields.Many2many(
        string="Amministrazione Titolare",
        comodel_name="sd.dms.contact",
        relation="sd_dms_document_contact_amministrazione_titolare_rel",
        domain=[("is_pa", "=", True)],
        readonly=True
    )

    amministrazione_partecipante_ids = fields.Many2many(
        string="Amministrazione Partecipante",
        comodel_name="sd.dms.contact",
        relation="sd_fascicolo_fascicolo_contact_amministrazione_partecipante_rel",
        domain=[("is_pa", "=", True)],
        readonly=True
    )

    soggetto_intestatario_ids = fields.Many2many(
        string="Soggetto Intestatario",
        relation="sd_fascicolo_fascicolo_contact_soggetto_intestatario_rel",
        comodel_name="sd.dms.contact",
        readonly=True
    )

    rup_ids = fields.Many2many(
        string="Responsabile Unico Procedimento",
        readonly=True,
        comodel_name="sd.dms.contact",
        relation="sd_dms_document_contact_rup_rel",
        domain=[
            '|',
            ("company_type", "=", "person"),
            '&',
            ("company_type", "=", "company"), ("contact_pa_name", '!=', False)
        ]
    )

    ufficio_autore_id = fields.Many2one(
        string="Ufficio autore",
        comodel_name="fl.set.set",
        domain="[('user_ids', '=', autore_id)]",
        required=True,
        store=True,
    )

    autore_id = fields.Many2one(
        string="Autore",
        comodel_name="res.users",
        readonly=True,
        default=lambda self: self.env.user.id,
    )

    @api.onchange("autore_id")
    @api.depends("autore_id")
    def _preselect_ufficio_autore_id(self):
        for dossier in self:
            uffici = self.env["fl.set.set"].sudo().search([("user_ids", "=", self.autore_id.id)]).ids
            if len(uffici) == 1:
                dossier.ufficio_autore_id = uffici[0]

    @api.onchange("ufficio_autore_id")
    @api.depends("ufficio_autore_id")
    def _get_acl_ids(self):
        fl_acl_set = self.env["ir.module.module"].sudo().search([
            ("name", "=", "fl_acl_set"),
            ("state", "=", "installed"),
        ])
        if not fl_acl_set or not self.ufficio_autore_id:
            self.acl_ids = []
        else:
            if self.acl_ids:
                for acl in self.acl_ids:
                    if acl.res_model == "fl_set_set" and acl.fl_set_set_id in self.autore_id.fl_set_set_ids:
                        self.acl_ids = [((3, acl.id))]
            self.acl_ids = [((0, 0, {
                "res_model": "fl_set_set",
                "res_id": self.ufficio_autore_id,
                "module_id": self.env["sd.fascicolo.fascicolo.acl"].get_default_module_id().id,
                "create_system": False,
                "perm_create": True,
                "perm_read": True,
                "perm_write": True,
                "perm_delete": False
            }))]

    @api.depends("documento_ids")
    def _compute_documento_ids_count(self):
        dossier_documents_obj = self.env["sd.dms.document"]
        for document in self:
            documento_ids_count = dossier_documents_obj.search([("fascicolo_ids", "=", self.id)], count=True)
            document.documento_ids_count = documento_ids_count

    @api.onchange("voce_titolario_id")
    @api.depends("codice_sequenza", "parent_id", "voce_titolario_id")
    def _compute_sequence_code(self):
        """
        La ricerca del sequence code deve essere fatta mediante query. Se viene fatta mediante il search dell'orm viene
        lanciato un evento di _compute_nome il quale interrompe il corrente calcolo del sequence code generando di
        conseguenza un nome sbagliato
        """
        for rec in self:
            sequence_code = 1
            query_condition = ""
            if rec.parent_id:
                query_condition = """
                    parent_id = {parent_id}
                """.format(parent_id=rec.parent_id.id)
            elif not rec.parent_id and self.voce_titolario_id.id:
                query_condition = """
                    tipologia = 'fascicolo' AND
                    id != {id} AND
                    voce_titolario_id = {voce_titolario_id}
                """.format(
                    id=rec._origin.id if rec._origin.id else 0,
                    voce_titolario_id=self.voce_titolario_id.id
                )
            if query_condition:
                query = """
                    SELECT MAX(codice_sequenza) 
                    FROM sd_fascicolo_fascicolo
                    WHERE {query_condition}
                """.format(
                    query_condition=query_condition
                )
                self.env.cr.execute(query)
                sequence_code_list = [result[0] for result in self.env.cr.fetchall()]
                if sequence_code_list and sequence_code_list[0]:
                    sequence_code = sequence_code_list[0] + 1
            rec.codice_sequenza = sequence_code

    def _get_sequence_from_parent(self, parent, code="", oggetto=""):
        if parent:
            code = "." + str(parent.codice_sequenza) + code
            oggetto = " / " + str(parent.oggetto) + oggetto
            if parent.parent_id:
                code, oggetto = self._get_sequence_from_parent(parent.parent_id, code, oggetto)
        return code, oggetto

    @api.onchange("oggetto")
    @api.depends("oggetto", "codice_sequenza", "voce_titolario_id", "voce_titolario_id.complete_name", "parent_id.nome")
    def _compute_nome(self):
        for rec in self:
            rec.nome = rec._get_nome()
            rec.child_ids._compute_nome()

    def _get_nome(self):
        self.ensure_one()
        if not self.oggetto or not self.voce_titolario_id:
            return self.nome or False
        sequence_code = ".%s" % str(self.codice_sequenza if self.codice_sequenza else 0)
        oggetto = " / %s" % self.oggetto
        if not self.parent_id:
            parent_sequence_code, parent_oggetto = "", ""
        else:
            parent_sequence_code, parent_oggetto = self._get_sequence_from_parent(self.parent_id)
        voce_titolario = self.voce_titolario_id
        path_classificazione = " - " + voce_titolario._path_name_get(voce_titolario)
        if not parent_sequence_code:
            return voce_titolario.code + sequence_code + path_classificazione + oggetto
        return voce_titolario.code + parent_sequence_code + sequence_code + path_classificazione + parent_oggetto + oggetto

    @api.onchange("tipologia")
    def _compute_parent_id_domain(self):
        for record in self:
            parent_id_domain = False
            if record.tipologia:
                if record.tipologia == "sottofascicolo":
                    parent_id_domain = "fascicolo"
                elif record.tipologia == "inserto":
                    parent_id_domain = "sottofascicolo"
            record.parent_id_domain = parent_id_domain

    @api.onchange("tipologia")
    def _onchange_tipologia(self):
        self.ensure_one()
        self.nome = False
        self.voce_titolario_id = False
        if not self.env.context.get("default_tipologia", False):
            self.parent_id = False

    @api.onchange("parent_id")
    def _onchange_parent_id(self):
        if self.tipologia in ["sottofascicolo", "inserto"]:
            voce_titolario_id = False
            if self.parent_voce_titolario_id:
                voce_titolario_id = self.parent_voce_titolario_id
            self.voce_titolario_id = voce_titolario_id

    @api.constrains("company_id", "documento_ids", "voce_titolario_id")
    def _validate_fascicolo(self):
        for fascicolo in self:
            validity = fascicolo._check_company_fascicolo()
            if validity:
                self._raise_error_message(validity)

    def _check_company_fascicolo(self):
        for documento in self.documento_ids:
            if documento.company_id != self.company_id:
                return "L'operazione non può essere completata:\n sono presenti documenti con company diversa da quella del fascicolo"
            if self.voce_titolario_id and self.company_id.id != self.voce_titolario_id.titolario_company_id.id:
                return "L'operazione non può essere completata:\n la company della classificazione è diversa da quella del fascicolo"
        return False

    def _raise_error_message(self, message=False):
        if not message:
            message = "L'operazione non può essere completata"
        raise ValidationError(_(message))

    @api.depends("sottofascicolo_child_ids")
    def _compute_sottofascicolo_count(self):
        for rec in self:
            rec.sottofascicolo_count = len(rec.sottofascicolo_child_ids.ids)

    @api.depends("inserto_child_ids")
    def _compute_inserto_count(self):
        for rec in self:
            rec.inserto_count = len(rec.inserto_child_ids.ids)

    # ----------------------------------------------------------
    # Create, Update, Delete
    # ----------------------------------------------------------

    def init(self):
        # inserimento dell'indice utilizzato nella ricerca della tree e kanban view: è importante inserire sia il l'id
        # che il campo usato nella property _order per definire l'ordinamento di default usato nel modello: i due campi
        # in questione verranno utilizzati nella query di ricerca di visibilità
        sd_fascicolo_fascicolo_id_nome_index = "sd_fascicolo_fascicolo_id_nome_index"
        self.env.cr.execute("""
            SELECT indexname FROM pg_indexes WHERE indexname = '%s'
        """ % sd_fascicolo_fascicolo_id_nome_index)
        if not self.env.cr.fetchone():
            self.env.cr.execute("""
                CREATE INDEX %s ON sd_fascicolo_fascicolo USING btree (id, nome)
            """ % sd_fascicolo_fascicolo_id_nome_index)
        sd_fascicolo_fascicolo_nome_id_index = "sd_fascicolo_fascicolo_nome_id_index"
        self.env.cr.execute("""
            SELECT indexname FROM pg_indexes WHERE indexname = '%s'
        """ % sd_fascicolo_fascicolo_nome_id_index)
        if not self.env.cr.fetchone():
            self.env.cr.execute("""
                CREATE INDEX %s ON sd_fascicolo_fascicolo USING btree (nome, id)
            """ % sd_fascicolo_fascicolo_nome_id_index)

    @api.model
    def create(self, vals_list):
        context = dict(self.env.context,
                       mail_create_nolog=True)
        if "default_parent_id" in context:
            # si elimina dal context il default_parent_id in modo da evitare di generare un eventuale errore nella
            # creazione del message dello storico: infatti anche il modello message ha il campo parent_id, di
            # conseguenza quando il sistema cerca di creare il message "Fascicolo creato", prende come valore di default
            # del parent_id, lo stesso parent_id del fascicolo, il quale se non è presente nella tabella mail_message
            # genera un errore di integrità referenziale
            del context["default_parent_id"]
        rec = super(Fascicolo, self.with_context(context)).create(vals_list)
        if rec.parent_id and rec.tipologia in ["sottofascicolo", "inserto"]:
            rec.parent_id.storico_aggiunta_sottofascicolo_inserto(rec.tipologia, rec.nome)
        rec.storico_crea_fascicolo_sottofascicolo_inserto()
        return rec

    def unlink(self):
        for rec in self:
            if rec.state != "bozza":
                raise ValidationError(_("The dossier cannot be deleted because it is already opened!"))
        if self.parent_id and self.tipologia in ["sottofascicolo", "inserto"]:
            self.parent_id.storico_disassocia_sottofascicolo_inserto(self.tipologia, self.nome)
        return super(Fascicolo, self).unlink()

    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        default["nome"] = _("Copy of %s") % self.nome
        default["documento_ids"] = [(6, 0, [])]
        default["partner_ids"] = [(6, 0, [])]
        default["data_apertura"] = False
        default["data_chiusura"] = False
        default["state"] = "bozza"
        return super(Fascicolo, self).copy(default=default)

    def write(self, values):
        old_parent_id = self.browse(self.id).parent_id
        res = super(Fascicolo, self).write(values)
        if self.parent_id and self.parent_id.id != old_parent_id.id:
            self.parent_id.storico_aggiunta_sottofascicolo_inserto(self.tipologia, self.nome)
            if old_parent_id:
                old_parent_id.storico_disassocia_sottofascicolo_inserto(self.tipologia, self.nome)
        if "voce_titolario_id" in values:
            self._write_voce_titolario_id_in_child_ids(values["voce_titolario_id"])
        return res

    def _write_voce_titolario_id_in_child_ids(self, voce_titolario_id):
        for fascicolo in self:
            for child in fascicolo.child_ids:
                child.codice_sequenza = 0
                child.voce_titolario_id = voce_titolario_id
            fascicolo.child_ids._write_voce_titolario_id_in_child_ids(voce_titolario_id)

    def export_data(self, fields_to_export):
        # Questa function viene richiamata tramite l'esportazione dei record (csv/xlsx), non fa altro che passare
        # un context export_document_data che andrà a disabilitare il compute del campo content in fase di esportazione

        if "content" not in fields_to_export:
            context = dict(
                self.env.context,
                export_document_data=True
            )
            self.env.context = context

        return super(Fascicolo, self).export_data(fields_to_export)

    ####################################################################################################################
    # Security
    ####################################################################################################################

    @api.model
    def skip_security(self):
        result = super(Fascicolo, self).skip_security()
        result = result or self.env.user.has_group("sd_fascicolo.group_sd_fascicolo_manager")
        return result

