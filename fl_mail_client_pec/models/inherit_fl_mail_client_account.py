# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Account(models.Model):

    _inherit = "fl.mail.client.account"

    pec = fields.Boolean(
        string="PEC",
    )