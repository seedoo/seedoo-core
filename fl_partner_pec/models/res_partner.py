# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartner(models.Model):

    _inherit = "res.partner"

    pec_mail = fields.Char(
        string="PEC Mail"
    )