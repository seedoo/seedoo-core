from odoo import api, fields, models


class ResUsers(models.Model):

    _inherit = "res.users"

    account_permission_ids = fields.One2many(
        "fl.mail.client.account.permission",
        "user_id",
        string="Account Permissions",
        readonly=True
    )