# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

import logging
from openerp.osv import fields, osv
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DSDF
from openerp.tools.translate import _
import time


_logger = logging.getLogger(__name__)


class protocollo_journal_wizard(osv.TransientModel):
    """
        A wizard to manage the creation of journal protocollo
    """
    _name = 'protocollo.journal.wizard'
    _description = 'Crea Registro Giornaliero'
    _columns = {
        'date_register': fields.date('Data Registro', required=True, readonly=False),
    }

    def get_aoo_id(self, cr, uid, wizard):
        aoo_ids = self.pool.get('protocollo.aoo').search(cr, uid, [])
        for aoo_id in aoo_ids:
            check = self.pool.get('protocollo.aoo').is_visible_to_protocol_action(cr, uid, aoo_id)
            if check:
                return aoo_id
        return False

    def action_create(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids[0], context)

        aoo_id = self.get_aoo_id(cr, uid, wizard)

        journal_obj = self.pool.get('protocollo.journal')
        journal_today = journal_obj.search(cr, uid, [
            ('aoo_id', '=', aoo_id),
            ('state', '=', 'closed'),
            ('date', '=', wizard.date_register)
        ])
        if journal_today:
            raise osv.except_osv(
                _('Attenzione!'),
                _('Registro Giornaliero del Protocollo esistente per la data selezionata!')
            )
        protocollo_obj = self.pool.get('protocollo.protocollo')
        protocol_ids = protocollo_obj.search(cr, uid, [
            ('aoo_id', '=', aoo_id),
            ('state', 'in', ['registered', 'notified', 'waiting', 'error', 'sent', 'acts']),
            ('registration_date', '>', wizard.date_register + ' 00:00:00'),
            ('registration_date', '<', wizard.date_register + ' 23:59:59'),
        ])
        journal_id = journal_obj.create(cr, uid, {
            'name': wizard.date_register,
            'date': wizard.date_register,
            'aoo_id': aoo_id,
            'user_id': uid,
            'protocol_ids': [[6, 0, protocol_ids]],
            'state': 'closed',
        })

        datas = {'ids': [journal_id], 'model': 'protocollo.journal'}
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'seedoo_protocollo.journal_qweb',
            'datas': datas,
        }