from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

SELECTION_ASSEGNATARIO_TIPOLOGIA = [
    ("ufficio", "Ufficio"),
    ("utente", "Utente")
]

SELECTION_TIPOLOGIA = [
    ("competenza", "Competenza"),
    ("conoscenza", "Conoscenza")
]

SELECTION_STATE = [
    ("assegnato", "Assegnato"),
    ("preso_in_carico", "Preso in carico"),
    ("letto_co", "Letto"),
    ("rifiutato", "Rifiutato"),
    ("letto_cc", "Letto"),
    ("lavorazione_completata", "Lavorazione completata")
]


class Assegnazione(models.Model):
    _name = "sd.protocollo.assegnazione"
    _description = "Assegnazione"
    _order = 'tipologia,create_date'
    _rec_name = "nome"

    nome = fields.Char(
        string="Assegnazione"
    )

    protocollo_id = fields.Many2one(
        string="Protocollo",
        comodel_name="sd.protocollo.protocollo",
        ondelete="cascade"
    )

    assegnatario_id = fields.Many2one(
        string="Assegnatario",
        comodel_name="fl.set.voce.organigramma",
        domain=[("parent_active", "=", True)]
    )

    assegnatario_nome = fields.Char(
        string="Assegnatario"
    )

    assegnatario_tipologia = fields.Selection(
        string="Tipologia",
        selection=SELECTION_ASSEGNATARIO_TIPOLOGIA,
        index=True
    )

    assegnatario_utente_id = fields.Many2one(
        string="Assegnatario Utente",
        comodel_name="res.users",
        index=True
    )

    assegnatario_utente_parent_id = fields.Many2one(
        string="Assegnatario Utente Padre",
        comodel_name="fl.set.set"
    )

    assegnatario_ufficio_id = fields.Many2one(
        string="Assegnatario Ufficio",
        comodel_name="fl.set.set",
        index=True
    )

    assegnatario_ufficio_parent_id = fields.Many2one(
        string="Assegnatario Ufficio Padre",
        comodel_name="fl.set.set"
    )

    tipologia = fields.Selection(
        string="Assegnazione",
        selection=SELECTION_TIPOLOGIA,
        index=True
    )

    data = fields.Datetime(
        string="Data ultima operazione"
    )

    state = fields.Selection(
        string="Stato",
        selection=SELECTION_STATE,
        index=True
    )

    state_competenza = fields.Selection(
        string="State Competenza",
        selection=SELECTION_STATE,
        compute="_compute_state_cc_co"
    )

    state_conoscenza = fields.Selection(
        string="Stato Conoscenza",
        selection=SELECTION_STATE,
        compute="_compute_state_cc_co"
    )

    messaggio = fields.Text(
        string="Messaggio"
    )

    presa_in_carico = fields.Boolean(
        string="Presa In Carico",
        default=False
    )

    presa_in_carico_attuale = fields.Boolean(
        string="Taken in charge now",
        default=False
    )

    assegnatore_id = fields.Many2one(
        string="Assegnatore",
        comodel_name="res.users"
    )

    assegnatore_nome = fields.Char(
        string="Assegnatore Nome",
    )

    assegnatore_nome_completo = fields.Char(
        string="Assegnatore Nome Completo",
    )

    assegnatore_parent_id = fields.Many2one(
        string="Assegnatore Padre",
        comodel_name="fl.set.set"
    )

    parent_id = fields.Many2one(
        string="Padre",
        comodel_name="sd.protocollo.assegnazione",
        ondelete="cascade"
    )

    child_ids = fields.One2many(
        string="Figli",
        comodel_name="sd.protocollo.assegnazione",
        inverse_name="parent_id"
    )

    motivazione_rifiuto = fields.Text(
        string="Motivazione Rifiuto"
    )

    archivio_id = fields.Many2one(
        string="Archivio",
        comodel_name="sd.protocollo.archivio",
        related="protocollo_id.archivio_id"
    )

    @api.model
    def get_default_assegnatore_ufficio(self, protocollo_id):
        if not protocollo_id:
            return False

        set_list = self.env["fl.set.set"].search([("can_used_to_protocol", "=", True)])
        if len(set_list) == 0:
            return False
        if len(set_list) == 1:
            return set_list[0]

        protocollo = self.env["sd.protocollo.protocollo"].browse(protocollo_id)

        # se il protocollo è stato registrato e l'utente corrente ha messo in lavorazione il protocollo, allora l'ufficio
        # dell'assegnatore è lo stesso dell'assegnatario per competenza
        if protocollo.data_registrazione:
            assegnazione_list = self.search([
                ("protocollo_id", "=", protocollo_id),
                ("tipologia", "=", "competenza"),
                ("state", "=", "preso_in_carico"),
                ("assegnatario_utente_id", "=", self.env.uid)
            ])
            if len(assegnazione_list) > 1:
                return False
            if len(assegnazione_list) == 1:
                return assegnazione_list[0].assegnatario_utente_parent_id

        # se l'utente appartiene all'ufficio di protocollazione, si usa quest'ultimo come ufficio dell'assegnatore
        if protocollo.protocollatore_ufficio_id and self.env.uid in protocollo.protocollatore_ufficio_id.user_ids.ids:
            return protocollo.protocollatore_ufficio_id

        return False

    @api.model
    def crea_assegnazione(self, protocollo_id, assegnatario_id, assegnatore_id, assegnatore_ufficio_id, tipologia,
                          parent_id=False, values={}):
        assegnatario_obj = self.env["fl.set.voce.organigramma"]
        assegnatario = assegnatario_obj.browse(assegnatario_id)

        user_obj = self.env["res.users"]
        assegnatore = user_obj.browse(assegnatore_id)
        assegnatore_nome = assegnatore.partner_id.name

        set_obj = self.env["fl.set.set"]
        assegnatore_ufficio = set_obj.browse(assegnatore_ufficio_id)
        assegnatore_nome_completo = "%s / %s" % (assegnatore_ufficio.get_path(), assegnatore_nome)

        vals = dict(values or {})
        vals["nome"] = self._get_nome(tipologia, assegnatario, values)
        vals["protocollo_id"] = protocollo_id
        vals["assegnatario_id"] = assegnatario.id
        vals["assegnatario_nome"] = assegnatario.nome_completo
        vals["assegnatario_tipologia"] = assegnatario.tipologia
        vals["tipologia"] = tipologia
        vals["data"] = fields.Datetime.now()
        vals["state"] = "assegnato"
        vals["assegnatore_id"] = assegnatore.id
        vals["assegnatore_nome"] = assegnatore_nome
        vals["assegnatore_nome_completo"] = assegnatore_nome_completo
        vals["assegnatore_parent_id"] = assegnatore_ufficio.id
        vals["parent_id"] = parent_id

        if assegnatario.tipologia == "utente":
            vals["assegnatario_utente_id"] = assegnatario.utente_id.id
            vals["assegnatario_utente_parent_id"] = assegnatario.parent_id.ufficio_id.id if assegnatario.parent_id.ufficio_id else False
        if assegnatario.tipologia == "ufficio":
            vals["assegnatario_ufficio_id"] = assegnatario.ufficio_id.id
            vals["assegnatario_ufficio_parent_id"] = assegnatario.parent_id.ufficio_id.id if assegnatario.parent_id.ufficio_id else False

        assegnazione = self.create(vals)
        # self.notifica_assegnazione(assegnazione)
        # il metodo refresh serve per invalidare la cache degli id memorizzati nell'oggetto assegnatario_obj: se non si
        # invalida la cache ad ogni creazione di un'assegnazione, si ricalcola il name anche per le assegnazione create
        # in precedenza, rallentando notevolmente il processo
        # assegnatario_obj.refresh(cr, uid)
        return assegnazione

    @api.model
    def crea_assegnazioni(self, protocollo_id, assegnatario_ids,
                          assegnatore_id, assegnatore_ufficio_id, tipologia, values={}):
        messaggi = values.pop("messaggi") if "messaggi" in values else {}
        for assegnatario_id in assegnatario_ids:
            assegnazione_values = dict(values or {})
            if messaggi:
                messaggio = messaggi.get(assegnatario_id, False)
                assegnazione_values.update({"messaggio": messaggio})
            self.crea_assegnazione(
                protocollo_id,
                assegnatario_id,
                assegnatore_id,
                assegnatore_ufficio_id,
                tipologia,
                False,
                assegnazione_values
            )

    @api.model
    def verifica_assegnazione_competenza(self, assegnatario_ids):
        if len(assegnatario_ids) > 1:
            raise ValidationError(_("Non si possono inserire più assegnatari per competenza!"))

    @api.model
    def get_assegnatario_to_create_ids(self, assegnatario_ids, old_assegnatario_ids, assegnatario_to_replace_ids):
        if assegnatario_to_replace_ids:
            return assegnatario_ids
        else:
            return list(set(assegnatario_ids) - set(old_assegnatario_ids))

    @api.model
    def get_assegnatario_to_unlink_ids(self, assegnatario_ids, old_assegnatario_ids, assegnatario_to_replace_ids):
        if assegnatario_to_replace_ids:
            return assegnatario_to_replace_ids
        else:
            return list(set(old_assegnatario_ids) - set(assegnatario_ids))

    @api.model
    def get_next_state_list(self, state):
        if state in ["assegnato"]:
            return ["preso_in_carico", "rifiutato", "letto_co", "letto_cc", "lavorazione_completata"]
        if state in ["preso_in_carico", "letto_cc", "letto_co"]:
            return ["lavorazione_completata"]
        if state in ["lavorazione_completata"]:
            return ["preso_in_carico", "letto_co", "letto_cc"]
        return []

    @api.depends("state")
    def _compute_state_cc_co(self):
        for rec in self:
            rec.state_competenza = rec.state
            rec.state_conoscenza = rec.state

    @api.model
    def _get_nome(self, tipologia, assegnatario, values):
        tipologia_nome = tipologia
        for tipologia_value in SELECTION_TIPOLOGIA:
            if tipologia_value[0] == tipologia:
                tipologia_nome = tipologia_value[1]
        return "%s - %s" % (tipologia_nome, assegnatario.nome_completo)
