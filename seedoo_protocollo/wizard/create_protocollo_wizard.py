# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

import logging
from openerp.osv import fields, osv, orm


_logger = logging.getLogger(__name__)


class create_protocollo_wizard(osv.TransientModel):

    _name = 'protocollo.create.wizard'
    _description = 'Crea Protocollo'

    def _get_types(self, cr, uid, context=None):
        types = []
        if self.user_has_groups(cr, uid, 'seedoo_protocollo.group_crea_protocollo_ingresso'):
            types.append(('in', 'Ingresso'))
        if self.user_has_groups(cr, uid, 'seedoo_protocollo.group_crea_protocollo_uscita'):
            types.append(('out', 'Uscita'))
        if self.user_has_groups(cr, uid, 'seedoo_protocollo.group_crea_protocollo_interno'):
            types.append(('internal', 'Interno'))
        return types

    _columns = {
        'aoo_id': fields.many2one('protocollo.aoo', string='AOO', readonly=True),
        'registry_id': fields.many2one('protocollo.registry', string='Registro', readonly=True),
        'type': fields.selection(_get_types, 'Tipo', size=32),
        'registration_employee_department_id': fields.many2one('hr.department', 'Ufficio'),
        'type_readonly': fields.boolean('Campo type readonly', readonly=True),
        'registration_employee_department_id_readonly': fields.boolean('Campo registration_employee_department_id readonly', readonly=True),
        'error': fields.text('Errore', readonly=True),
        'user_id': fields.many2one('res.users', 'Utente', readonly=True),
        'emergency_active': fields.boolean('Registro Emergenza Attivo'),
        'registration_type': fields.selection([ ('normal', 'Normale'), ('emergency', 'Emergenza')], 'Tipologia Registrazione', size=32),
        'protocolla_emergenza_visibility': fields.boolean(string='Seleziona Protocollazione Emergenza')
    }

    def _default_aoo_id(self, cr, uid, context):
        aoo_id = self.pool.get('protocollo.protocollo')._get_default_aoo_id(cr, uid, context)
        if aoo_id:
            return aoo_id
        return False

    def _default_registry_id(self, cr, uid, context):
        aoo_id = self.pool.get('protocollo.protocollo')._get_default_aoo_id(cr, uid, context)
        if aoo_id:
            aoo = self.pool.get('protocollo.aoo').browse(cr, uid, aoo_id)
            if aoo:
                return aoo.registry_id.id
        return False

    def _default_type(self, cr, uid, context):
        types = self._get_types(cr, uid, context)
        if types and len(types) == 1:
            return types[0][0]
        return False

    def _default_registration_employee_department_id(self, cr, uid, context):
        department_ids = self.pool.get('hr.department').search(cr, uid, [('can_used_to_protocol', '=', True)])
        if department_ids:
            return department_ids[0]
        return False

    def _default_type_readonly(self, cr, uid, context):
        types = self._get_types(cr, uid, context)
        if len(types) == 1:
            return True
        return False

    def _default_registration_employee_department_id_readonly(self, cr, uid, context):
        department_ids = self.pool.get('hr.department').search(cr, uid, [('can_used_to_protocol', '=', True)])
        if len(department_ids) == 1:
            return True
        return False

    def _default_error(self, cr, uid, context):
        return self.pool.get('protocollo.protocollo').seedoo_error(cr, uid)

    def _default_is_emergency_active(self, cr, uid, context=None):
        aoo_id = self.pool.get('protocollo.protocollo')._get_default_aoo_id(cr, uid, context)
        if aoo_id:
            emergency_registry_obj = self.pool.get('protocollo.emergency.registry')
            if aoo_id:
                reg_ids = emergency_registry_obj.search(cr, uid, [
                    ('aoo_id', '=', aoo_id),
                    ('state', '=', 'draft')
                ])
                if len(reg_ids) > 0:
                    return True
        return False

    def _default_protocolla_emergenza_visibility(self, cr, uid, context=None):
        check = self.user_has_groups(cr, uid, 'seedoo_protocollo.group_configurazione_emergenza')

        return check

    _defaults = {
        'aoo_id': _default_aoo_id,
        'registry_id': _default_registry_id,
        'type': _default_type,
        'registration_employee_department_id': _default_registration_employee_department_id,
        'type_readonly': _default_type_readonly,
        'registration_employee_department_id_readonly': _default_registration_employee_department_id_readonly,
        'error': _default_error,
        'user_id': lambda self, cr, uid, context: uid,
        'emergency_active': _default_is_emergency_active,
        'registration_type': 'normal',
        'protocolla_emergenza_visibility': _default_protocolla_emergenza_visibility
    }

    def action_create(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids[0], context)
        values = {
            'type': wizard.type,
            'registration_type': wizard.registration_type,
            'registration_employee_department_id': wizard.registration_employee_department_id.id,
            'registration_employee_department_name': wizard.registration_employee_department_id.complete_name
        }
        protocollo_id = self.pool.get('protocollo.protocollo').create(cr, uid, values)
        return {
            'name': 'Protocollo',
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'protocollo.protocollo',
            'res_id': protocollo_id,
            'context': context,
            'type': 'ir.actions.act_window',
            'flags': {'initial_mode': 'edit'}
        }