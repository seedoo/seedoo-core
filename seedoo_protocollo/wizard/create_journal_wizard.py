# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

import logging
from openerp.osv import fields, osv
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DSDF
from openerp.tools.translate import _
import time


_logger = logging.getLogger(__name__)


class wizard(osv.TransientModel):
    """
        A wizard to manage the creation of journal protocollo
    """
    _name = 'protocollo.journal.wizard'
    _description = 'Create Journal Management'

    def action_create(self, cr, uid, ids, context=None):
        aoo_ids = self.pool.get('protocollo.aoo').search(cr, uid, [])

        if aoo_ids and len(aoo_ids)>0:
            for aoo_id in aoo_ids:
                journal_obj = self.pool.get('protocollo.journal')
                journal_today = journal_obj.search(cr, uid, [
                    ('aoo_id', '=', aoo_id),
                    ('state', '=', 'closed'),
                    ('date', '=', time.strftime('%Y-%m-%d'))
                ])
                if journal_today:
                    raise osv.except_osv(
                        _('Attenzione!'),
                        _('Registro Giornaliero del Protocollo esistente per la giornata di oggi!')
                    )
                protocollo_obj = self.pool.get('protocollo.protocollo')
                protocol_ids = protocollo_obj.search(cr, uid, [
                    ('aoo_id', '=', aoo_id),
                    ('state', 'in', ['registered', 'notified', 'waiting', 'error', 'sent']),
                    ('registration_date', '>', time.strftime('%Y-%m-%d') + ' 00:00:00'),
                    ('registration_date', '<', time.strftime('%Y-%m-%d') + ' 23:59:59'),
                ])
                journal_id = journal_obj.create(cr, uid, {
                    'name': time.strftime(DSDF),
                    'aoo_id': aoo_id,
                    'user_id': uid,
                    'protocol_ids': [[6, 0, protocol_ids]],
                    'state': 'closed',
                })

                if len(aoo_ids)==1:
                    datas = {'ids': [journal_id], 'model': 'protocollo.journal'}
                    return {
                        'type': 'ir.actions.report.xml',
                        'report_name': 'seedoo_protocollo.journal_qweb',
                        'datas': datas,
                    }

        return {
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'protocollo.journal',
            'type': 'ir.actions.act_window',
            'context': context,
        }
