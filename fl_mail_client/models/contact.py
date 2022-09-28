# -*- coding: utf-8 -*-

from odoo import fields, models, tools, api, _
from odoo.exceptions import UserError


class Contact(models.Model):

    _name = "fl.mail.client.contact"
    _description = "Contact"
    _order = "email"
    _auto = False

    # campo calcolato dalla id del partner moltiplicato per 10: in questo modo si ottiene un id univoco nel caso in cui
    # uno stesso partner abbia più indirizzi email
    id = fields.Integer(
        string="ID",
        readonly=True
    )

    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        readonly=True
    )

    name = fields.Char(
        string="Name"
    )

    type = fields.Char(
        string="Address Type",
        default="contact"
    )

    is_company = fields.Boolean(
        string="Is a Company",
        default=False
    )

    company_type = fields.Selection(
        string="Company Type",
        selection=[("person", "Individual"), ("company", "Company")],
        compute="_compute_company_type",
        inverse="_write_company_type"
    )

    parent_id = fields.Many2one(
        "res.partner",
        string="Related Company"
    )

    function = fields.Char(
        string="Job Position"
    )

    email = fields.Char(
        string="Email"
    )

    phone = fields.Char(
        string="Phone"
    )

    mobile = fields.Char(
        string="Mobile"
    )

    def _select(self):
        select_query = """
            SELECT id*10 AS id,
                   email AS email,
                   id AS partner_id,
                   CONCAT(name, ' <', email, '>') AS name,
                   type AS type,
                   is_company AS is_company,
                   parent_id AS parent_id,
                   function AS function,
                   phone AS phone,
                   mobile AS mobile
            FROM res_partner
            WHERE active = TRUE AND 
                  email IS NOT NULL
        """
        return select_query

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE view %s as %s
        """ % (self._table, self._select()))

    @api.depends("is_company")
    def _compute_company_type(self):
        for contact in self:
            contact.company_type = "company" if contact.is_company else "person"

    def _write_company_type(self):
        for contact in self:
            contact.is_company = contact.company_type == "company"

    @api.model
    def create(self, vals):
        partner_obj = self.env["res.partner"]
        partner = partner_obj.create(vals)
        contact = self.search([("partner_id", "=", partner.id)])
        return contact

    @api.model
    def name_create(self, name):
        raise UserError(_("Couldn't create contact without email address!"))