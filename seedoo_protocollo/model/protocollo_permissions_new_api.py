# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp import api, fields, models

class Protocollo(models.Model):
    _inherit = 'protocollo.protocollo'

    in_attesa = fields.Boolean(string='In Attesa', compute='_compute_state_assegnazione', store=True, readonly=True)
    preso = fields.Boolean(string='Preso', compute='_compute_state_assegnazione', store=True, readonly=True)
    rifiutato = fields.Boolean(string='Rifiutato', compute='_compute_state_assegnazione', store=True, readonly=True)

    da_assegnare = fields.Boolean(string='Da Assegnare', compute='_compute_da_assegnare', store=True, readonly=True, default=False)

    server_sharedmail_id_required = fields.Boolean(string='Server Sharedmail Obbligatorio', compute='_compute_server_sharedmail_id_required', readonly=True)
    server_pec_id_required = fields.Boolean(string='Server PEC Obbligatorio', compute='_compute_server_pec_id_required', readonly=True)

    @api.multi
    @api.depends('registration_date', 'assegnazione_competenza_ids.state')
    def _compute_state_assegnazione(self):
        for protocollo_each in self:
            protocollo = protocollo_each.with_context(skip_check=True)
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
                protocollo_each.in_attesa = in_attesa
                protocollo_each.preso = preso
                protocollo_each.rifiutato = rifiutato

    @api.multi
    @api.depends('registration_date', 'assegnazione_competenza_ids')
    def _compute_da_assegnare(self):
        for protocollo_each in self:
            protocollo = protocollo_each.with_context(skip_check=True)
            da_assegnare = True
            if protocollo.assegnazione_competenza_ids:
                da_assegnare = False
            protocollo_each.da_assegnare = da_assegnare

    @api.multi
    @api.depends('typology')
    def _compute_server_sharedmail_id_required(self):
        for protocollo_each in self:
            protocollo = protocollo_each.with_context(skip_check=True)
            if protocollo.sharedmail and protocollo.type=='out':
                protocollo_each.server_sharedmail_id_required = True
            else:
                protocollo_each.server_sharedmail_id_required = False

    @api.multi
    @api.depends('typology')
    def _compute_server_pec_id_required(self):
        for protocollo_each in self:
            protocollo = protocollo_each.with_context(skip_check=True)
            if protocollo.pec and protocollo.type=='out':
                protocollo_each.server_pec_id_required = True
            else:
                protocollo_each.server_pec_id_required = False

    @api.model
    def get_state_label(self, protocollo):
        state = ''
        if protocollo.state == 'draft':
            state = 'bozza'
        elif protocollo.state == 'registered':
            state = 'registrato'
        elif protocollo.state == 'waiting':
            state = 'pec-inviata'
        elif protocollo.state == 'error':
            state = 'pec-errore'
        elif protocollo.state == 'sent':
            state = 'inviato'
        elif protocollo.state == 'canceled':
            state = 'annullato'
        return state