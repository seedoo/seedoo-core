# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.exceptions


class protocollo_segna_come_letto_wizard(osv.TransientModel):
    _name = 'protocollo.segna.come.letto.wizard'
    _description = 'Segna come Letto Protocollo'

    def default_get(self, cr, uid, fields, context=None):
        result = super(protocollo_segna_come_letto_wizard, self).default_get(cr, uid, fields, context=context)
        result['assegnatario_department_id_visible'] = True

        if context and context.get('active_id'):
            protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'], {'skip_check': True})

            if not protocollo.segna_come_letto_visibility:
                result['errore'] = 'Il protocollo non può più essere "Segnato come Letto"!'
                return result

            assegnatario_department_ids = []
            assegnazione_obj = self.pool.get('protocollo.assegnazione')

            # ricerca tutte le assegnazioni fatte ad un dipendente associato all'utente corrente
            assegnazione_ids = assegnazione_obj.search(cr, uid, [
                ('protocollo_id', '=', context['active_id']),
                ('tipologia_assegnazione', '=', 'conoscenza'),
                ('tipologia_assegnatario', '=', 'employee'),
                ('assegnatario_employee_id.user_id.id', '=', uid),
                ('state', '=', 'assegnato'),
                ('parent_id', '=', False)
            ])
            if assegnazione_ids:
                assegnazione_list = assegnazione_obj.browse(cr, uid, assegnazione_ids)
                for assegnazione in assegnazione_list:
                    assegnatario_department_ids.append(assegnazione.assegnatario_employee_department_id.id)

            # ricerca tutte le assegnazioni fatte ad un ufficio associato all'utente corrente: è importante non
            # ricercare l'assegnazione del dipendente correlata all'ufficio perchè potrebbe non esserci (caso in cui
            # il dipendente viene spostato nell'ufficio dopo che l'assegnazione è stata fatta)
            department_ids = []
            employee_obj = self.pool.get('hr.employee')
            employee_ids = employee_obj.search(cr, uid, [('user_id', '=', uid)])
            for employee_id in employee_ids:
                employee = employee_obj.browse(cr, uid, employee_id)
                if employee.department_id:
                    department_ids.append(employee.department_id.id)
            assegnazione_ids = assegnazione_obj.search(cr, uid, [
                ('protocollo_id', '=', context['active_id']),
                ('tipologia_assegnazione', '=', 'conoscenza'),
                ('tipologia_assegnatario', '=', 'department'),
                ('assegnatario_department_id', 'in', department_ids),
                ('state', '=', 'assegnato')
            ])
            if assegnazione_ids:
                #`controlla per ogni assegnazione per ufficio che non esista una assegnazione fatta al dipendente con
                # stato diversa da assegnato (caso in cui l'utente abbia già segnato come letta l'assegnazione)
                assegnazione_list = assegnazione_obj.browse(cr, uid, assegnazione_ids)
                for assegnazione in assegnazione_list:
                    not_found = True
                    for assegnazione_child in assegnazione.child_ids:
                        if assegnazione_child.assegnatario_employee_id.id in employee_ids and assegnazione_child.state != 'assegnato':
                            not_found = False
                            break
                    if not_found:
                        assegnatario_department_ids.append(assegnazione.assegnatario_department_id.id)

            result['assegnatario_department_ids_visible'] = assegnatario_department_ids
            if len(assegnatario_department_ids) == 1:
                department_obj = self.pool.get('hr.department')
                department = department_obj.browse(cr, uid, assegnatario_department_ids[0])
                result['assegnatario_department_id'] = department.id
                result['assegnatario_department_name'] = department.name
                result['assegnatario_department_id_visible'] = False

        return result

    _columns = {
        'errore': fields.char(string='Errore', readonly=True),
        'assegnatario_department_id': fields.many2one('hr.department', "Segna come letto per l'ufficio"),
        'assegnatario_department_name': fields.related('assegnatario_department_id',
                                                       'name',
                                                       type='char',
                                                       string="Segna come letto per l'ufficio",
                                                       readonly=True),
        'assegnatario_department_id_visible': fields.boolean(string='Ufficio Visibili'),
        'assegnatario_department_ids_visible': fields.many2many('hr.department',
                                                                'protocollo_segna_come_letto_department_visible_rel',
                                                                'wizard_id',
                                                                'department_id',
                                                                'Uffici Visibili',
                                                                domain="[('is_visible', '=', True)]")
    }

    def action_save(self, cr, uid, ids, context=None):
        protocollo_obj = self.pool.get('protocollo.protocollo')
        wizard = self.browse(cr, uid, ids[0], context)
        employee_ids = self.pool.get('hr.employee').search(cr, uid, [
            ('department_id', '=', wizard.assegnatario_department_id.id),
            ('user_id', '=', uid)
        ])
        # se non trova nessun dipendente allora vuol dire che è stato selezionato un ufficio relativo ad una
        # assegnazione per dipendente, di cui ora il dipendente non fa più parte, quindi bisogna ricercare il nuovo
        # ufficio tramite l'assegnazione in questione
        if not employee_ids:
            assegnazione_obj = self.pool.get('protocollo.assegnazione')
            assegnazione_id = assegnazione_obj.search(cr, uid, [
                ('protocollo_id', '=', context['active_id']),
                ('tipologia_assegnatario', '=', 'employee'),
                ('assegnatario_employee_department_id', '=', wizard.assegnatario_department_id.id),
                ('assegnatario_employee_id.user_id.id', '=', uid),
                ('parent_id', '=', False)
            ], limit=1)
            assegnazione = assegnazione_obj.browse(cr, uid, assegnazione_id)
            if assegnazione and assegnazione.assegnatario_employee_id:
                employee_ids = [assegnazione.assegnatario_employee_id.id]
        assegnatario_employee_id = employee_ids[0] if employee_ids else False
        protocollo_obj.segna_come_letto(cr, uid, [context['active_id']], assegnatario_employee_id)
        return {'type': 'ir.actions.act_window_close'}