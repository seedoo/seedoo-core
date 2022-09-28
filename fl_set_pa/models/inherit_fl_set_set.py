from odoo import models, fields, api
from odoo.exceptions import UserError

SET_TYPE_SELECTION = [
    ("aoo", "AOO"),
    ("uo", "UO")
]


class Set(models.Model):
    _inherit = "fl.set.set"

    set_type = fields.Selection(
        selection_add=SET_TYPE_SELECTION,
        ondelete={
            'aoo': 'set default',
            'uo': 'set default',
        }
    )

    aoo_id = fields.Many2one(
        string="AOO",
        comodel_name="fl.set.set",
        domain="[('company_id','=', company_id),('set_type','=','aoo')]"
    )

    cod_aoo = fields.Char(
        string="Codice AOO"
    )

    cod_ou = fields.Char(
        string="Codice Univoco Ufficio"
    )

    street = fields.Char(
        string="Indirizzo"
    )

    street2 = fields.Char(
        string="Indirizzo 2"
    )

    city = fields.Char(
        string="Città"
    )

    state_id = fields.Many2one(
        string="Provincia",
        comodel_name="res.country.state"
    )

    zip = fields.Char(
        string="CAP"
    )

    country_id = fields.Many2one(
        string="Nazione",
        comodel_name="res.country"
    )

    parent_set_aoo_id = fields.Many2one(
        string="AOO parent_set_id",
        related="parent_set_id.aoo_id"
    )

    uo_responsabile_id = fields.Many2one(
        string="Responsabile",
        comodel_name="res.partner",
    )

    aoo_responsabile_gestione_documentale_id = fields.Many2one(
        string="Responsabile Gestione Documentale",
        comodel_name="res.users"
    )

    aoo_responsabile_conservazione_documentale_id = fields.Many2one(
        string="Responsabile Conservazione Documentale",
        comodel_name="res.users"
    )

    @api.onchange("set_type")
    def _onchange_set_type(self):
        if self.set_type == "aoo":
            self.user_ids = [(6, 0, [])]

    @api.onchange("company_id")
    def _onchange_company_id(self):
        super(Set, self)._onchange_company_id()
        if self._origin.id and self.browse(self._origin.id).company_id != self.company_id:
            if self.search_count([("aoo_id", "=", self._origin.id)]) > 0:
                return self._warning_company_error_message()

    def _get_field_to_reset(self):
        field_list = super(Set, self)._get_field_to_reset()
        field_list.append("aoo_id")
        return field_list

    @api.model
    def create(self, vals):
        self._set_aoo_id_in_vals(
            vals,
            vals.get("parent_set_id", False)
        )
        return super(Set, self).create(vals)

    def write(self, vals):
        self._set_aoo_id_in_vals(
            vals,
            vals.get("parent_set_id", False)
        )
        res = super(Set, self).write(vals)
        # Al cambio della company di un set:
        # se il relativo set è di tipo AOO ricerco tutte le UO che hanno la AOO associata e ne cambio la company
        # se il set è di tipo standard o UO per ogni set in child_set_ids setto la nuova company
        if vals.get("company_id", False) and self.set_type == "aoo":
            uo_list = self.search([("aoo_id", "=", self.id)])
            for uo in uo_list:
                uo.company_id = self.company_id
        return res

    @api.model
    def _set_aoo_id_in_vals(self, vals, parent_set_id):
        if not parent_set_id:
            return
        parent_set = self.search([("id", "=", parent_set_id)])
        if not parent_set or not parent_set.aoo_id:
            return
        vals["aoo_id"] = parent_set.aoo_id.id

    @api.constrains("set_type")
    def _check_aoo_domain(self):
        for rec in self:
            if rec._get_aoo_result():
                raise UserError("Una AOO è già esistente!")

    def _get_aoo_result(self):
        return self.set_type == "aoo" and self.search_count([("set_type", "=", "aoo")]) > 1