# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountPermission(models.Model):

    _name = "fl.mail.client.account.permission"
    _description = "Account Permission"
    _order = "create_date DESC"

    name = fields.Char(
        string="Name",
        compute="_compute_name",
    )

    account_id = fields.Many2one(
        "fl.mail.client.account",
        string="Account",
        ondelete = "cascade",
        required=True,
        index=True
    )

    account_user_ids = fields.Many2many(
        "res.users",
        string="Account Users",
        compute="_compute_account_user_ids",
    )

    user_id = fields.Many2one(
        "res.users",
        string="User",
        ondelete="cascade",
        required=True,
    )

    user_account_ids = fields.Many2many(
        "fl.mail.client.account",
        string="User Accounts",
        compute="_compute_user_account_ids",
    )

    show_inbox_mails = fields.Boolean(
        string="Show Inbox Mails",
    )

    show_outgoing_mails = fields.Boolean(
        string="Show Outgoing Mails",
    )

    use_outgoing_server = fields.Boolean(
        string="Use Outgoing Mail Servers",
    )

    _sql_constraints = [
        (
            "unique_account_permission",
            "unique(account_id, user_id)",
            _("There can only be one user permission for each account")
        )
    ]

    @api.depends("account_id", "user_id")
    def _compute_name(self):
        for account_permission in self:
            account_permission.name = "%s - %s" % (account_permission.account_id.name, account_permission.user_id.name)

    @api.depends("account_id")
    def _compute_account_user_ids(self):
        for account_permission in self:
            user_ids = []
            if account_permission.account_id:
                permission_list = self.search([
                    ("account_id", "=", account_permission.account_id.id)
                ])
                for permission in permission_list:
                    user_ids.append(permission.user_id.id)
            account_permission.account_user_ids = user_ids

    @api.depends("user_id")
    def _compute_user_account_ids(self):
        for account_permission in self:
            account_ids = []
            if account_permission.user_id:
                permission_list = self.search([
                    ("user_id", "=", account_permission.user_id.id)
                ])
                for permission in permission_list:
                    account_ids.append(permission.account_id.id)
            account_permission.user_account_ids = account_ids