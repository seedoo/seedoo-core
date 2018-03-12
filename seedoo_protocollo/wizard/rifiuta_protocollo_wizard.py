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
        rec = self.pool.get('res.users').browse(cr, uid, uid)
        wizard = self.browse(cr, uid, ids[0], context)

        if wizard.name:
            action_class = "history_icon refused"
            post_vars = {'subject': "Rifiuto assegnazione: %s" %wizard.name,
                         'body': "<div class='%s'><ul><li>Assegnazione rifiutata da <span style='color:#990000;'>%s</span></li></ul></div>" % (
                         action_class, rec.name),
                         'model': "protocollo.protocollo",
                         'res_id': context['active_id'],
                         }

            thread_pool = self.pool.get('protocollo.protocollo')
            thread_pool.message_post(cr, uid, context['active_id'], type="notification", context=context, **post_vars)

            self.pool.get('protocollo.stato.dipendente').modifica_stato_dipendente(cr, uid, [context['active_id']], 'rifiutato')

        return {'type': 'ir.actions.act_window_close'}
