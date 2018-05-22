# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp import api, fields, models

class Protocollo(models.Model):
    _inherit = 'protocollo.protocollo'

    in_attesa = fields.Boolean(string='In Attesa', compute='_compute_state_assegnazione', store=True, readonly=True)
    preso = fields.Boolean(string='Preso', compute='_compute_state_assegnazione', store=True, readonly=True)
    rifiutato = fields.Boolean(string='Rifiutato', compute='_compute_state_assegnazione', store=True, readonly=True)

    @api.multi
    @api.depends('registration_employee_id', 'assegnazione_competenza_ids.state')
    def _compute_state_assegnazione(self):
        for protocollo in self:
            if protocollo.registration_employee_id:
                protocollo.in_attesa = True
                for assegnazione_competenza in protocollo.assegnazione_competenza_ids:
                    if assegnazione_competenza.state == 'preso':
                        protocollo.in_attesa = False
                        protocollo.preso = True
                        protocollo.rifiutato = False
                    elif assegnazione_competenza.state == 'rifiutato':
                        protocollo.in_attesa = False
                        protocollo.preso = False
                        protocollo.rifiutato = True

    # @api.model
    # def recompute(self):
    #     self.with_context(skip_check=True)
    #     cr, uid, context = self.env.args
    #     new_context = dict(context or {})
    #     new_context['skip_check'] = True
    #     new_args = (cr, uid, new_context)
    #     self.env.args = new_args
    #     super(Protocollo, self).recompute()