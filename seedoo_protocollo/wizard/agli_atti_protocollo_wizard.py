# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

import logging
from openerp.osv import fields, osv, orm

_logger = logging.getLogger(__name__)


class agli_atti_protocollo_wizard(osv.TransientModel):

    _name = 'protocollo.agli.atti.wizard'
    _description = 'Agli Atti Protocollo'

    _columns = {
        'errore': fields.char('Errore', required=False, readonly=True),
        'motivazione': fields.text('Motivazione', required=False, readonly=False)
    }

    def _default_errore(self, cr, uid, context):
        errore = False
        if 'active_id' in context:
            protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'], {'skip_check': True})
            esito_visibility = protocollo.agli_atti_visibility
            if esito_visibility and protocollo.type == 'out' and protocollo.state in ['registered', 'waiting', 'error']:
                errore = 'Il protocollo deve essere in stato "Inviato" prima di essere messo "Agli Atti"!'
        return errore

    _defaults = {
        'errore': _default_errore
    }

    def agli_atti(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids[0], context)
        self.pool.get('protocollo.protocollo').agli_atti(cr, uid, context['active_ids'], wizard.motivazione, context)
        return {'type': 'ir.actions.act_window_close'}
