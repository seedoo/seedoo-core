# Copyright 2020-2022 Flosslab S.r.l.
# Copyright 2017-2019 MuK IT GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, fields, api
from odoo.addons.fl_partner_pa.models.res_partner_email_address import SELECTION_EMAIL_ADDRESS_TYPE


class ContactEmailAddress(models.Model):
    _name = "sd.dms.contact.email.address"
    _description = "Contact e-mail address"
    _rec_name = "email_address"

    contact_id = fields.Many2one(
        string="Contact",
        comodel_name="sd.dms.contact",
        required=True,
        ondelete="cascade",
    )

    type = fields.Selection(
        string="Type",
        selection=SELECTION_EMAIL_ADDRESS_TYPE,
        required=True
    )

    email_address = fields.Char(
        string="E-mail address",
        required=True
    )

    @api.model
    def get_values_partner_contact_email_address(self, email_address):
        values = {
            "type": email_address.type,
            "email_address": email_address.email_address
        }
        return values