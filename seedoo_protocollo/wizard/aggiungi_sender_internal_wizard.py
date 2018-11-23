# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.exceptions

class protocollo_sender_internal_wizard(osv.TransientModel):
    _name = 'protocollo.aggiungi.sender.internal.wizard'
    _description = 'Aggiungi Mittente Interno'

    _columns = {
        'sender_internal_ref': fields.many2one('protocollo.assegnatario', 'Dipendente del Mittente Interno', domain="[('assignable', '=', True)]")
    }

    def _default_sender_internal_employee_id(self, cr, uid, context):
        protocollo_obj = self.pool.get('protocollo.protocollo')
        protocollo_ids = protocollo_obj.search(cr, uid, [
            ('id', '=', context['active_id'])
        ])
        if protocollo_ids:
            protocollo = protocollo_obj.browse(cr, uid, protocollo_ids[0])
            return protocollo.sender_internal_assegnatario.id
        return False

    _defaults = {
        'sender_internal_ref': _default_sender_internal_employee_id
    }

    def action_save(self, cr, uid, ids, context=None):
        protocollo_obj = self.pool.get('protocollo.protocollo')
        wizard = self.browse(cr, uid, ids[0], context)
        vals = {}
        vals['sender_internal_assegnatario'] = wizard.sender_internal_ref.id
        vals['sender_internal_name'] = wizard.sender_internal_ref.name
        vals['sender_internal_employee'] = wizard.sender_internal_ref.employee_id.id
        vals['sender_internal_department'] = wizard.sender_internal_ref.department_id.id
        protocollo_obj.write(cr, uid, [context['active_id']], vals)

        return {
                'name': 'Protocollo',
                'view_type': 'form',
                'view_mode': 'form,tree',
                'res_model': 'protocollo.protocollo',
                'res_id': context['active_id'],
                'context': context,
                'type': 'ir.actions.act_window'
        }
