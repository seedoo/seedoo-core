# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, exceptions, fields, models, modules


class Partner(models.Model):
    _name = 'res.partner'
    _inherit = ['res.partner']

    is_fl_mail_reader_writer = fields.Boolean(string='Is fl mail reader and writer', compute='_compute_is_fl_mail_user')
    has_compose_permission = fields.Boolean(string='As compose permission', compute='_compute_has_compose_permission')

    @api.depends("user_id")
    def _compute_is_fl_mail_user(self):
        for user in self:
            user.is_fl_mail_reader_writer = user.user_has_groups('fl_mail_client.group_fl_mail_client_user_base')

    @api.depends("user_id")
    def _compute_has_compose_permission(self):
        for user in self:
            user.has_compose_permission = user.user_has_groups("fl_mail_client.group_fl_mail_client_user_advanced")

    def mail_partner_format(self):
        res = super().mail_partner_format()
        res["is_fl_mail_reader_writer"] = self.is_fl_mail_reader_writer
        res["has_compose_permission"] = self.has_compose_permission
        return res
