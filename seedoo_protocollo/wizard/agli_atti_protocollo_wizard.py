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
        'motivazione': fields.text('Motivazione', required=False, readonly=False)
    }

    def agli_atti(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids[0], context)
        if wizard.motivazione:
            self.pool.get('protocollo.protocollo').agli_atti(cr, uid, context['active_ids'], wizard.motivazione)
        return {'type': 'ir.actions.act_window_close'}
