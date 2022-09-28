from odoo import models, fields, api, tools, _


class Account(models.Model):
    _name = "fl.mail.client.account"
    _description = "Account"
    _order = "create_date DESC"

    name = fields.Char(
        string="Name",
        compute="_compute_name",
    )

    description = fields.Char(
        string="Name",
        required=True
    )

    email = fields.Char(
        string="Email",
        required=True
    )

    fetchmail_server_id = fields.Many2one(
        "fetchmail.server",
        string="Inbox Mail Server",
    )

    ir_mail_server_id = fields.Many2one(
        "ir.mail_server",
        string="Outgoing Mail Server",
    )

    use_outgoing_server = fields.Boolean(
        compute="_compute_use_outgoing_server",
        search="_search_use_outgoing_server",
        string="Use Outgoing Server"
    )

    email_received_count = fields.Integer(
        string="Email Received",
        compute="_compute_email_received_count"
    )

    email_sent_count = fields.Integer(
        string="Email Sent",
        compute="_compute_email_sent_count"
    )

    account_permission_ids = fields.One2many(
        "fl.mail.client.account.permission",
        "account_id",
        string="Account Permissions",
    )

    account_permission_count = fields.Integer(
        "# Account Permissions",
        compute="_compute_account_permission_count",
    )

    def _compute_email_received_count(self):
        mail_obj = self.env["mail.mail"]
        for account in self:
            account.email_received_count = mail_obj.search_count(
                [("account_id", "=", account.id), ('direction', '=', 'in')]
            )

    def _compute_email_sent_count(self):
        mail_obj = self.env["mail.mail"]
        for account in self:
            account.email_sent_count = mail_obj.search_count(
                [("account_id", "=", account.id), ('direction', '=', 'out')]
            )

    @api.depends("account_permission_ids")
    def _compute_account_permission_count(self):
        for account in self:
            account.account_permission_count = len(account.account_permission_ids)

    @api.depends("description", "email")
    def _compute_name(self):
        for account in self:
            if self._context.get("display_with_email") and account.description and account.email:
                account.name = tools.formataddr((account.description, account.email))
            else:
                account.name = account.description

    def _compute_use_outgoing_server(self):
        if self.env.user.has_group("fl_mail_client.group_fl_mail_client_administrator"):
            for mail in self:
                mail.mail_client_use = True
        else:
            for mail in self:
                if mail.id in self._query_use_outgoing_server():
                    mail.mail_client_use = True

    def _search_use_outgoing_server(self, operator, value):
        if self.env.user.has_group("fl_mail_client.group_fl_mail_client_administrator"):
            return []
        return [("id", "in", self._query_use_outgoing_server())]

    @api.model
    def _query_use_outgoing_server(self):
        cr = self.env.cr
        cr.execute("""
            SELECT fmca.id
            FROM fl_mail_client_account fmca, fl_mail_client_account_permission fmcap 
            WHERE fmca.id = fmcap.account_id AND 
                  fmcap.user_id = %s AND 
                  fmcap.use_outgoing_server = TRUE
        """, (self.env.uid,))
        ids = [result[0] for result in cr.fetchall()]
        return ids

    @api.onchange("email")
    def _onchange_email(self):
        partner_obj = self.env["res.partner"]
        if not self.email:
            return
        email = {
            "email": self.email
        }
        partner_obj.check_email_validity(email)

    def action_show_account_permissions(self):
        self.ensure_one()
        return {
            "name": _("Account Permissions"),
            "view_mode": "tree,form",
            "res_model": "fl.mail.client.account.permission",
            "type": "ir.actions.act_window",
            "target": "current",
            "domain": [("account_id", "=", self.id)],
            "context": {
                "default_account_id": self.id,
            }
        }
