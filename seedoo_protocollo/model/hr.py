# -*- encoding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp import SUPERUSER_ID
from openerp.osv import orm,  fields
from openerp.tools.translate import _


# class hr_department_collaborator(orm.Model):
#     _name = 'hr.department.collaborator'
#
#     _columns = {
#         'department_id': fields.many2one('hr.department', 'Department', required=True),
#         'name': fields.many2one('res.users', 'Collaborator', required=True),
#         'to_notify': fields.boolean('To be notified by mail'),
#     }


class hr_department(orm.Model):
    _inherit = 'hr.department'

    _columns = {
        'description': fields.text('Descrizione Ufficio'),
        'assignable': fields.boolean('Assegnabile in Protocollazione'),
        # 'collaborator_ids': fields.one2many('hr.department.collaborator', 'department_id', 'Collaborators'),
        'aoo_id': fields.many2one('protocollo.aoo', 'AOO', required=False),
        'aoo_name': fields.related('aoo_id', 'name', type='char', string='Nome AOO', readonly=1),
    }

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        if not ids:
            return True
        if not hasattr(ids, '__iter__'):
            ids = [ids]

        objsdep = self.browse(cr, uid, ids, context=context)
        for dep in objsdep:
            if dep.manager_id.user_id is not None:
                manager_id = dep.manager_id.user_id.id
                if (
                        #vals.get('collaborator_ids') or
                        vals.get('manager_id') or
                        vals.get('type')):
                    if ((uid == SUPERUSER_ID) or (uid == manager_id)):
                        res = super(hr_department, self).write(
                            cr, uid, ids, vals, context
                            )
                    else:
                        raise orm.except_orm(
                            'Error !',
                            "Only the administrator or manager"
                            "can change configuration fields"
                        )
                else:
                    res = super(hr_department, self).write(
                        cr, uid, ids, vals, context)
            else:
                res = super(hr_department, self).write(
                    cr, uid, ids, vals, context)
        return res


class hr_employee(orm.Model):
    _inherit = 'hr.employee'

    # def _save_aoo_id_in_partner_id(self, cr, uid, employee_ids):
    #     for employee_id in employee_ids:
    #         employee = self.browse(cr, uid, employee_id)
    #         aoo_id = False
    #         if employee and employee.department_id and employee.department_id.aoo_id:
    #             aoo_id = employee.department_id.aoo_id.id
    #         partner_id = False
    #         if employee and employee.user_id and employee.user_id.partner_id:
    #             partner_id = employee.user_id.partner_id.id
    #         if aoo_id and partner_id:
    #             self.pool.get('res.partner').write(cr, uid, [partner_id], {'aoo_id': aoo_id})
    #         else:
    #             self.pool.get('res.partner').write(cr, uid, [partner_id], {'aoo_id': False})

    _columns = {
        'protocollo_registry_ids': fields.many2many('protocollo.registry', 'protocollo_registry_hr_employee_rel',
                                                    'employee_id', 'registry_id', 'Dipendenti Abilitati'),
        'aoo': fields.related('department_id', 'aoo_name', type='char', string='AOO', readonly=1),
        'gruppo': fields.related('user_id', 'group', type='char', string='Gruppo', readonly=1),
        'profile_id': fields.many2one('protocollo.profile', 'Profilo Seedoo Protocollo'),

    }

    def create(self, cr, uid, vals, context=None):
        employee_id = super(hr_employee, self).create(cr, uid, vals, context=context)

        if vals and vals.has_key('profile_id') and vals['profile_id']:

            employee = self.browse(cr,uid, employee_id)

            protocollo_profile = self.pool.get('protocollo.profile').browse(cr, uid, vals['profile_id'])

            self.pool.get('res.users').write(cr,uid, [employee.user_id.id], {
                'groups_id': [(6, 0, protocollo_profile.groups_id.ids)]
            })

            self.pool.get('protocollo.profile').write(cr,uid, [protocollo_profile.id], {
                'employees': [(4, employee.id)]
            })

        # if vals.has_key('user_id') and vals['user_id']:
        #     self._save_aoo_id_in_partner_id(cr, uid, [employee_id])
        self.pool.get('ir.rule').clear_cache(cr, uid)
        return employee_id

    def write(self, cr, uid, ids, vals, context=None):
        res = super(hr_employee, self).write(cr, uid, ids, vals, context)
        # if vals.has_key('user_id') and vals['user_id']:
        #     self._save_aoo_id_in_partner_id(cr, uid, ids)
        if vals and vals.has_key('department_id') and vals['department_id']:
            self.pool.get('ir.rule').clear_cache(cr, uid)

        if vals and vals.has_key('profile_id') and vals['profile_id']:

            employee = self.browse(cr,uid, ids)

            protocollo_profile = self.pool.get('protocollo.profile').browse(cr, uid, vals['profile_id'])

            self.pool.get('res.users').write(cr,uid, [employee.user_id.id], {
                    'groups_id': [(6, 0, protocollo_profile.groups_id.ids)]
                })

            self.pool.get('protocollo.profile').write(cr,uid, [protocollo_profile.id], {
                'employees': [(4, employee.id)]
            })


        return res
