# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

import logging
from openerp.osv import fields, osv
from openerp.tools.translate import _
import datetime


_logger = logging.getLogger(__name__)


class protocollo_emergency_registry_wizard(osv.TransientModel):
    """
        A wizard to manage the creation of emergency registry
    """
    _name = 'protocollo.emergency.registry.wizard'
    _description = 'Create Emergency Registry Management'
    _columns = {
        'name': fields.char('Causa Emergenza', size=256, required=True, readonly=False),
        'user_id': fields.many2one('res.users', 'Responsabile', readonly=True),
        'date_start': fields.datetime('Data Inizio Emergenza', required=True, readonly=False),
        'date_end': fields.datetime('Data Fine Emergenza', required=True, readonly=False),
        'number': fields.integer('Numero Protocolli in Emergenza', required=True),
        'registry_exists': fields.boolean('Registro Emergenza per AOO'),
    }

    def get_default_registry_exists(self, cr, uid, context=None):
        emergency_registry_obj = self.pool.get('protocollo.emergency.registry')
        reg_ids = emergency_registry_obj.search(cr, uid, [('state', '=', 'draft')])
        if len(reg_ids) > 0:
            return True
        return False

    _defaults = {
        'user_id': lambda obj, cr, uid, context: uid,
        'registry_exists': get_default_registry_exists
    }

    def get_last_protocollo(self, cr, uid, wizard):
        protocol_obj = self.pool.get('protocollo.protocollo')
        last_id = protocol_obj.search(cr, uid, [
            ('state', 'in', ('registered', 'notify'))
        ], limit=1, order='registration_date desc')
        return last_id

    def get_aoo_id(self, cr, uid, wizard):
        aoo_ids = self.pool.get('protocollo.aoo').search(cr, uid, [])
        for aoo_id in aoo_ids:
            check = self.pool.get('protocollo.aoo').is_visible_to_protocol_action(cr, uid, aoo_id)
            if check:
                return aoo_id
        return False

    def get_next_number(self, cr, uid, wizard):
        sequence_obj = self.pool.get('ir.sequence')
        protocol_obj = self.pool.get('protocollo.protocollo')
        last_id = self.get_last_protocollo(cr, uid, wizard)
        if last_id:
            now = datetime.datetime.now()
            last = protocol_obj.browse(cr, uid, last_id[0], {'skip_check': True})
            if last.registration_date[0:4] < str(now.year):
                seq_id = sequence_obj.search( cr, uid, [('code', '=', last.aoo_id.registry_id.sequence.code)])
                sequence_obj.write(cr, uid, seq_id, {'number_next': 1})
            next_num = sequence_obj.get(cr, uid, last.aoo_id.registry_id.sequence.code) or None
            if not next_num:
                raise osv.except_osv(_('Errore'), _('Il sistema ha riscontrato un errore nel reperimento del numero protocollo'))
            return next_num
        else:
            raise osv.except_osv(_('Errore'), _('Registrare almeno un protocollo prima di aprire un registro di emergenza'))

    def action_create(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids[0], context)
        if wizard.name and wizard.date_start:
            emergency_registry_obj = self.pool.get('protocollo.emergency.registry')
            emergency_registry_line_obj = self.pool.get('protocollo.emergency.registry.line')
            line_ids = []
            line_vals = {}
            for num in range(wizard.number):
                line_vals['name'] = self.get_next_number(cr, uid, wizard)
                line_ids.append(emergency_registry_line_obj.create(cr, uid, line_vals))
            vals = {
                'name': wizard.name,
                'user_id': wizard.user_id.id,
                'date_start': wizard.date_start,
                'date_end': wizard.date_end,
                'aoo_id': self.get_aoo_id(cr, uid, wizard),
                'emergency_ids': [[6, 0, line_ids]]
            }
            emergency_registry_id = emergency_registry_obj.create(cr, uid, vals)
            return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'protocollo.emergency.registry',
                'res_id': emergency_registry_id,
                'type': 'ir.actions.act_window',
                'context': context,
            }


        return {'type': 'ir.actions.act_window_close'}