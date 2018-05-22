# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp import api, fields, models

class ProtocolloAssegnazione(models.Model):
    _inherit = 'protocollo.assegnazione'

    @api.model
    def recompute(self):
        self.with_context(skip_check=True)
        cr, uid, context = self.env.args
        new_context = dict(context or {})
        new_context['skip_check'] = True
        new_args = (cr, uid, new_context)
        self.env.args = new_args
        super(ProtocolloAssegnazione, self).recompute()