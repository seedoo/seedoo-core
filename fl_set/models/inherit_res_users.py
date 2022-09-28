# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = "res.users"

    fl_set_set_ids = fields.Many2many(
        string="Set",
        comodel_name="fl.set.set",
        relation="fl_set_set_res_users_rel",
        column1="user_id",
        column2="set_id"
    )

    is_online = fields.Boolean(
        string="Online",
        compute="_compute_presence_state",
    )

    count_user_set = fields.Integer(
        string="Count User with set",
        compute="_compute_count_user_set",
        readonly=True
    )

    @api.depends('fl_set_set_ids')
    def _compute_count_user_set(self):
        for rec in self:
            rec.count_user_set = len(rec.fl_set_set_ids)

    @api.depends('im_status')
    def _compute_presence_state(self):
        for user in self:
            if user.im_status == 'online':
                user.is_online = True
            elif user.im_status == 'offline':
                user.is_online = False
            else:
                user.is_online = False
