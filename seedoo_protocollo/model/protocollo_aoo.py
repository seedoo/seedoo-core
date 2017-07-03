# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp import SUPERUSER_ID
from openerp.osv import orm, fields, osv


class protocollo_aoo(orm.Model):
    _name = 'protocollo.aoo'

    def _office_check(self, cr, uid, user, aoo):
        for employee in user.employee_ids:
            if employee.department_id and employee.department_id.aoo_id and employee.department_id.aoo_id.id==aoo.id:
                return True
        return False

    def is_visible_to_protocol_action(self, cr, uid, aoo_id):
        if uid == SUPERUSER_ID:
            return True

        user = self.pool.get('res.users').browse(cr, uid, uid)
        aoo = self.pool.get('protocollo.aoo').browse(cr, uid, aoo_id)
        if aoo and aoo.registry_id and aoo.registry_id.allowed_employee_ids:
            for employee in aoo.registry_id.allowed_employee_ids:
                if employee.user_id and employee.user_id.id == user.id and self._office_check(cr, uid, user, aoo):
                    return True

        return False

    def _is_visible_to_protocol(self, cr, uid, ids, name, arg, context=None):
        return {}

    def _is_visible_to_protocol_search(self, cr, uid, obj, name, args, domain=None, context=None):
        aoo_visible_list = []
        aoo_ids = self.pool.get('protocollo.aoo').search(cr, uid, [], context=context)
        for aoo_id in aoo_ids:
            if self.is_visible_to_protocol_action(cr, uid, aoo_id):
                aoo_visible_list.append(aoo_id)
        return [('id', 'in', aoo_visible_list)]

    _columns = {
        'name': fields.char('Nome', size=256, required=True),
        'company_id': fields.many2one('res.company', 'Ente', required=True),
        'ident_code': fields.char('Codice Identificativo Area', size=256, required=True),
        'manager_employee_id': fields.many2one('hr.employee', 'Responsabile'),
        'reserved_employee_id': fields.many2one('hr.employee', 'Responsabile Dati Sensibili'),
        'registry_id': fields.many2one('protocollo.registry', 'Registro', readonly=True),
        'department_ids': fields.one2many('hr.department', 'aoo_id', 'Uffici'),
        'classification_ids': fields.one2many('protocollo.classification', 'aoo_id', 'Titolari'),
        'dossier_ids': fields.one2many('protocollo.dossier', 'aoo_id', 'Fascicolari'),
        'typology_ids': fields.one2many('protocollo.typology', 'aoo_id', 'Mezzi di Trasmissione'),

        'street': fields.char('Indirizzo'),
        'zip': fields.char('CAP', size=24, change_default=True),
        'city': fields.char('Città'),
        'country_id': fields.many2one('res.country', 'Nazione', ondelete='restrict'),
        'email': fields.char('Email'),
        'phone': fields.char('Telefono'),
        'website': fields.char('Website'),

        'is_visible_to_protocol': fields.function(_is_visible_to_protocol, fnct_search=_is_visible_to_protocol_search,
                                                  type='boolean', method=True, string='Visibile per Protocollare'),
        'employee_ids': fields.related('registry_id', 'allowed_employee_ids', type='many2many', relation='hr.employee', string='AOO'),
        #
        # 'journal_ids': fields.related('config_id', 'journal_ids',
        #                               type='many2many',
        #                               readonly=True,
        #                               relation='account.journal',
        #                               string='Available Payment Methods'),

    }

    def _get_default_company_id(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid)
        return user.company_id.id

    _defaults = {
        'company_id': _get_default_company_id
    }

    def get_aoo_count(self, cr, uid, context={}):
        count = 0
        aoo_ids = self.pool.get('protocollo.aoo').search(cr, uid, [], context)
        for aoo_id in aoo_ids:
            check = self.pool.get('protocollo.aoo').is_visible_to_protocol_action(cr, uid, aoo_id)
            if check:
                count = count + 1
        return count

    def create(self, cr, uid, vals, context=None):
        aoo_id = super(protocollo_aoo, self).create(cr, uid, vals, context=context)
        aoo = self.browse(cr, uid, aoo_id)

        sequence_obj = self.pool.get('ir.sequence')
        sequence_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'seedoo_protocollo', 'seq_def_protocollo')[1]

        sequence_type_obj = self.pool.get('ir.sequence.type')
        sequence_type_code = 'protocollo.sequence.aoo.' + str(aoo.id)
        sequence_type_obj.create(cr, uid, {
            'name': 'Sequence Registro ' + vals['name'],
            'code': sequence_type_code
        })

        sequence_copy_id = sequence_obj.copy(cr, uid, sequence_id, {
            'name': 'Sequence Registro ' + vals['name'],
            'code': sequence_type_code
        })

        registry_id = self.pool.get('protocollo.registry').create(cr, uid, {
            'name': 'Registro ' + aoo.name,
            'code': 'protocollo.registro.aoo.' + str(aoo.id),
            'company_id': aoo.company_id.id,
            'sequence': sequence_copy_id
        })
        self.write(cr, uid, [aoo.id], {'registry_id': registry_id})
        return aoo.id
