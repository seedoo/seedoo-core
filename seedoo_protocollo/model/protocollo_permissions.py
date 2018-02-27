# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.
import time
from collections import OrderedDict

from openerp import SUPERUSER_ID
from openerp.osv import orm, fields, osv
import logging

_logger = logging.getLogger(__name__)


class protocollo_protocollo(osv.Model):
    _inherit = 'protocollo.protocollo'

    def _get_protocolli(self, cr, uid, ids):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]

        protocolli = self.browse(cr, uid, ids)
        return protocolli

    def _check_stato_assegnatario_competenza(self, cr, uid, protocollo, stato, assegnatario_uid=None):
        if not assegnatario_uid:
            assegnatario_uid = uid
        stato_dipendente_obj = self.pool.get('protocollo.stato.dipendente')
        employees_ids = self._get_assegnatari_competenza(cr, uid, protocollo)
        employees = self.browse(cr, uid, employees_ids)
        for employee in employees:
            if employee.user_id and employee.user_id.id == assegnatario_uid:
                stato_dipendente_ids = stato_dipendente_obj.search(cr, uid, [
                    ('dipendente_id', '=', employee.id),
                    ('protocollo_id', '=', protocollo.id),
                ])
                if len(stato_dipendente_ids) > 0:
                    stato_dipendente = stato_dipendente_obj.browse(cr, uid, stato_dipendente_ids[0])
                    if stato_dipendente and stato_dipendente.state == stato:
                        return True
        return False

    ####################################################################################################################
    # Visibilità dei protocolli
    ####################################################################################################################

    def _is_registered_by_child_departments(self, cr, uid, department, registration_department):
        for child_department in department.child_ids:
            if child_department.id == registration_department.id or self._is_registered_by_child_departments(cr, uid,
                                                                                                             child_department,
                                                                                                             registration_department):
                return True
        return False

    def _is_assigned_to_child_departments(self, cr, uid, department, assigned_department):
        for child_department in department.child_ids:
            if child_department.id == assigned_department.id or self._is_assigned_to_child_departments(cr, uid,
                                                                                                       child_department,
                                                                                                       assigned_department):
                return True
        return False

    # def _check_visible(self, cr, uid, user_employee, protocollo):
    #     user = user_employee.user_id
    #     user_department = user_employee.department_id if user_employee.department_id else None
    #     registration_employee = protocollo.registration_employee_id if protocollo.registration_employee_id else None
    #     registration_department = registration_employee.department_id if registration_employee and registration_employee.department_id else None

    ################################################################################################################
    # Visibilità dei protocolli: casi base
    ################################################################################################################

    # un utente deve poter vedere i protocolli in bozza (IN e OUT) creati da lui
    # if protocollo.state == 'draft' and protocollo.user_id and protocollo.user_id.id == user.id:
    #     return True

    # un utente deve poter vedere i protocolli (IN e OUT) registrati da lui
    # if registration_employee and registration_employee.id == user_employee.id:
    #     return True

    # un utente deve poter vedere i protocolli registrati (IN e OUT) assegnati a lui
    # purchè lui o un dipendente del suo ufficio non abbia rifiutato la presa in carico
    # is_assegnatario = False
    # is_protocollo_rifiutato_by_department = False
    #
    # if registration_employee:
    #     stato_dipendente_obj = self.pool.get('protocollo.stato.dipendente')
    #
    #     employees_ids = self._get_assegnatari(cr, uid, protocollo)
    #     if user_employee.id in employees_ids:
    #         is_assegnatario = True
    #     # else:
    #     #     employees_ids = self._get_assegnatari_conoscenza(cr, uid, protocollo)
    #     #     if user_employee.id in employees_ids:
    #     #         is_assegnatario = True
    #
    #     stato_dipendente_ids = stato_dipendente_obj.search(cr, uid, [
    #         ('dipendente_id', 'in', employees_ids),
    #         ('protocollo_id', '=', protocollo.id),
    #         ('state', '=', 'rifiutato')
    #     ])
    #     if len(stato_dipendente_ids) > 0:
    #         is_protocollo_rifiutato_by_department = True
    #
    #     if is_assegnatario and not is_protocollo_rifiutato_by_department:
    #         return True

    ################################################################################################################
    # Visibilità dei protocolli: permessi in configurazione
    ################################################################################################################

    # # un utente deve poter vedere i protocolli (IN e OUT) REGISTRATI dal suo UFFICIO di appartenenza
    # check_gruppo = self.user_has_groups(cr, user.id,
    #                                     'seedoo_protocollo.group_vedi_protocolli_ingresso_registrati_ufficio,seedoo_protocollo.group_vedi_protocolli_uscita_registrati_ufficio')
    # if check_gruppo and user_department and registration_department and user_department.id == registration_department.id:
    #     return True

    # un utente deve poter vedere i protocolli (IN e OUT) REGISTRATI da un UFFICIO FIGLIO del suo ufficio di appartenenza
    # check_gruppo = self.user_has_groups(cr, user.id,
    #                                     'seedoo_protocollo.group_vedi_protocolli_ingresso_registrati_ufficio_figlio,seedoo_protocollo.group_vedi_protocolli_uscita_registrati_ufficio_figlio')
    # if check_gruppo and user_department and registration_department and self._is_registered_by_child_departments(cr,
    #                                                                                                              uid,
    #                                                                                                              user_department,
    #                                                                                                              registration_department):
    #     return True

    # un utente deve poter vedere QUALUNQUE protocollo (IN e OUT) in stato BOZZA appartenente alla sua AOO
    # check_gruppo = self.user_has_groups(cr, user.id,
    #                                     'seedoo_protocollo.group_vedi_protocolli_ingresso_bozza,seedoo_protocollo.group_vedi_protocolli_uscita_bozza')
    # if check_gruppo and protocollo.state == 'draft' and protocollo.aoo_id and user_department.aoo_id and protocollo.aoo_id.id == user_department.aoo_id.id:
    #     return True

    # # un utente deve poter vedere QUALUNQUE protocollo (IN e OUT) REGISTRATO da un utente della sua AOO
    # check_gruppo = self.user_has_groups(cr, user.id,
    #                                     'seedoo_protocollo.group_vedi_protocolli_ingresso_registrati,seedoo_protocollo.group_vedi_protocolli_uscita_registrati')
    # if check_gruppo and protocollo.aoo_id and registration_department and registration_department.aoo_id and protocollo.aoo_id.id == registration_department.aoo_id.id:
    #     return True

    # un utente deve poter vedere i protocolli (IN e OUT) REGISTRATI e ASSEGNATI ad un UTENTE del suo UFFICIO di appartenenza
    # check_gruppo = self.user_has_groups(cr, user.id,
    #                                     'seedoo_protocollo.group_vedi_protocolli_ingresso_registrati_ass_ut_uff,seedoo_protocollo.group_vedi_protocolli_uscita_registrati_ass_ut_uff')
    # if check_gruppo and registration_employee and user_department:
    #     for assegnatari_competenza_dipendente in protocollo.assegnatari_competenza_dipendenti_ids:
    #         employee = assegnatari_competenza_dipendente.dipendente_id
    #         if employee and employee.department_id and employee.department_id.id == user_department.id:
    #             return True
    #     for assegnatari_conoscenza_dipendente in protocollo.assegnatari_conoscenza_dipendenti_ids:
    #         employee = assegnatari_conoscenza_dipendente.dipendente_id
    #         if employee and employee.department_id and employee.department_id.id == user_department.id:
    #             return True

    # un utente deve poter vedere i protocolli (IN e OUT) REGISTRATI e ASSEGNATI ad un suo UFFICIO FIGLIO
    # check_gruppo = self.user_has_groups(cr, user.id,
    #                                     'seedoo_protocollo.group_vedi_protocolli_ingresso_registrati_ass_uff_fig,seedoo_protocollo.group_vedi_protocolli_uscita_registrati_ass_uff_fig')
    # if check_gruppo and registration_employee and user_department:
    #     for assegnatari_competenza_ufficio in protocollo.assegnatari_competenza_uffici_ids:
    #         department = assegnatari_competenza_ufficio.department_id
    #         if department and self._is_assigned_to_child_departments(cr, uid, user_department, department):
    #             return True
    #     for assegnatari_conoscenza_ufficio in protocollo.assegnatari_conoscenza_uffici_ids:
    #         department = assegnatari_conoscenza_ufficio.department_id
    #         if department and self._is_assigned_to_child_departments(cr, uid, user_department, department):
    #             return True

    # un utente deve poter vedere i protocolli (IN e OUT) REGISTRATI e ASSEGNATI ad un UTENTE di un suo UFFICIO FIGLIO
    # check_gruppo = self.user_has_groups(cr, user.id,
    #                                     'seedoo_protocollo.group_vedi_protocolli_ingresso_registrati_ass_ut_uff_fig,seedoo_protocollo.group_vedi_protocolli_uscita_registrati_ass_ut_uff_fig')
    # if check_gruppo and registration_employee and user_department:
    #     for assegnatari_competenza_dipendente in protocollo.assegnatari_competenza_dipendenti_ids:
    #         employee = assegnatari_competenza_dipendente.dipendente_id
    #         if employee and employee.department_id and self._is_assigned_to_child_departments(cr, uid,
    #                                                                                           user_department,
    #                                                                                           employee.department_id):
    #             return True
    #     for assegnatari_conoscenza_dipendente in protocollo.assegnatari_conoscenza_dipendenti_ids:
    #         employee = assegnatari_conoscenza_dipendente.dipendente_id
    #         if employee and employee.department_id and self._is_assigned_to_child_departments(cr, uid,
    #                                                                                           user_department,
    #                                                                                           employee.department_id):
    #             return True

    # un utente deve poter vedere i protocolli (IN e OUT) REGISTRATI, ASSEGNATI e RIFIUTATI da un UTENTE del suo UFFICIO
    # check_gruppo = self.user_has_groups(cr, user.id,
    #                                     'seedoo_protocollo.group_vedi_protocolli_ingresso_registrati_ass_rif_ut_uff,seedoo_protocollo.group_vedi_protocolli_uscita_registrati_ass_rif_ut_uff')
    # if check_gruppo and registration_employee and is_protocollo_rifiutato_by_department:
    #     return True
    #
    # return False

    # def clear_cache(self):
    #     self._get_protocollo_visibile_ids.clear_cache(self)

    # @tools.ormcache()
    def _get_protocollo_visibile_ids(self, cr, uid, current_user_id):
        protocollo_visible_ids = []
        start_time = time.time()
        employee_obj = self.pool.get('hr.employee')
        department_obj = self.pool.get('hr.department')
        employee_ids = employee_obj.search(cr, uid, [('user_id', '=', current_user_id)])
        if len(employee_ids) > 0:
            employee = employee_obj.browse(cr, uid, employee_ids[0])
            record_list = []

            # un utente deve poter vedere i protocolli in bozza (IN e OUT) creati da lui
            protocollo_ids_drafts = self.search(cr, uid,
                                                [('state', '=', 'draft'), ('user_id.id', '=', employee.user_id.id)])

            # un utente deve poter vedere i protocolli (IN e OUT) registrati da lui
            protocollo_ids_created = self.search(cr, uid, [('registration_employee_id.id', '=', employee.id)])

            # un utente deve poter vedere i protocolli registrati (IN e OUT) assegnati a lui
            # purchè lui o un dipendente del suo ufficio non abbia rifiutato la presa in carico

            cr.execute('''
                    SELECT DISTINCT(pad.protocollo_id) FROM protocollo_assegnatario_dipendente pad JOIN hr_employee e ON pad.dipendente_id = e.id 
                    WHERE e.department_id = %s AND pad.protocollo_id IS NOT NULL AND pad.protocollo_id NOT IN (
                    SELECT pad.protocollo_id FROM protocollo_assegnatario_dipendente pad JOIN hr_employee e ON pad.dipendente_id = e.id
                    JOIN protocollo_stato_dipendente s ON s.id = pad.stato_dipendente_id
                     WHERE pad.tipo IN ('competenza', 'conoscenza')
                    AND e.department_id = %s AND pad.protocollo_id IS NOT NULL AND s.state = 'rifiutato') 
            ''', (employee.department_id.id, employee.department_id.id,))

            protocollo_ids_assigned_not_refused = [res[0] for res in cr.fetchall()]

            # un utente deve poter vedere i protocolli (IN e OUT) REGISTRATI dal suo UFFICIO di appartenenza
            check_gruppo = self.user_has_groups(cr, current_user_id,
                                                'seedoo_protocollo.group_vedi_protocolli_ingresso_registrati_ufficio,seedoo_protocollo.group_vedi_protocolli_uscita_registrati_ufficio')
            if check_gruppo:
                protocollo_ids_department = self.search(cr, uid, [
                    ('registration_employee_id.department_id.id', '=', employee.department_id.id)])
                protocollo_visible_ids.extend(protocollo_ids_department)

            # un utente deve poter vedere i protocolli (IN e OUT) REGISTRATI da un UFFICIO FIGLIO del suo ufficio di appartenenza
            check_gruppo = self.user_has_groups(cr, current_user_id,
                                                'seedoo_protocollo.group_vedi_protocolli_ingresso_registrati_ufficio_figlio,seedoo_protocollo.group_vedi_protocolli_uscita_registrati_ufficio_figlio')
            if check_gruppo:
                deps = department_obj.search(cr, uid, [('parent_id', '=', employee.department_id.id)])
                protocollo_ids_department_childs = self.search(cr, uid, [
                    ('registration_employee_id.department_id.id', 'in', deps)])
                protocollo_visible_ids.extend(protocollo_ids_department_childs)

            # un utente deve poter vedere QUALUNQUE protocollo (IN e OUT) in stato BOZZA appartenente alla sua AOO
            check_gruppo = self.user_has_groups(cr, current_user_id,
                                                'seedoo_protocollo.group_vedi_protocolli_ingresso_bozza, seedoo_protocollo.group_vedi_protocolli_uscita_bozza')
            if check_gruppo:
                protocollo_ids_aoo = self.search(
                    [('state', '=', 'draft'), ('aoo_id', '=', employee.department_id.aoo_id.id)])
                protocollo_visible_ids.extend(protocollo_ids_aoo)

            # un utente deve poter vedere QUALUNQUE protocollo (IN e OUT) REGISTRATO da un utente della sua AOO
            check_gruppo = self.user_has_groups(cr, current_user_id,
                                                'seedoo_protocollo.group_vedi_protocolli_ingresso_registrati,seedoo_protocollo.group_vedi_protocolli_uscita_registrati')
            if check_gruppo:
                protocollo_ids_aoo = self.search([('aoo_id', '=', employee.department_id.aoo_id.id)])
                protocollo_visible_ids.extend(protocollo_ids_aoo)

            # un utente deve poter vedere i protocolli (IN e OUT) REGISTRATI e ASSEGNATI ad un UTENTE del suo UFFICIO di appartenenza
            check_gruppo = self.user_has_groups(cr, current_user_id,
                                                'seedoo_protocollo.group_vedi_protocolli_ingresso_registrati_ass_ut_uff,seedoo_protocollo.group_vedi_protocolli_uscita_registrati_ass_ut_uff')
            if check_gruppo:
                protocollo_visible_ids.extend(self.search(cr, uid, [(
                                                                    'assegnatari_competenza_dipendenti_ids.dipendente_id.department_id.id',
                                                                    '=', employee.department_id.id)]))
                protocollo_visible_ids.extend(self.search(cr, uid[(
                'assegnatari_conoscenza_dipendenti_ids.dipendente_id.department_id.id', '=',
                employee.department_id.id)]))

            # un utente deve poter vedere i protocolli (IN e OUT) REGISTRATI e ASSEGNATI ad un suo UFFICIO FIGLIO
            check_gruppo = self.user_has_groups(cr, current_user_id,
                                                'seedoo_protocollo.group_vedi_protocolli_ingresso_registrati_ass_uff_fig,seedoo_protocollo.group_vedi_protocolli_uscita_registrati_ass_uff_fig')
            if check_gruppo:
                protocollo_visible_ids.extend(self.search(cr, uid, [
                    ('assegnatari_competenza_uffici_ids.department_id.parent_id.id', '=', employee.department_id.id)]))
                protocollo_visible_ids.extend(self.search(cr, uid[
                    ('assegnatari_conoscenza_uffici_ids.department_id.parent_id.id', '=', employee.department_id.id)]))

            # un utente deve poter vedere i protocolli (IN e OUT) REGISTRATI e ASSEGNATI ad un UTENTE di un suo UFFICIO FIGLIO
            check_gruppo = self.user_has_groups(cr, current_user_id,
                                                'seedoo_protocollo.group_vedi_protocolli_ingresso_registrati_ass_ut_uff_fig,seedoo_protocollo.group_vedi_protocolli_uscita_registrati_ass_ut_uff_fig')
            if check_gruppo:
                protocollo_visible_ids.extend(self.search(cr, uid, [(
                                                                    'assegnatari_competenza_dipendenti_ids.dipendente_id.department_id.parent_id.id',
                                                                    '=', employee.department_id.id)]))
                protocollo_visible_ids.extend(self.search(cr, uid[(
                'assegnatari_conoscenza_dipendenti_ids.dipendente_id.department_id.parent_id.id', '=',
                employee.department_id.id)]))

            protocollo_visible_ids.extend(protocollo_ids_drafts)
            protocollo_visible_ids.extend(protocollo_ids_created)
            protocollo_visible_ids.extend(protocollo_ids_assigned_not_refused)

            # tutti gli altri
            protocollo_ids = self.search(cr, uid, [('id', 'not in', protocollo_visible_ids)])

            _logger.info("--- %s len protocollo_ids ---" % (len(protocollo_ids)))

            protocollo_visible_ids = list(set(protocollo_visible_ids))

        _logger.info("--- %s seconds ---" % (time.time() - start_time))
        _logger.info("--- %s start ---" % (start_time))
        _logger.info("--- %s len ---" % (len(protocollo_visible_ids)))

        return protocollo_visible_ids

    def _is_visible(self, cr, uid, ids, name, arg, context=None):
        return {}

    def _is_visible_search(self, cr, uid, obj, name, args, domain=None, context=None):

        if 'params' not in context:
            return []

        protocollo_visible_ids = []
        if context and context.has_key('uid') and context['uid']:
            current_user_id = context['uid']
            protocollo_visible_ids = self._get_protocollo_visibile_ids(cr, uid, current_user_id)

        return [('id', 'in', protocollo_visible_ids)]

    # def write(self, cr, uid, ids, vals, context=None):
    #     protocollo_ids = super(protocollo_protocollo, self).write(cr, uid, ids, vals, context=context)
    #     self.clear_cache()
    #     return protocollo_ids
    #
    # def create(self, cr, uid, vals, context=None):
    #     self.clear_cache()
    #     protocollo_id = super(protocollo_protocollo, self).create(cr, uid, vals, context=context)
    #     return protocollo_id
    #
    # def rifiuta_presa_in_carico(self, cr, uid, ids, context=None):
    #     result = super(protocollo_protocollo, self).rifiuta_presa_in_carico(cr, uid, ids, context=context)
    #     self.clear_cache()
    #     return result

    ####################################################################################################################

    ####################################################################################################################
    # Visibilità dei protocolli nella dashboard
    ####################################################################################################################

    def _bozza_creato_da_me_visibility(self, cr, uid, ids, name, arg, context=None):
        return {}

    def _bozza_creato_da_me_visibility_search(self, cr, uid, obj, name, args, domain=None, context=None):
        protocollo_visible_ids = self.search(cr, 1, [('state', '=', 'draft'), ('user_id', '=', uid)])
        return [('id', 'in', protocollo_visible_ids)]

    def _assegnato_a_me_visibility(self, cr, uid, ids, name, arg, context=None):
        return {}

    def _assegnato_a_me_visibility_search(self, cr, uid, obj, name, args, domain=None, context=None):
        protocollo_visible_ids = []

        protocollo_visible_ids.extend(self.pool.get('protocollo.assegnatario.dipendente').search(cr, 1, [
            ('dipendente_id.user_id.id', '=', uid),
            ('stato_dipendente_id.state', '=', 'assegnato'),
            ('tipo', '=', 'competenza'),
            ('protocollo_id.state', '!=', 'draft')
        ]))
        return [('id', 'in', protocollo_visible_ids)]

    def _assegnato_a_me_cc_visibility(self, cr, uid, ids, name, arg, context=None):
        return {}

    def _assegnato_a_me_cc_visibility_search(self, cr, uid, obj, name, args, domain=None, context=None):
        cr.execute('''
            SELECT p.protocollo_id FROM protocollo_assegnatario_dipendente p, protocollo_protocollo pp, resource_resource r, hr_employee e, protocollo_stato_dipendente s 
            WHERE p.dipendente_id = e.id AND e.resource_id = r.id and pp.id = p.protocollo_id and pp.state != 'draft'
            AND r.user_id = %s AND p.tipo = 'conoscenza' AND p.stato_dipendente_id = s.id AND s.state = 'assegnato' '''
        , (uid,))

        protocollo_visible_ids = [res[0] for res in cr.fetchall()]

        return [('id', 'in', protocollo_visible_ids)]

    def _assegnato_a_mio_ufficio_visibility(self, cr, uid, ids, name, arg, context=None):
        return {}

    def _assegnato_a_mio_ufficio_visibility_search(self, cr, uid, obj, name, args, domain=None, context=None):
        department_ids = self.pool.get('hr.department').search(cr, 1, [('member_ids.user_id.id', '=', uid)])
        if department_ids:
            cr.execute('''
            select pau.protocollo_id from protocollo_assegnatario_ufficio pau join protocollo_protocollo p on pau.protocollo_id = p.id
            where pau.department_id = %s and pau.tipo = 'competenza' and p.state != 'draft' and pau.protocollo_id not in (
            
            select pau.protocollo_id from protocollo_assegnatario_dipendente pad join protocollo_assegnatario_ufficio pau on pad.ufficio_assegnatario_id = pau.id
            join protocollo_stato_dipendente psd on pad.stato_dipendente_id = psd.id 
            
            where psd.state = 'rifiutato' and pau.tipo = 'competenza' and pau.department_id = %s
            )
            '''
                       , (department_ids[0],department_ids[0],))

        protocollo_visible_ids = [res[0] for res in cr.fetchall()]

        return [('id', 'in', protocollo_visible_ids)]


    def _assegnato_a_mio_ufficio_cc_visibility(self, cr, uid, ids, name, arg, context=None):
        return {}

    def _assegnato_a_mio_ufficio_cc_visibility_search(self, cr, uid, obj, name, args, domain=None, context=None):
        protocollo_visible_ids = []
        department_ids = self.pool.get('hr.department').search(cr, 1, [('member_ids.user_id.id', '=', uid)])

        if department_ids:
            cr.execute('''
            select pau.protocollo_id from protocollo_assegnatario_ufficio pau join protocollo_protocollo p on pau.protocollo_id = p.id
            where pau.department_id = %s and pau.tipo = 'conoscenza' and p.state != 'draft' 
            ''', (department_ids[0],))

            protocollo_visible_ids = [res[0] for res in cr.fetchall()]

        return [('id', 'in', protocollo_visible_ids)]

    def _assegnato_da_me_in_attesa_visibility(self, cr, uid, ids, name, arg, context=None):
        return {}

    def _assegnato_da_me_in_attesa_visibility_search(self, cr, uid, obj, name, args, domain=None, context=None):

        cr.execute('''
                select pau.protocollo_id from protocollo_assegnatario_ufficio pau join protocollo_protocollo p on pau.protocollo_id = p.id
                where p.user_id = %s and pau.tipo = 'competenza' and p.state != 'draft' and pau.protocollo_id not in (
                
                select pad.protocollo_id from protocollo_assegnatario_dipendente pad 
                join protocollo_stato_dipendente psd on pad.stato_dipendente_id = psd.id 
                
                where psd.state in  ('rifiutato', 'preso') and pad.tipo = 'competenza' and pad.protocollo_id is not null
                )
            ''', (uid,))

        protocollo_visible_ids = [res[0] for res in cr.fetchall()]

        cr.execute('''
                    select pau.protocollo_id from protocollo_assegnatario_ufficio pau join protocollo_protocollo p on pau.protocollo_id = p.id
                    where p.user_id = %s and pau.tipo = 'competenza' and p.state != 'draft' and pau.protocollo_id not in (
                    
                                select pau.protocollo_id from protocollo_assegnatario_dipendente pad join protocollo_assegnatario_ufficio pau on pad.ufficio_assegnatario_id = pau.id
                                join protocollo_stato_dipendente psd on pad.stato_dipendente_id = psd.id 
                                
                    where psd.state in  ('rifiutato', 'preso') and pad.tipo = 'competenza' and pad.protocollo_id is not null
                    )
            ''', (uid,))

        protocollo_visible_ids.extend([res[0] for res in cr.fetchall()])

        protocollo_visible_ids = list(set(protocollo_visible_ids))

        return [('id', 'in', protocollo_visible_ids)]

    def _assegnato_da_me_in_rifiutato_visibility(self, cr, uid, ids, name, arg, context=None):
        return {}

    def _assegnato_da_me_in_rifiutato_visibility_search(self, cr, uid, obj, name, args, domain=None, context=None):
        cr.execute('''
                        select pau.protocollo_id from protocollo_assegnatario_ufficio pau join protocollo_protocollo p on pau.protocollo_id = p.id
                        where p.user_id = %s and pau.tipo = 'competenza' and p.state != 'draft' and pau.protocollo_id in (
                        
                        select pad.protocollo_id from protocollo_assegnatario_dipendente pad 
                        join protocollo_stato_dipendente psd on pad.stato_dipendente_id = psd.id 
                        
                        where psd.state in  ('rifiutato') and pad.tipo = 'competenza' 
                        )
                    ''', (uid,))

        protocollo_visible_ids = [res[0] for res in cr.fetchall()]

        cr.execute('''
                            select pau.protocollo_id from protocollo_assegnatario_ufficio pau join protocollo_protocollo p on pau.protocollo_id = p.id
                            where p.user_id = %s and pau.tipo = 'competenza' and p.state != 'draft' and pau.protocollo_id in (
                            
                                        select pau.protocollo_id from protocollo_assegnatario_dipendente pad join protocollo_assegnatario_ufficio pau on pad.ufficio_assegnatario_id = pau.id
                                        join protocollo_stato_dipendente psd on pad.stato_dipendente_id = psd.id 
                                        
                            where psd.state in  ('rifiutato') and pad.tipo = 'competenza'
                            )
                    ''', (uid,))

        protocollo_visible_ids.extend([res[0] for res in cr.fetchall()])

        protocollo_visible_ids = list(set(protocollo_visible_ids))

        return [('id', 'in', protocollo_visible_ids)]

    ####################################################################################################################

    ####################################################################################################################
    # Visibilità dei button sui protocolli
    ####################################################################################################################

    def _registra_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False

            if protocollo.state == 'draft':
                check = True

            if check:
                check_gruppi = False
                if protocollo.type == 'in':
                    check_gruppi = self.user_has_groups(cr, uid, 'seedoo_protocollo.group_registra_protocollo_ingresso')
                elif protocollo.type == 'out':
                    check_gruppi = self.user_has_groups(cr, uid, 'seedoo_protocollo.group_registra_protocollo_uscita')
                check = check and check_gruppi

            res.append((protocollo.id, check))

        return dict(res)

    def _annulla_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False

            if protocollo.state in ['registered', 'notified', 'sent', 'waiting', 'error']:
                check = True

            if check:
                check_gruppi = False
                if protocollo.type == 'in':
                    check_gruppi = self.user_has_groups(cr, uid, 'seedoo_protocollo.group_annulla_protocollo_ingresso')
                elif protocollo.type == 'out':
                    check_gruppi = self.user_has_groups(cr, uid, 'seedoo_protocollo.group_annulla_protocollo_uscita')
                check = check and check_gruppi

            if uid == protocollo.user_id.id or uid == SUPERUSER_ID:
                check = check and True
            else:
                check_assegnatari = False
                if check:
                    check_assegnatari = self._check_stato_assegnatario_competenza(cr, uid, protocollo, 'preso')
                check = check and check_assegnatari

            res.append((protocollo.id, check))

        return dict(res)

    def _prendi_in_carico_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False

            if protocollo.state in ('registered', 'notified', 'waiting', 'sent', 'error'):
                check = True

            if check:
                check_gruppi = False
                if protocollo.type == 'in':
                    check_gruppi = self.user_has_groups(cr, uid,
                                                        'seedoo_protocollo.group_prendi_in_carico_protocollo_ingresso')
                elif protocollo.type == 'out':
                    check_gruppi = self.user_has_groups(cr, uid,
                                                        'seedoo_protocollo.group_prendi_in_carico_protocollo_uscita')
                check = check and check_gruppi

            if check:
                check_assegnatari = self._check_stato_assegnatario_competenza(cr, uid, protocollo, 'assegnato')
                check = check and check_assegnatari

            res.append((protocollo.id, check))

        return dict(res)

    def _rifiuta_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False

            if protocollo.state in ('registered', 'notified', 'waiting', 'sent', 'error'):
                check = True

            if check:
                check_gruppi = False
                if protocollo.type == 'in':
                    check_gruppi = self.user_has_groups(cr, uid, 'seedoo_protocollo.group_rifiuta_protocollo_ingresso')
                elif protocollo.type == 'out':
                    check_gruppi = self.user_has_groups(cr, uid, 'seedoo_protocollo.group_rifiuta_protocollo_uscita')
                check = check and check_gruppi

            if check:
                check_assegnatari = self._check_stato_assegnatario_competenza(cr, uid, protocollo, 'assegnato')
                check = check and check_assegnatari

            res.append((protocollo.id, check))

        return dict(res)

    def _modifica_dati_generali_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False

            if protocollo.state in ('registered', 'notified', 'waiting', 'sent', 'error'):
                check = True

            if check:
                check_gruppi = False
                if protocollo.type == 'in':
                    check_gruppi = self.user_has_groups(cr, uid, 'seedoo_protocollo.group_modifica_protocollo_ingresso')
                elif protocollo.type == 'out':
                    check_gruppi = self.user_has_groups(cr, uid, 'seedoo_protocollo.group_modifica_protocollo_uscita')
                check = check and check_gruppi

            if uid == protocollo.user_id.id or uid == SUPERUSER_ID:
                check = check and True
            else:
                check_assegnatari = False
                if check:
                    check_assegnatari = self._check_stato_assegnatario_competenza(cr, uid, protocollo, 'preso')
                check = check and check_assegnatari

            res.append((protocollo.id, check))

        return dict(res)

    def _classifica_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False

            if protocollo.state in ('registered', 'notified', 'waiting', 'sent', 'error'):
                check = True

            if check:
                check_gruppi = False
                if protocollo.type == 'in':
                    check_gruppi = self.user_has_groups(cr, uid,
                                                        'seedoo_protocollo.group_classifica_protocollo_ingresso')
                elif protocollo.type == 'out':
                    check_gruppi = self.user_has_groups(cr, uid, 'seedoo_protocollo.group_classifica_protocollo_uscita')
                check = check and check_gruppi

            if uid == protocollo.user_id.id or uid == SUPERUSER_ID:
                check = check and True
            else:
                check_assegnatari = False
                if check:
                    check_assegnatari = self._check_stato_assegnatario_competenza(cr, uid, protocollo, 'preso')
                check = check and check_assegnatari

            res.append((protocollo.id, check))

        return dict(res)

    def _fascicola_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False

            if protocollo.state in ('registered', 'notified', 'waiting', 'sent', 'error'):
                check = True

            if check:
                check_gruppi = False
                if protocollo.type == 'in':
                    check_gruppi = self.user_has_groups(cr, uid,
                                                        'seedoo_protocollo.group_fascicola_protocollo_ingresso')
                elif protocollo.type == 'out':
                    check_gruppi = self.user_has_groups(cr, uid, 'seedoo_protocollo.group_fascicola_protocollo_uscita')
                check = check and check_gruppi

            if uid == protocollo.user_id.id or uid == SUPERUSER_ID:
                check = check and True
            else:
                check_assegnatari = False
                if check:
                    check_assegnatari = self._check_stato_assegnatario_competenza(cr, uid, protocollo, 'preso')
                check = check and check_assegnatari

            res.append((protocollo.id, check))

        return dict(res)

    def _assegna_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False

            if protocollo.state in ('registered', 'notified', 'waiting', 'sent', 'error'):
                check = True

            if check:
                check_gruppi = False
                if protocollo.type == 'in':
                    check_gruppi = self.user_has_groups(cr, uid, 'seedoo_protocollo.group_assegna_protocollo_ingresso')
                elif protocollo.type == 'out':
                    check_gruppi = self.user_has_groups(cr, uid, 'seedoo_protocollo.group_assegna_protocollo_uscita')
                check = check and check_gruppi

            if uid == protocollo.user_id.id or uid == SUPERUSER_ID:
                check = check and True
            else:
                check_assegnatari = False
                if check:
                    check_assegnatari = self._check_stato_assegnatario_competenza(cr, uid, protocollo, 'preso')
                check = check and check_assegnatari

            res.append((protocollo.id, check))

        return dict(res)

    def _invio_pec_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False

            if protocollo.state == 'registered' and protocollo.type == 'out' and protocollo.pec is True:
                check = True

            if check:
                check_gruppi = self.user_has_groups(cr, uid, 'seedoo_protocollo.group_invia_protocollo_pec_uscita')
                check = check and check_gruppi

            res.append((protocollo.id, check))

        return dict(res)

    def _reinvio_pec_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False

            if protocollo.state in ('waiting', 'sent',
                                    'error') and protocollo.type == 'out' and protocollo.typology.name == 'PEC' and protocollo.sender_receivers:
                for sender_receiver_id in protocollo.sender_receivers.ids:
                    sender_receiver_obj = self.pool.get('protocollo.sender_receiver').browse(cr, uid,
                                                                                             sender_receiver_id,
                                                                                             context=context)
                    if not sender_receiver_obj.pec_invio_status:
                        check = True

            if check:
                check_gruppi = self.user_has_groups(cr, uid, 'seedoo_protocollo.group_reinvia_protocollo_pec_uscita')
                check = check and check_gruppi

            res.append((protocollo.id, check))

        return dict(res)

    def _invio_sharedmail_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False

            if protocollo.state == 'registered' and protocollo.type == 'out' and protocollo.sharedmail is True:
                check = True

            if check:
                check_gruppi = self.user_has_groups(cr, uid,
                                                    'seedoo_protocollo.group_invia_protocollo_sharedmail_uscita')
                check = check and check_gruppi

            res.append((protocollo.id, check))

        return dict(res)

    def _invio_protocollo_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False
            if protocollo.state == 'registered' and protocollo.type == 'out' and protocollo.pec is False and protocollo.sharedmail is False:
                check = True

            if check:
                check_gruppi = self.user_has_groups(cr, uid, 'seedoo_protocollo.group_invia_protocollo_uscita')
                check = check and check_gruppi

            res.append((protocollo.id, check))

        return dict(res)

    def _modifica_pec_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False
            if protocollo.type == 'out' and protocollo.pec is True and protocollo.state in ['waiting', 'sent', 'error']:
                if protocollo.sender_receivers:
                    for sender_receiver_id in protocollo.sender_receivers.ids:
                        sender_receiver_obj = self.pool.get('protocollo.sender_receiver').browse(cr, uid,
                                                                                                 sender_receiver_id,
                                                                                                 context=context)
                        if sender_receiver_obj.pec_errore_consegna_status:
                            check = True

            if check:
                check_gruppi = self.user_has_groups(cr, uid, 'seedoo_protocollo.group_modifica_destinatari_pec_uscita')
                check = check and check_gruppi

            res.append((protocollo.id, check))

        return dict(res)

    def _modifica_email_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False

            if protocollo.type == 'out' and protocollo.sharedmail == True and protocollo.state in ['sent', 'waiting',
                                                                                                   'error']:
                check = True

            if check:
                check_gruppi = self.user_has_groups(cr, uid,
                                                    'seedoo_protocollo.group_modifica_destinatari_email_uscita')
                check = check and check_gruppi

            res.append((protocollo.id, check))

        return dict(res)

    def _aggiungi_pec_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False
            if protocollo.type == 'out' and protocollo.pec is True and protocollo.state in ['waiting', 'sent', 'error']:
                check = True

            if check:
                check_gruppi = self.user_has_groups(cr, uid, 'seedoo_protocollo.group_aggiungi_destinatari_pec_uscita')
                check = check and check_gruppi

            res.append((protocollo.id, check))

        return dict(res)

    def _protocollazione_riservata_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = self.user_has_groups(cr, uid, 'seedoo_protocollo.group_protocollazione_riservata')

            res.append((protocollo.id, check))

        return dict(res)

    def _inserisci_testo_mailpec_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        res = []
        check = False
        configurazione_ids = self.pool.get('protocollo.configurazione').search(cr, uid, [])
        configurazione = self.pool.get('protocollo.configurazione').browse(cr, uid, configurazione_ids[0])
        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:

            if configurazione.inserisci_testo_mailpec:
                check = True

            res.append((protocollo.id, check))

        return dict(res)

    def _aggiungi_allegati_post_registrazione_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        res = []
        check = False
        configurazione_ids = self.pool.get('protocollo.configurazione').search(cr, uid, [])
        configurazione = self.pool.get('protocollo.configurazione').browse(cr, uid, configurazione_ids[0])
        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:

            if configurazione.aggiungi_allegati_post_registrazione:
                check = True

            res.append((protocollo.id, check))

        return dict(res)

    ####################################################################################################################

    _columns = {
        # Visibilità dei protocolli
        'is_visible': fields.function(_is_visible, fnct_search=_is_visible_search, type='boolean', string='Visibile'),

        # Visibilità dei protocolli nella dashboard
        'bozza_creato_da_me_visibility': fields.function(_bozza_creato_da_me_visibility,
                                                         fnct_search=_bozza_creato_da_me_visibility_search,
                                                         type='boolean', string='Visibile'),
        'assegnato_a_me_visibility': fields.function(_assegnato_a_me_visibility,
                                                     fnct_search=_assegnato_a_me_visibility_search, type='boolean',
                                                     string='Visibile'),
        'assegnato_a_me_cc_visibility': fields.function(_assegnato_a_me_cc_visibility,
                                                        fnct_search=_assegnato_a_me_cc_visibility_search,
                                                        type='boolean', string='Visibile'),
        'assegnato_a_mio_ufficio_visibility': fields.function(_assegnato_a_mio_ufficio_visibility,
                                                              fnct_search=_assegnato_a_mio_ufficio_visibility_search,
                                                              type='boolean', string='Visibile'),
        'assegnato_a_mio_ufficio_cc_visibility': fields.function(_assegnato_a_mio_ufficio_cc_visibility,
                                                                 fnct_search=_assegnato_a_mio_ufficio_cc_visibility_search,
                                                                 type='boolean', string='Visibile'),
        'assegnato_da_me_in_attesa_visibility': fields.function(_assegnato_da_me_in_attesa_visibility,
                                                                fnct_search=_assegnato_da_me_in_attesa_visibility_search,
                                                                type='boolean', string='Visibile'),
        'assegnato_da_me_in_rifiutato_visibility': fields.function(_assegnato_da_me_in_rifiutato_visibility,
                                                                   fnct_search=_assegnato_da_me_in_rifiutato_visibility_search,
                                                                   type='boolean', string='Visibile'),

        # Visibilità dei button sui protocolli
        'registra_visibility': fields.function(_registra_visibility, type='boolean', string='Registra'),
        'annulla_visibility': fields.function(_annulla_visibility, type='boolean', string='Annulla'),
        'prendi_in_carico_visibility': fields.function(_prendi_in_carico_visibility, type='boolean',
                                                       string='Prendi in Carico'),
        'rifiuta_visibility': fields.function(_rifiuta_visibility, type='boolean', string='Rifiuta'),
        'modifica_dati_generali_visibility': fields.function(_modifica_dati_generali_visibility, type='boolean',
                                                             string='Modifica Dati Generali'),
        'classifica_visibility': fields.function(_classifica_visibility, type='boolean', string='Classifica'),
        'fascicola_visibility': fields.function(_fascicola_visibility, type='boolean', string='Fascicola'),
        'assegna_visibility': fields.function(_assegna_visibility, type='boolean', string='Assegna'),
        'invio_pec_visibility': fields.function(_invio_pec_visibility, type='boolean', string='Invio PEC'),
        'reinvio_pec_visibility': fields.function(_reinvio_pec_visibility, type='boolean', string='Invio PEC'),
        'invio_sharedmail_visibility': fields.function(_invio_sharedmail_visibility, type='boolean',
                                                       string='Invio E-mail'),
        'invio_protocollo_visibility': fields.function(_invio_protocollo_visibility, type='boolean',
                                                       string='Invio Protocollo'),
        'modifica_pec_visibility': fields.function(_modifica_pec_visibility, type='boolean', string='Modifica PEC'),
        # 'aggiungi_pec_visibility': fields.function(_aggiungi_pec_visibility, type='boolean', string='Aggiungi PEC'),
        'modifica_email_visibility': fields.function(_modifica_email_visibility, type='boolean',
                                                     string='Modifica e-mail'),
        'protocollazione_riservata_visibility': fields.function(_protocollazione_riservata_visibility, type='boolean',
                                                                string='Protocollazione Riservata'),
        'aggiungi_allegati_post_registrazione_visibility': fields.function(
            _aggiungi_allegati_post_registrazione_visibility, type='boolean',
            string='Aggiungi Allegati Post Registrazione'),
        'inserisci_testo_mailpec_visibility': fields.function(_inserisci_testo_mailpec_visibility, type='boolean',
                                                              string='Abilita testo PEC')

    }

    def _default_protocollazione_riservata_visibility(self, cr, uid, context):
        return self.user_has_groups(cr, uid, 'seedoo_protocollo.group_protocollazione_riservata')

    _defaults = {
        'protocollazione_riservata_visibility': _default_protocollazione_riservata_visibility,
    }
