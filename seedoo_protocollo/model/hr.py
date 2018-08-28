# -*- encoding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp import SUPERUSER_ID
from openerp.osv import orm, fields
from openerp.tools.safe_eval import safe_eval
from openerp.tools.translate import _



class hr_department(orm.Model):
    _inherit = 'hr.department'

    _columns = {
        'description': fields.text('Descrizione Ufficio'),
        'assignable': fields.boolean('Assegnabile in Protocollazione'),
        'aoo_id': fields.many2one('protocollo.aoo', 'AOO', required=False),
        'aoo_name': fields.related('aoo_id', 'name', type='char', string='Nome AOO', readonly=1),
    }

    def _check_department_depth(self, cr, uid, ids):
        for department in self.browse(cr, uid, ids):
            if department.aoo_id and ((department.parent_id and department.child_ids) or (department.parent_id and department.parent_id.parent_id)):
                raise orm.except_orm('Errore', 'La gerarchia degli uffici di una AOO non possono superare il secondo livello!')

    def create(self, cr, uid, vals, context=None):
        department_id = super(hr_department, self).create(cr, uid, vals, context=context)
        self._check_department_depth(cr, uid, [department_id])
        return department_id

    def write(self, cr, uid, ids, vals, context=None):
        res = super(hr_department, self).write(cr, uid, ids, vals, context)
        self._check_department_depth(cr, uid, ids)
        return res


class hr_employee(orm.Model):
    _inherit = 'hr.employee'

    _columns = {
        'protocollo_registry_ids': fields.many2many('protocollo.registry', 'protocollo_registry_hr_employee_rel',
                                                    'employee_id', 'registry_id', 'Dipendenti Abilitati'),
        'aoo': fields.related('department_id', 'aoo_name', type='char', string='AOO', readonly=1),
        'gruppo': fields.related('user_id', 'group', type='char', string='Gruppo', readonly=1),
    }

    def create(self, cr, uid, vals, context=None):
        new_context = dict(context or {})
        icp = self.pool.get('ir.config_parameter')
        if safe_eval(icp.get_param(cr, uid, 'auth_signup.disable_email_create_employee', 'False')):
            new_context['mail_notify_noemail'] = True
        employee_id = super(hr_employee, self).create(cr, uid, vals, context=new_context)
        self.pool.get('ir.rule').clear_cache(cr, uid)
        return employee_id

    def write(self, cr, uid, ids, vals, context=None):
        res = super(hr_employee, self).write(cr, uid, ids, vals, context)
        if vals and vals.has_key('department_id') and vals['department_id']:
            self.pool.get('ir.rule').clear_cache(cr, uid)
        return res
