# Copyright 2020-2022 Flosslab S.r.l.
# Copyright 2017-2019 MuK IT GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, fields, api
from odoo.addons.fl_partner_pa.models.res_partner_digital_domicile import SELECTION_EMAIL_ADDRESS_TYPE


class ContactDigitalDomicile(models.Model):
    _name = "sd.dms.contact.digital.domicile"
    _description = "Contact digital domicile"
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
        required=True,
        default="pec_mail"
    )

    email_address = fields.Char(
        string="PEC mail address",
        required=True
    )

    @api.model
    def get_values_partner_contact_digital_domicile(self, digital_domicile):
        values = {
            "type": digital_domicile.type,
            "email_address": digital_domicile.email_address
        }
        return values