# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp import api, fields, models

class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = ['res.partner', 'mail.thread']

    name = fields.Char(track_visibility='onchange')
    vat = fields.Char(track_visibility='onchange')
    street = fields.Char(track_visibility='onchange')
    street2 = fields.Char(track_visibility='onchange')
    zip = fields.Char(track_visibility='onchange')
    city = fields.Char(track_visibility='onchange')
    state_id = fields.Many2one(track_visibility='onchange')
    country_id = fields.Many2one(track_visibility='onchange')
    category_id = fields.Many2many(track_visibility='onchange')
    phone = fields.Char(track_visibility='onchange')
    mobile = fields.Char(track_visibility='onchange')
    fax = fields.Char(track_visibility='onchange')
    email = fields.Char(track_visibility='onchange')
    pec_mail = fields.Char(track_visibility='onchange')
    website = fields.Char(track_visibility='onchange')
    function = fields.Char(track_visibility='onchange')
    title = fields.Many2one(track_visibility='onchange')
    comment = fields.Text(track_visibility='onchange')
    lang = fields.Selection(track_visibility='onchange')
    parent_id = fields.Many2one(track_visibility='onchange')
    type = fields.Selection(track_visibility='onchange')
    legal_type = fields.Selection(track_visibility='onchange')
    pa_type = fields.Selection(track_visibility='onchange')
    ident_code = fields.Char(track_visibility='onchange')
    ammi_code = fields.Char(track_visibility='onchange')
    ipa_code = fields.Char(track_visibility='onchange')