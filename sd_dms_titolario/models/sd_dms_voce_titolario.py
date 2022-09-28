from odoo import models, fields, api

SELECTION_CLASS_TYPE = [
    ('titolo', 'Titolo'),
    ('classe', 'Classe'),
    ('sottoclasse', 'Sottoclasse')
]


class VoceTitolario(models.Model):
    _name = "sd.dms.titolario.voce.titolario"
    _description = "Voce Titolario"

    _parent_field = "parent_id"
    _parent_model = "sd.dms.titolario.voce.titolario"

    _order = "sequence"
    _rec_name = "complete_name"

    name = fields.Char(
        string="Nome",
        required=True,
        readonly=False
    )

    code = fields.Char(
        string="Codice",
        required=True
    )

    complete_name = fields.Char(
        string="Nome Completo",
        compute="_compute_complete_name",
        readonly=True,
        store=True
    )

    path_name = fields.Char(
        string="Path Name",
        compute="_compute_path_name",
        readonly=True,
        store=True
    )

    sequence = fields.Integer(
        string="sequence"
    )

    class_type = fields.Selection(
        string="Tipologia",
        selection=SELECTION_CLASS_TYPE,
        required=True
    )

    titolario_id = fields.Many2one(
        string="Titolario",
        comodel_name="sd.dms.titolario.titolario",
        required=True
    )

    parent_id = fields.Many2one(
        string="Voce Titolario Padre",
        comodel_name="sd.dms.titolario.voce.titolario",
        required=False,
        domain="[('titolario_id','=',titolario_id), ('parent_active','=',True), ('titolario_company_id','=', titolario_company_id)]",
    )

    parent_path_name = fields.Char(
        string="Parent path",
        related="parent_id.path_name"
    )

    child_ids = fields.One2many(
        string="Voci Titolario",
        comodel_name="sd.dms.titolario.voce.titolario",
        inverse_name="parent_id",
        required=False,
        readonly=True
    )

    description = fields.Text(
        string="Descrizione"
    )

    active = fields.Boolean(
        string="Active",
        default=True
    )

    parent_active = fields.Boolean(
        string="Parent Active",
        compute="_compute_parent_active",
        readonly=True,
        store=True
    )

    titolario_company_id = fields.Many2one(
        string="Company",
        related="titolario_id.company_id"
    )

    @api.depends("name", "code")
    def _compute_complete_name(self):
        for rec in self:
            nome_completo = False
            if rec.code:
                nome_completo = rec.code + ' - ' + rec.name
            elif rec.name:
                nome_completo = rec.name
            rec.complete_name = nome_completo

    def _path_name_get(self, voce_titolario_id):
        name = voce_titolario_id.name
        if voce_titolario_id.parent_id:
            name = self._path_name_get(voce_titolario_id.parent_id) + " / " + voce_titolario_id.name
        return name if name else ""

    @api.depends("name", "code", "parent_id", "parent_id.path_name")
    def _compute_path_name(self):
        for rec in self:

            name = rec.name
            if rec.parent_id:
                name = self._path_name_get(rec.parent_id) + " / " + rec.name
            if rec.code:
                name = rec.code + " - " + name

            rec.path_name = name

    @api.depends("active", "parent_id", "parent_id.active", "parent_id.parent_active")
    def _compute_parent_active(self):
        for rec in self:
            parent_active = False
            if rec.active:
                if rec.parent_id.active and rec.parent_id.parent_active or not rec.parent_id:
                    parent_active = True

            rec.parent_active = parent_active
