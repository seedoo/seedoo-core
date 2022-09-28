from odoo import models, fields, api, tools

SELECTION_TIPOLOGIA = [
    ("ufficio", "Ufficio"),
    ("utente", "Utente")
]


class VoceOrganigramma(models.Model):
    _name = "fl.set.voce.organigramma"
    _rec_name = "nome"

    _auto = False

    _description = "Voce Organigramma"

    _set_mask = 1000000

    nome = fields.Char(
        string="Nome",
    )

    nome_completo = fields.Char(
        string="Nome Completo",
        compute="_compute_complete_name"
    )

    tipologia = fields.Selection(
        string="Tipologia",
        selection=SELECTION_TIPOLOGIA
    )

    tipologia_ufficio = fields.Char(
        string="Tipologia Ufficio"
    )

    utente_id = fields.Many2one(
        string="Utente",
        comodel_name="res.users"
    )

    ufficio_id = fields.Many2one(
        string="Ufficio",
        comodel_name="fl.set.set"
    )

    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company"
    )

    parent_id = fields.Many2one(
        string="Padre",
        comodel_name="fl.set.voce.organigramma",
        domain=[("parent_active", "=", True)]
    )

    child_ids = fields.One2many(
        string="Figli",
        comodel_name="fl.set.voce.organigramma",
        inverse_name="parent_id",
    )

    parent_active = fields.Boolean(
        string="Parent Active",
        readonly=True
    )

    path_name = fields.Char(
        string="Path Name",
        readonly=True
    )

    active = fields.Boolean(
        string="Attivo"
    )

    def _compute_complete_name(self):
        for rec in self:
            name = rec.nome
            if rec.parent_id:
                parent_complete_name = rec.parent_id.nome_completo
                name = parent_complete_name + ' / ' + name
            rec.nome_completo = name

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        view_sql = """CREATE VIEW {table} as
            (
                SELECT {view_fields_from_users}
                FROM res_users ut, res_partner rp, fl_set_set_res_users_rel fssrur, fl_set_set fss
                WHERE ut.partner_id = rp.id AND
                      ut.id = fssrur.user_id AND 
                      fssrur.set_id = fss.id
            )
            UNION
            (
                SELECT {view_fields_from_sets}
                FROM fl_set_set uf
            )
        """.format(
            table=self._table,
            view_fields_from_users=self.get_view_fields_from_users(),
            view_fields_from_sets=self.get_view_fields_from_sets()
        )
        self.env.cr.execute(view_sql)

    @api.model
    def get_view_fields_from_users(self):
        view_fields = """
                fssrur.set_id*{set_mask} + ut.id AS id,
                rp.name AS nome,
                'utente' AS tipologia,
                ut.id AS utente_id,
                NULL AS ufficio_id,
                NULL AS tipologia_ufficio,
                ut.active AS active,
                CONCAT(fss.path_name, ' / ', rp.name) as path_name,                 
                fss.parent_active AS parent_active,
                fssrur.set_id*{set_mask} AS parent_id,
                fss.company_id AS company_id
            """.format(
            set_mask=self._set_mask
        )
        return view_fields

    @api.model
    def get_view_fields_from_sets(self):
        view_fields = """
                uf.id*{set_mask} AS id,
                uf.name AS nome,
                'ufficio' AS tipologia,
                NULL AS utente_id,
                uf.id AS ufficio_id,
                uf.set_type AS tipologia_ufficio,
                uf.active AS active,
                uf.path_name as path_name,
                uf.parent_active AS parent_active,
                uf.parent_set_id*{set_mask} AS parent_id,
                uf.company_id AS company_id
            """.format(
            set_mask=self._set_mask
        )
        return view_fields

    @api.model
    def get_domain_utente(self, field_dict=False):
        if field_dict and "company_id" in field_dict:
            company_id = field_dict["company_id"][0]
        elif self.env.context.get("company_id", False):
            company_id = self.env.context.get("company_id")
        else:
            company_id = self.env.company.id
        return [
            "&", "&", "&",
            ("tipologia", "=", "utente"),
            ("parent_id", "!=", False),
            ("parent_active", "=", True),
            ("company_id", "=", company_id)
        ]

    @api.model
    def get_domain_ufficio(self, field_dict=False):
        if field_dict and "company_id" in field_dict:
            company_id = field_dict["company_id"][0]
        elif self.env.context.get("company_id", False):
            company_id = self.env.context.get("company_id")
        else:
            company_id = self.env.company.id
        return [
            "&", "&",
            ("tipologia", "=", "ufficio"),
            ("parent_active", "=", True),
            ("company_id", "=", company_id)
        ]

    def name_get(self):
        res = super(VoceOrganigramma, self).name_get()
        for record in self:
            display_name = record.env.context.get("display_field", False)
            # Se valorizzato il context con display_field e quest'ultimo esiste nel record verifico che nella super
            # siano presenti dei valori mi recupero quello con lo stesso id del record e aggiorno il name altrimenti se
            # non presenti faccio un append del valore
            if display_name and display_name in record and record[display_name]:
                name = record[display_name]
                index = [i for i, r in enumerate(res) if r and r[0] == record.id]
                if index:
                    res[index[0]] = (record.id, name)
                else:
                    res.append((record.id, name))
        return res
