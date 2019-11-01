# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

import logging
from openerp.osv import fields, osv, orm
from openerp.tools import (
    DEFAULT_SERVER_DATETIME_FORMAT as DSDF)
from openerp.tools.translate import _
from openerp import netsvc

_logger = logging.getLogger(__name__)


class wizard(osv.TransientModel):
    """
        A wizard to manage the cancel state of protocol
    """
    _name = 'protocollo.rifiuta.wizard'
    _description = 'Rifiuta Protocollo'

    _columns = {
        'name': fields.text(
            'Causa rifiuto assegnazione',
            required=True,
            readonly=False
        ),
    }

    def rifiuta_presa_in_carico(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids[0], context)
        if wizard.name:
            self.pool.get('protocollo.protocollo').rifiuta_presa_in_carico(cr, uid, [context['active_id']], wizard.name, context)
        return {'type': 'ir.actions.act_window_close'}
