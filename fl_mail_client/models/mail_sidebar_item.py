from odoo import fields, models, _


class MailSidebarItem(models.Model):
    _name = "mail.sidebar.item"
    _description = "Mail sidebar item email client"

    name = fields.Char(
        string="Name",
    )
