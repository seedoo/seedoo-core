# -*- encoding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp import SUPERUSER_ID
from openerp.osv import orm, fields
from openerp.tools.safe_eval import safe_eval
from openerp.tools.translate import _



class hr_department(orm.Model):
    _inherit = 'hr.department'

    def _get_child_ids(self, cr, uid, department):
        res = []
        for child in department.child_ids:
            res.append(child.id)
            child_res = self._get_child_ids(cr, uid, child)
            res = res + child_res
        return res

    def _get_all_child_ids(self, cr, uid, ids, field_names, arg=None, context=None):
        res = dict((res_id, []) for res_id in ids)
        for department in self.browse(cr, uid, ids, context=context):
            res[department.id] = self._get_child_ids(cr, uid, department)
        return res

    def _can_used_to_protocol(self, cr, uid, ids, name, arg, context=None):
        return {}

    def _can_used_to_protocol_search(self, cr, uid, obj, name, args, domain=None, context=None):
        department_ids = []
        employee_ids = self.pool.get('hr.employee').search(cr, uid, [('user_id', '=', uid)])
        for employee_id in employee_ids:
            department_ids.extend(self.pool.get('hr.department').search(cr, SUPERUSER_ID, [
                ('member_ids', '=', employee_id),
                ('aoo_id.registry_id.allowed_employee_ids', '=', employee_id)
            ]))
        return [('id', 'in', list(set(department_ids)))]

    _columns = {
        'code': fields.char("Codice della Risorsa dell'Organigramma", size=256),
        'description': fields.text('Descrizione Ufficio'),
        'active': fields.boolean('Attivo'),
        'aoo_id': fields.many2one('protocollo.aoo', 'AOO', required=False),
        'aoo_name': fields.related('aoo_id', 'name', type='char', string='Nome AOO', readonly=1),
        'all_child_ids': fields.function(_get_all_child_ids, type='one2many', relation='hr.department',
                                         string='Uffici figli di tutti i livelli sottostanti'),
        'can_used_to_protocol': fields.function(_can_used_to_protocol, fnct_search=_can_used_to_protocol_search,
                                                type='boolean', string='Può essere usato per protocollare'),
    }

    _defaults = {
        'active': True
    }

    def write(self, cr, uid, ids, vals, context=None):
        res = super(hr_department, self).write(cr, uid, ids, vals, context)
        if vals and vals.has_key('aoo_id') and vals['aoo_id']:
            self.pool.get('ir.rule').clear_cache(cr, uid)
        return res


class hr_employee(orm.Model):
    _inherit = 'hr.employee'

    _columns = {
        'code': fields.char("Codice della Risorsa dell'Organigramma", size=256),
        'protocollo_registry_ids': fields.many2many('protocollo.registry', 'protocollo_registry_hr_employee_rel',
                                                    'employee_id', 'registry_id', 'Dipendenti Abilitati'),
        'aoo': fields.related('department_id', 'aoo_name', type='char', string='AOO', readonly=1),
        'gruppo': fields.related('user_id', 'group', type='char', string='Gruppo', readonly=1),
    }

    def create(self, cr, uid, vals, context=None):
        new_context = dict(context or {})
        icp = self.pool.get('ir.config_parameter')
        if safe_eval(icp.get_param(cr, SUPERUSER_ID, 'auth_signup.disable_email_create_employee', 'False')):
            new_context['mail_notify_noemail'] = True
        employee_id = super(hr_employee, self).create(cr, uid, vals, context=new_context)
        self.pool.get('ir.rule').clear_cache(cr, uid)
        return employee_id

    def write(self, cr, uid, ids, vals, context=None):
        res = super(hr_employee, self).write(cr, uid, ids, vals, context)
        if vals and vals.has_key('department_id') and vals['department_id']:
            self.pool.get('ir.rule').clear_cache(cr, uid)
        return res
