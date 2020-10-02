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
        'reserved': fields.boolean('Riservato', readonly=True),
        'sender_internal_ref': fields.many2one('protocollo.assegnatario', 'Dipendente del Mittente Interno', domain="[('is_visible', '=', True)]")
    }

    def _default_reserved(self, cr, uid, context):
        protocollo_obj = self.pool.get('protocollo.protocollo')
        protocollo = protocollo_obj.browse(cr, uid, context['active_id'], {'skip_check': True})
        if protocollo:
            return protocollo.reserved
        return False

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
        'reserved': _default_reserved,
        'sender_internal_ref': _default_sender_internal_employee_id
    }

    def action_save(self, cr, uid, ids, context=None):
        protocollo_obj = self.pool.get('protocollo.protocollo')
        protocollo = protocollo_obj.browse(cr, uid, context['active_id'], {'skip_check': True})
        save_history = protocollo.state in protocollo_obj.get_history_state_list(cr, uid)

        wizard = self.browse(cr, uid, ids[0], context)
        vals = {}
        vals['sender_internal_assegnatario'] = wizard.sender_internal_ref.id
        vals['sender_internal_name'] = wizard.sender_internal_ref.complete_name
        vals['sender_internal_employee'] = wizard.sender_internal_ref.employee_id.id if wizard.sender_internal_ref.employee_id else False
        vals['sender_internal_employee_department'] = wizard.sender_internal_ref.employee_id.department_id.id if wizard.sender_internal_ref.employee_id else False
        vals['sender_internal_department'] = wizard.sender_internal_ref.department_id.id if wizard.sender_internal_ref.department_id else False

        if save_history:
            old_sender_internal_id = protocollo.sender_internal_assegnatario.id if protocollo.sender_internal_assegnatario else False
            old_sender_internal_name = protocollo.sender_internal_assegnatario.complete_name if protocollo.sender_internal_assegnatario else ''
            operation_label = "Inserimento mittente" if not old_sender_internal_id else "Modifica mittente"

            if old_sender_internal_id != vals['sender_internal_assegnatario']:
                action_class = "history_icon update"
                body = "<div class='%s'><ul>" % action_class
                body += "<li>%s: <span style='color:#990000'> %s</span> -> <span style='color:#007ea6'> %s </span></li>" \
                              % ('Mittente', old_sender_internal_name, vals['sender_internal_name'])
                body += "</ul></div>"
                post_vars = {
                    'subject': operation_label,
                    'body': body,
                    'model': 'protocollo.protocollo',
                    'res_id': context['active_id']
                }
                protocollo_obj.message_post(cr, uid, context['active_id'], type="notification", context={'pec_messages': True},  **post_vars)

        protocollo_obj.write(cr, uid, [context['active_id']], vals)
        if protocollo.registration_date:
            protocollo_obj.aggiorna_segnatura_xml(cr, uid, [protocollo.id], force=True, log=False, commit=False, context=context)

        return {
                'name': 'Protocollo',
                'view_type': 'form',
                'view_mode': 'form,tree',
                'res_model': 'protocollo.protocollo',
                'res_id': context['active_id'],
                'context': context,
                'type': 'ir.actions.act_window',
                'flags': {'initial_mode': 'edit'}
        }

