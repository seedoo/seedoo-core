from odoo import models, fields, tools


class ResCityItCode(models.Model):
    _name = "res.city.it.code"
    _description = "National city codes"

    national_code = fields.Char(
        string='National code',
        size=4
    )
    cadastre_code = fields.Char(
        string='Belfiore cadastre code (not used anymore)',
        size=4
    )
    province = fields.Char(
        string='Province',
        size=5
    )
    name = fields.Char(
        string='Name'
    )
    notes = fields.Char(
        string='Notes',
        size=4
    )
    national_code_var = fields.Char(
        string='National code variation',
        size=4
    )
    cadastre_code_var = fields.Char(
        string='Cadastre code variation',
        size=4
    )
    province_var = fields.Char(
        string='Province variation',
        size=5
    )
    name_var = fields.Char(
        string='Name variation',
        size=100
    )
    creation_date = fields.Date(
        string='Creation date'
    )
    var_date = fields.Date(
        string='Variation date'
    )

class ResCityItCodeDistinct(models.Model):
    _name = 'res.city.it.code.distinct'
    _description = "National city codes distinct"
    _auto = False

    name = fields.Char('Name', size=100)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            """
            CREATE OR REPLACE VIEW res_city_it_code_distinct AS (
            SELECT name, MAX(id) AS id FROM res_city_it_code
            GROUP BY name)
            """)
