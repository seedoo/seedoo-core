# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp import api, fields, models

class Protocollo(models.Model):
    _inherit = 'protocollo.protocollo'

    in_attesa = fields.Boolean(string='In Attesa', compute='_compute_state_assegnazione', store=True, readonly=True)
    preso = fields.Boolean(string='Preso', compute='_compute_state_assegnazione', store=True, readonly=True)
    rifiutato = fields.Boolean(string='Rifiutato', compute='_compute_state_assegnazione', store=True, readonly=True)

    server_sharedmail_id_required = fields.Boolean(string='Server Sharedmail Obbligatorio', compute='_compute_server_sharedmail_id_required', readonly=True)
    server_pec_id_required = fields.Boolean(string='Server PEC Obbligatorio', compute='_compute_server_pec_id_required', readonly=True)

    @api.multi
    @api.depends('registration_date', 'assegnazione_competenza_ids.state')
    def _compute_state_assegnazione(self):
        for protocollo in self:
            if protocollo.registration_date:
                in_attesa = False
                preso = protocollo.preso
                rifiutato = False
                for assegnazione_competenza in protocollo.assegnazione_competenza_ids:
                    if assegnazione_competenza.state == 'assegnato':
                        in_attesa = in_attesa or True
                        preso = preso or False
                        rifiutato = rifiutato or False
                    elif assegnazione_competenza.state == 'preso':
                        in_attesa = in_attesa or False
                        preso = preso or True
                        rifiutato = rifiutato or False
                    elif assegnazione_competenza.state == 'rifiutato':
                        in_attesa = in_attesa or False
                        preso = preso or False
                        rifiutato = rifiutato or True
                protocollo.in_attesa = in_attesa
                protocollo.preso = preso
                protocollo.rifiutato = rifiutato

    @api.multi
    @api.depends('typology')
    def _compute_server_sharedmail_id_required(self):
        for protocollo in self:
            if protocollo.sharedmail and protocollo.type=='out':
                protocollo.server_sharedmail_id_required = True
            else:
                protocollo.server_sharedmail_id_required = False

    @api.multi
    @api.depends('typology')
    def _compute_server_pec_id_required(self):
        for protocollo in self:
            if protocollo.pec and protocollo.type=='out':
                protocollo.server_pec_id_required = True
            else:
                protocollo.server_pec_id_required = False