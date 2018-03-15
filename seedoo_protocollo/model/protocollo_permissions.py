# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp import SUPERUSER_ID
from openerp.osv import orm, fields, osv
import logging
import time

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
        assegnazione_obj = self.pool.get('protocollo.assegnazione')
        assegnazione_ids = assegnazione_obj.search(cr, uid, [
            ('assegnatario_employee_id.user_id.id', '=', assegnatario_uid),
            ('protocollo_id', '=', protocollo.id),
            ('tipologia_assegnazione', '=', 'competenza'),
            ('tipologia_assegnatario', '=', 'employee'),
            ('state', '=', stato)
        ])
        if len(assegnazione_ids) > 0:
            return True
        return False


    def _check_stato_assegnatario_competenza_ufficio(self, cr, uid, protocollo, stato, assegnatario_uid=None):
        if not assegnatario_uid:
            assegnatario_uid = uid
        assegnazione_obj = self.pool.get('protocollo.assegnazione')
        assegnazione_ids = assegnazione_obj.search(cr, uid, [
            ('assegnatario_employee_id.user_id.id', '=', assegnatario_uid),
            ('protocollo_id', '=', protocollo.id),
            ('tipologia_assegnazione', '=', 'competenza'),
            ('tipologia_assegnatario', '=', 'employee'),
            ('state', '=', stato),
            ('parent_id', '!=', False)
        ])
        if len(assegnazione_ids) > 0:
            return True
        return False

    ####################################################################################################################
    # Visibilità dei protocolli
    ####################################################################################################################

    # def _is_registered_by_child_departments(self, cr, uid, department, registration_department):
    #     for child_department in department.child_ids:
    #         if child_department.id == registration_department.id or self._is_registered_by_child_departments(cr, uid, child_department, registration_department):
    #             return True
    #     return False
    #
    # def _is_assigned_to_child_departments(self, cr, uid, department, assigned_department):
    #     for child_department in department.child_ids:
    #         if child_department.id == assigned_department.id or self._is_assigned_to_child_departments(cr, uid, child_department, assigned_department):
    #             return True
    #     return False
    #
    # def _check_visible(self, cr, uid, user_employee, protocollo_id):
    #     protocollo = self.browse(cr, uid, protocollo_id)
    #     user = user_employee.user_id
    #     user_department = user_employee.department_id if user_employee.department_id else None
    #     registration_employee = protocollo.registration_employee_id if protocollo.registration_employee_id else None
    #     registration_department = registration_employee.department_id if registration_employee and registration_employee.department_id else None
    #
    #     ################################################################################################################
    #     # Visibilità dei protocolli: casi base
    #     ################################################################################################################
    #
    #     # un utente deve poter vedere i protocolli in bozza (IN e OUT) creati da lui
    #     if protocollo.state == 'draft' and protocollo.user_id and protocollo.user_id.id == user.id:
    #         return True
    #
    #     # un utente deve poter vedere i protocolli (IN e OUT) registrati da lui
    #     if registration_employee and registration_employee.id == user_employee.id:
    #         return True
    #
    #     # un utente deve poter vedere i protocolli registrati (IN e OUT) assegnati a lui
    #     # purchè lui o un dipendente del suo ufficio non abbia rifiutato la presa in carico
    #     is_assegnatario = False
    #     is_protocollo_rifiutato_by_department = False
    #
    #     if registration_employee:
    #         stato_dipendente_obj = self.pool.get('protocollo.stato.dipendente')
    #
    #         employees = self._get_assegnatari_competenza(cr, uid, protocollo)
    #         for employee in employees:
    #             if employee.id == user_employee.id:
    #                 is_assegnatario = True
    #
    #             if employee.department_id and user_department and employee.department_id.id == user_department.id:
    #                 stato_dipendente_ids = stato_dipendente_obj.search(cr, uid, [
    #                     ('dipendente_id', '=', employee.id),
    #                     ('protocollo_id', '=', protocollo.id),
    #                     ('state', '=', 'rifiutato')
    #                 ])
    #                 if len(stato_dipendente_ids) > 0:
    #                     is_protocollo_rifiutato_by_department = True
    #
    #         if not is_assegnatario:
    #             employees = self._get_assegnatari_conoscenza(cr, uid, protocollo)
    #             for employee in employees:
    #                 if employee.id == user_employee.id:
    #                     is_assegnatario = True
    #
    #         if is_assegnatario and not is_protocollo_rifiutato_by_department:
    #             return True
    #
    #     ################################################################################################################
    #     # Visibilità dei protocolli: permessi in configurazione
    #     ################################################################################################################
    #
    #     # un utente deve poter vedere i protocolli (IN e OUT) REGISTRATI dal suo UFFICIO di appartenenza
    #     check_gruppo = False
    #     if protocollo.type == 'in':
    #         check_gruppo = self.user_has_groups(cr, user.id, 'seedoo_protocollo.group_vedi_protocolli_ingresso_registrati_ufficio')
    #     elif protocollo.type == 'out':
    #         check_gruppo = self.user_has_groups(cr, user.id, 'seedoo_protocollo.group_vedi_protocolli_uscita_registrati_ufficio')
    #     if check_gruppo and user_department and registration_department and user_department.id == registration_department.id:
    #         return True
    #
    #     # un utente deve poter vedere i protocolli (IN e OUT) REGISTRATI da un UFFICIO FIGLIO del suo ufficio di appartenenza
    #     check_gruppo = False
    #     if protocollo.type == 'in':
    #         check_gruppo = self.user_has_groups(cr, user.id, 'seedoo_protocollo.group_vedi_protocolli_ingresso_registrati_ufficio_figlio')
    #     elif protocollo.type == 'out':
    #         check_gruppo = self.user_has_groups(cr, user.id, 'seedoo_protocollo.group_vedi_protocolli_uscita_registrati_ufficio_figlio')
    #     if check_gruppo and user_department and registration_department and self._is_registered_by_child_departments(cr, uid, user_department, registration_department):
    #         return True
    #
    #     # un utente deve poter vedere QUALUNQUE protocollo (IN e OUT) in stato BOZZA appartenente alla sua AOO
    #     check_gruppo = False
    #     if protocollo.type == 'in':
    #         check_gruppo = self.user_has_groups(cr, user.id, 'seedoo_protocollo.group_vedi_protocolli_ingresso_bozza')
    #     elif protocollo.type == 'out':
    #         check_gruppo = self.user_has_groups(cr, user.id, 'seedoo_protocollo.group_vedi_protocolli_uscita_bozza')
    #     if check_gruppo and protocollo.state == 'draft' and protocollo.aoo_id and user_department.aoo_id and protocollo.aoo_id.id == user_department.aoo_id.id:
    #         return True
    #
    #     # un utente deve poter vedere QUALUNQUE protocollo (IN e OUT) REGISTRATO da un utente della sua AOO
    #     check_gruppo = False
    #     if protocollo.type == 'in':
    #         check_gruppo = self.user_has_groups(cr, user.id, 'seedoo_protocollo.group_vedi_protocolli_ingresso_registrati')
    #     elif protocollo.type == 'out':
    #         check_gruppo = self.user_has_groups(cr, user.id, 'seedoo_protocollo.group_vedi_protocolli_uscita_registrati')
    #     if check_gruppo and protocollo.aoo_id and registration_department and registration_department.aoo_id and protocollo.aoo_id.id == registration_department.aoo_id.id:
    #         return True
    #
    #     # un utente deve poter vedere i protocolli (IN e OUT) REGISTRATI e ASSEGNATI ad un UTENTE del suo UFFICIO di appartenenza
    #     check_gruppo = False
    #     if protocollo.type == 'in':
    #         check_gruppo = self.user_has_groups(cr, user.id, 'seedoo_protocollo.group_vedi_protocolli_ingresso_registrati_ass_ut_uff')
    #     elif protocollo.type == 'out':
    #         check_gruppo = self.user_has_groups(cr, user.id, 'seedoo_protocollo.group_vedi_protocolli_uscita_registrati_ass_ut_uff')
    #     if check_gruppo and registration_employee and user_department:
    #         for assegnatari_competenza_dipendente in protocollo.assegnatari_competenza_dipendenti_ids:
    #             employee = assegnatari_competenza_dipendente.dipendente_id
    #             if employee and employee.department_id and employee.department_id.id == user_department.id:
    #                 return True
    #         for assegnatari_conoscenza_dipendente in protocollo.assegnatari_conoscenza_dipendenti_ids:
    #             employee = assegnatari_conoscenza_dipendente.dipendente_id
    #             if employee and employee.department_id and employee.department_id.id == user_department.id:
    #                 return True
    #
    #     # un utente deve poter vedere i protocolli (IN e OUT) REGISTRATI e ASSEGNATI ad un suo UFFICIO FIGLIO
    #     check_gruppo = False
    #     if protocollo.type == 'in':
    #         check_gruppo = self.user_has_groups(cr, user.id, 'seedoo_protocollo.group_vedi_protocolli_ingresso_registrati_ass_uff_fig')
    #     elif protocollo.type == 'out':
    #         check_gruppo = self.user_has_groups(cr, user.id, 'seedoo_protocollo.group_vedi_protocolli_uscita_registrati_ass_uff_fig')
    #     if check_gruppo and registration_employee and user_department:
    #         for assegnatari_competenza_ufficio in protocollo.assegnatari_competenza_uffici_ids:
    #             department = assegnatari_competenza_ufficio.department_id
    #             if department and self._is_assigned_to_child_departments(cr, uid, user_department, department):
    #                 return True
    #         for assegnatari_conoscenza_ufficio in protocollo.assegnatari_conoscenza_uffici_ids:
    #             department = assegnatari_conoscenza_ufficio.department_id
    #             if department and self._is_assigned_to_child_departments(cr, uid, user_department, department):
    #                 return True
    #
    #     # un utente deve poter vedere i protocolli (IN e OUT) REGISTRATI e ASSEGNATI ad un UTENTE di un suo UFFICIO FIGLIO
    #     check_gruppo = False
    #     if protocollo.type == 'in':
    #         check_gruppo = self.user_has_groups(cr, user.id, 'seedoo_protocollo.group_vedi_protocolli_ingresso_registrati_ass_ut_uff_fig')
    #     elif protocollo.type == 'out':
    #         check_gruppo = self.user_has_groups(cr, user.id, 'seedoo_protocollo.group_vedi_protocolli_uscita_registrati_ass_ut_uff_fig')
    #     if check_gruppo and registration_employee and user_department:
    #         for assegnatari_competenza_dipendente in protocollo.assegnatari_competenza_dipendenti_ids:
    #             employee = assegnatari_competenza_dipendente.dipendente_id
    #             if employee and employee.department_id and self._is_assigned_to_child_departments(cr, uid, user_department, employee.department_id):
    #                 return True
    #         for assegnatari_conoscenza_dipendente in protocollo.assegnatari_conoscenza_dipendenti_ids:
    #             employee = assegnatari_conoscenza_dipendente.dipendente_id
    #             if employee and employee.department_id and self._is_assigned_to_child_departments(cr, uid, user_department, employee.department_id):
    #                 return True
    #
    #     # un utente deve poter vedere i protocolli (IN e OUT) REGISTRATI, ASSEGNATI e RIFIUTATI da un UTENTE del suo UFFICIO
    #     check_gruppo = False
    #     if protocollo.type == 'in':
    #         check_gruppo = self.user_has_groups(cr, user.id, 'seedoo_protocollo.group_vedi_protocolli_ingresso_registrati_ass_rif_ut_uff')
    #     elif protocollo.type == 'out':
    #         check_gruppo = self.user_has_groups(cr, user.id, 'seedoo_protocollo.group_vedi_protocolli_uscita_registrati_ass_rif_ut_uff')
    #     if check_gruppo and registration_employee and is_protocollo_rifiutato_by_department:
    #         return True
    #
    #     return False

    # def clear_cache(self):
    #     self._get_protocollo_visibile_ids.clear_cache(self)

    #@tools.ormcache()
    def _get_protocollo_visibile_ids(self, cr, uid, current_user_id):
        protocollo_visible_ids = []

        assegnazione_obj = self.pool.get('protocollo.assegnazione')
        department_obj = self.pool.get('hr.department')
        employee_obj = self.pool.get('hr.employee')
        employee_ids = employee_obj.search(cr, uid, [('user_id', '=', current_user_id)])
        if len(employee_ids) > 0:
            employee = employee_obj.browse(cr, uid, employee_ids[0])
            employee_department = employee.department_id if employee.department_id else None

            ############################################################################################################
            # Visibilità dei protocolli: casi base
            ############################################################################################################

            start_time = time.time()
            # un utente deve poter vedere i protocolli in bozza (IN e OUT) creati da lui
            protocollo_ids_drafts = self.search(cr, uid, [
                ('state', '=', 'draft'),
                ('user_id.id', '=', employee.user_id.id)
            ])
            _logger.info("---Query draft %s seconds ---" % (time.time() - start_time))


            start_time = time.time()
            # un utente deve poter vedere i protocolli (IN e OUT) registrati da lui
            protocollo_ids_created = self.search(cr, uid, [('registration_employee_id.id', '=', employee.id)])
            _logger.info("---Query created %s seconds ---" % (time.time() - start_time))


            start_time = time.time()
            # un utente deve poter vedere i protocolli registrati (IN e OUT) assegnati a lui
            # purchè lui o un dipendente del suo ufficio non abbia rifiutato la presa in carico
            cr.execute('''
                SELECT DISTINCT(pa.protocollo_id) 
                FROM protocollo_assegnazione pa, protocollo_protocollo pp
                WHERE pp.registration_employee_id IS NOT NULL AND
                      pa.protocollo_id = pp.id AND
                      pa.tipologia_assegnatario = 'employee' AND 
                      pa.assegnatario_employee_id = %s AND 
                      pa.protocollo_id NOT IN (
                          SELECT DISTINCT(pa.protocollo_id) 
                          FROM protocollo_assegnazione pa
                          WHERE pa.tipologia_assegnatario = 'employee' AND 
                                pa.assegnatario_employee_department_id = %s AND 
                                pa.state = 'rifiutato'
                      )
            ''', (employee.id, employee_department.id))
            protocollo_ids_assigned_not_refused = [res[0] for res in cr.fetchall()]
            _logger.info("---Query assigned_not_refused %s seconds ---" % (time.time() - start_time))


            ############################################################################################################
            # Visibilità dei protocolli: permessi in configurazione
            ############################################################################################################


            start_time = time.time()
            # un utente deve poter vedere i protocolli (IN e OUT) REGISTRATI dal suo UFFICIO di appartenenza
            check_gruppo = self.user_has_groups(cr, current_user_id, 'seedoo_protocollo.group_vedi_protocolli_ingresso_registrati_ufficio,seedoo_protocollo.group_vedi_protocolli_uscita_registrati_ufficio')
            if check_gruppo:
                protocollo_ids_department = self.search(cr, uid, [
                    ('registration_employee_id.department_id.id', '=', employee.department_id.id)
                ])
                protocollo_visible_ids.extend(protocollo_ids_department)
            _logger.info("---Query department  %s seconds ---" % (time.time() - start_time))


            start_time = time.time()
            # un utente deve poter vedere i protocolli (IN e OUT) REGISTRATI da un UFFICIO FIGLIO del suo ufficio di appartenenza.
            check_gruppo = self.user_has_groups(cr, current_user_id, 'seedoo_protocollo.group_vedi_protocolli_ingresso_registrati_ufficio_figlio,seedoo_protocollo.group_vedi_protocolli_uscita_registrati_ufficio_figlio')
            if check_gruppo:
                deps = department_obj.search(cr, uid, [('parent_id', '=', employee.department_id.id)])
                protocollo_ids_department_childs = self.search(cr, uid, [
                    ('registration_employee_id.department_id.id', 'in', deps)
                ])
                protocollo_visible_ids.extend(protocollo_ids_department_childs)
            _logger.info("---Query ids_department_childs  %s seconds ---" % (time.time() - start_time))


            start_time = time.time()
            # un utente deve poter vedere QUALUNQUE protocollo (IN e OUT) in stato BOZZA appartenente alla sua AOO
            check_gruppo = self.user_has_groups(cr, current_user_id, 'seedoo_protocollo.group_vedi_protocolli_ingresso_bozza,seedoo_protocollo.group_vedi_protocolli_uscita_bozza')
            if check_gruppo:
                protocollo_ids_aoo = self.search([
                    ('state', '=', 'draft'), ('aoo_id', '=', employee.department_id.aoo_id.id)
                ])
                protocollo_visible_ids.extend(protocollo_ids_aoo)
            _logger.info("---Query aoo  %s seconds ---" % (time.time() - start_time))


            start_time = time.time()
            # un utente deve poter vedere QUALUNQUE protocollo (IN e OUT) REGISTRATO da un utente della sua AOO
            check_gruppo = self.user_has_groups(cr, current_user_id, 'seedoo_protocollo.group_vedi_protocolli_ingresso_registrati,seedoo_protocollo.group_vedi_protocolli_uscita_registrati')
            if check_gruppo:
                protocollo_ids_aoo = self.search([
                    ('registration_employee_id', '!=', False),
                    ('aoo_id', '=', employee.department_id.aoo_id.id)
                ])
                protocollo_visible_ids.extend(protocollo_ids_aoo)
            _logger.info("---Query aoo 2  %s seconds ---" % (time.time() - start_time))


            start_time = time.time()
            # un utente deve poter vedere i protocolli (IN e OUT) REGISTRATI e ASSEGNATI ad un UTENTE del suo UFFICIO di appartenenza
            check_gruppo = self.user_has_groups(cr, current_user_id, 'seedoo_protocollo.group_vedi_protocolli_ingresso_registrati_ass_ut_uff,seedoo_protocollo.group_vedi_protocolli_uscita_registrati_ass_ut_uff')
            if check_gruppo:
                assegnazione_ids = assegnazione_obj.search(cr, uid, [
                    ('tipologia_assegnatario', '=', 'employee'),
                    ('assegnatario_employee_department_id', '=', employee.department_id.id)
                ])
                protocollo_visible_ids.extend(self.search(cr, uid, [
                    ('registration_employee_id', '!=', False),
                    ('assegnazione_ids', 'in', assegnazione_ids)
                ]))
            _logger.info("---Query registrati_ass_ut_uff  %s seconds ---" % (time.time() - start_time))


            start_time = time.time()
            # un utente deve poter vedere i protocolli (IN e OUT) REGISTRATI e ASSEGNATI ad un suo UFFICIO FIGLIO
            check_gruppo = self.user_has_groups(cr, current_user_id, 'seedoo_protocollo.group_vedi_protocolli_ingresso_registrati_ass_uff_fig,seedoo_protocollo.group_vedi_protocolli_uscita_registrati_ass_uff_fig')
            if check_gruppo:
                assegnazione_ids = assegnazione_obj.search(cr, uid, [
                    ('tipologia_assegnatario', '=', 'department'),
                    ('assegnatario_department_parent_id', '=', employee.department_id.id)
                ])
                protocollo_visible_ids.extend(self.search(cr, uid, [
                    ('registration_employee_id', '!=', False),
                    ('assegnazione_ids', 'in', assegnazione_ids)
                ]))
            _logger.info("---Query _ass_uff_fig  %s seconds ---" % (time.time() - start_time))


            start_time = time.time()
            # un utente deve poter vedere i protocolli (IN e OUT) REGISTRATI e ASSEGNATI ad un UTENTE di un suo UFFICIO FIGLIO
            check_gruppo = self.user_has_groups(cr, current_user_id, 'seedoo_protocollo.group_vedi_protocolli_ingresso_registrati_ass_ut_uff_fig,seedoo_protocollo.group_vedi_protocolli_uscita_registrati_ass_ut_uff_fig')
            if check_gruppo:
                assegnazione_ids = assegnazione_obj.search(cr, uid, [
                    ('tipologia_assegnatario', '=', 'employee'),
                    ('assegnatario_employee_department_id.parent_id.id', '=', employee.department_id.id)
                ])
                protocollo_visible_ids.extend(self.search(cr, uid, [
                    ('registration_employee_id', '!=', False),
                    ('assegnazione_ids', 'in', assegnazione_ids)
                ]))
            _logger.info("---Query ass_ut_uff_fig  %s seconds ---" % (time.time() - start_time))


            start_time = time.time()
            # un utente deve poter vedere i protocolli (IN e OUT) REGISTRATI, ASSEGNATI e RIFIUTATI da un UTENTE del suo UFFICIO
            check_gruppo = self.user_has_groups(cr, current_user_id, 'seedoo_protocollo.group_vedi_protocolli_ingresso_registrati_ass_rif_ut_uff,seedoo_protocollo.group_vedi_protocolli_uscita_registrati_ass_rif_ut_uff')
            if check_gruppo:
                assegnazione_ids = assegnazione_obj.search(cr, uid, [
                    ('tipologia_assegnatario', '=', 'employee'),
                    ('assegnatario_employee_department_id', '=', employee.department_id.id),
                    ('state', '=', 'rifiutato')
                ])
                protocollo_visible_ids.extend(self.search(cr, uid, [
                    ('registration_employee_id', '!=', False),
                    ('assegnazione_ids', 'in', assegnazione_ids)
                ]))
            _logger.info("---Query ass_rif_ut_uff  %s seconds ---" % (time.time() - start_time))


            protocollo_visible_ids.extend(protocollo_ids_drafts)
            protocollo_visible_ids.extend(protocollo_ids_created)
            protocollo_visible_ids.extend(protocollo_ids_assigned_not_refused)

            protocollo_visible_ids = list(set(protocollo_visible_ids))

        #_logger.info("--- %s seconds ---" % (time.time() - start_time_total))
        _logger.info("--- %s start ---" % (start_time))
        _logger.info("--- %s len ---" % (len(protocollo_visible_ids)))

        return protocollo_visible_ids

    def _is_visible(self, cr, uid, ids, name, arg, context=None):
        return {}

    def _is_visible_search(self, cr, uid, obj, name, args, domain=None, context=None):
        if 'params' not in context:
            return []

        if 'action' in context['params'] and context['params']['action'] in [255, 254, 253, 252]:
            return []

        protocollo_visible_ids = []

        if context and context.has_key('uid') and context['uid']:
            current_user_id = context['uid']
            protocollo_visible_ids = self._get_protocollo_visibile_ids(cr, SUPERUSER_ID, current_user_id)
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
        protocollo_visible_ids = self.search(cr, uid, [('state', '=', 'draft'),('user_id', '=', uid)])
        return [('id', 'in', protocollo_visible_ids)]


    def _assegnato_a_me_visibility(self, cr, uid, ids, name, arg, context=None):
        return {}
    def _assegnato_a_me_visibility_search(self, cr, uid, obj, name, args, domain=None, context=None):
        cr.execute('''
            SELECT DISTINCT(pa.protocollo_id) 
            FROM protocollo_assegnazione pa, hr_employee he, resource_resource rr
            WHERE pa.assegnatario_employee_id = he.id AND
                  he.resource_id = rr.id AND
                  rr.user_id = %s AND
                  pa.tipologia_assegnatario = 'employee' AND 
                  pa.tipologia_assegnazione = 'competenza' AND
                  pa.state = 'assegnato' AND
                  pa.parent_id IS NULL
        ''', (uid, ))
        protocollo_visible_ids = [res[0] for res in cr.fetchall()]
        return [('id', 'in', protocollo_visible_ids)]


    def _assegnato_a_me_cc_visibility(self, cr, uid, ids, name, arg, context=None):
        return {}
    def _assegnato_a_me_cc_visibility_search(self, cr, uid, obj, name, args, domain=None, context=None):
        cr.execute('''
            SELECT DISTINCT(pa.protocollo_id) 
            FROM protocollo_assegnazione pa, hr_employee he, resource_resource rr
            WHERE pa.assegnatario_employee_id = he.id AND
                  he.resource_id = rr.id AND
                  rr.user_id = %s AND
                  pa.tipologia_assegnatario = 'employee' AND 
                  pa.tipologia_assegnazione = 'conoscenza' AND
                  pa.state = 'assegnato' AND
                  pa.parent_id IS NULL
        ''', (uid,))
        protocollo_visible_ids = [res[0] for res in cr.fetchall()]
        return [('id', 'in', protocollo_visible_ids)]


    def _assegnato_a_mio_ufficio_visibility(self, cr, uid, ids, name, arg, context=None):
        return {}
    def _assegnato_a_mio_ufficio_visibility_search(self, cr, uid, obj, name, args, domain=None, context=None):
        cr.execute('''
            SELECT DISTINCT(pa.protocollo_id) 
            FROM protocollo_assegnazione pa, hr_department hd, hr_employee he, resource_resource rr
            WHERE pa.assegnatario_department_id = hd.id AND
                  hd.id=he.department_id AND
                  he.resource_id = rr.id AND
                  rr.user_id = %s AND
                  pa.tipologia_assegnatario = 'department' AND 
                  pa.tipologia_assegnazione = 'competenza' AND
                  pa.state = 'assegnato'
        ''', (uid,))
        protocollo_visible_ids = [res[0] for res in cr.fetchall()]
        return [('id', 'in', protocollo_visible_ids)]


    def _assegnato_a_mio_ufficio_cc_visibility(self, cr, uid, ids, name, arg, context=None):
        return {}
    def _assegnato_a_mio_ufficio_cc_visibility_search(self, cr, uid, obj, name, args, domain=None, context=None):
        cr.execute('''
            SELECT DISTINCT(pa.protocollo_id) 
            FROM protocollo_assegnazione pa, hr_department hd, hr_employee he, resource_resource rr
            WHERE pa.assegnatario_department_id = hd.id AND
                  hd.id=he.department_id AND
                  he.resource_id = rr.id AND
                  rr.user_id = %s AND
                  pa.tipologia_assegnatario = 'department' AND 
                  pa.tipologia_assegnazione = 'conoscenza' AND
                  pa.state = 'assegnato'
        ''', (uid,))
        protocollo_visible_ids = [res[0] for res in cr.fetchall()]
        return [('id', 'in', protocollo_visible_ids)]


    def _assegnato_da_me_in_attesa_visibility(self, cr, uid, ids, name, arg, context=None):
        return {}
    def _assegnato_da_me_in_attesa_visibility_search(self, cr, uid, obj, name, args, domain=None, context=None):
        cr.execute('''
            SELECT DISTINCT(pa.protocollo_id) 
            FROM protocollo_protocollo pp, protocollo_assegnazione pa, hr_employee he, resource_resource rr
            WHERE pp.id = pa.protocollo_id AND 
                  pa.assegnatore_id = he.id AND
                  he.resource_id = rr.id AND
                  rr.user_id = %s AND
                  pp.registration_employee_id IS NOT NULL AND
                  pa.tipologia_assegnazione = 'competenza' AND
                  pa.state = 'assegnato' AND
                  (pa.tipologia_assegnatario = 'department' OR (pa.tipologia_assegnatario = 'employee' AND pa.parent_id IS NULL)) 
        ''', (uid,))
        protocollo_visible_ids = [res[0] for res in cr.fetchall()]
        return [('id', 'in', protocollo_visible_ids)]


    def _assegnato_da_me_in_rifiutato_visibility(self, cr, uid, ids, name, arg, context=None):
        return {}
    def _assegnato_da_me_in_rifiutato_visibility_search(self, cr, uid, obj, name, args, domain=None, context=None):
        cr.execute('''
            SELECT DISTINCT(pa.protocollo_id) 
            FROM protocollo_protocollo pp, protocollo_assegnazione pa, hr_employee he, resource_resource rr
            WHERE pp.id = pa.protocollo_id AND 
                  pa.assegnatore_id = he.id AND
                  he.resource_id = rr.id AND
                  rr.user_id = %s AND
                  pp.registration_employee_id IS NOT NULL AND
                  pa.tipologia_assegnazione = 'competenza' AND
                  pa.state = 'rifiutato'
        ''', (uid,))
        protocollo_visible_ids = [res[0] for res in cr.fetchall()]
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
                if self._check_stato_assegnatario_competenza_ufficio(cr, uid, protocollo, 'assegnato'):
                    check_gruppi = False
                    if protocollo.type == 'in':
                        check_gruppi = self.user_has_groups(cr, uid, 'seedoo_protocollo.group_prendi_in_carico_protocollo_ingresso')
                    elif protocollo.type == 'out':
                        check_gruppi = self.user_has_groups(cr, uid, 'seedoo_protocollo.group_prendi_in_carico_protocollo_uscita')
                    check = check and check_gruppi
                elif self._check_stato_assegnatario_competenza(cr, uid, protocollo, 'assegnato'):
                    check = True
                else:
                    check = False

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
                if self._check_stato_assegnatario_competenza_ufficio(cr, uid, protocollo, 'assegnato'):
                    check_gruppi = False
                    if protocollo.type == 'in':
                        check_gruppi = self.user_has_groups(cr, uid, 'seedoo_protocollo.group_rifiuta_protocollo_ingresso')
                    elif protocollo.type == 'out':
                        check_gruppi = self.user_has_groups(cr, uid, 'seedoo_protocollo.group_rifiuta_protocollo_uscita')
                    check = check and check_gruppi
                elif self._check_stato_assegnatario_competenza(cr, uid, protocollo, 'assegnato'):
                    check = True
                else:
                    check = False

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
                    check_gruppi = self.user_has_groups(cr, uid, 'seedoo_protocollo.group_classifica_protocollo_ingresso')
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
                    check_gruppi = self.user_has_groups(cr, uid, 'seedoo_protocollo.group_fascicola_protocollo_ingresso')
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


    def _aggiungi_assegnatari_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False

            if protocollo.state == 'draft':
                check = True

            if check:
                check_gruppi = False
                if protocollo.type == 'in':
                    check_gruppi = self.user_has_groups(cr, uid, 'seedoo_protocollo.group_aggiungi_assegnatari_protocollo_ingresso')
                elif protocollo.type == 'out':
                    check_gruppi = self.user_has_groups(cr, uid, 'seedoo_protocollo.group_aggiungi_assegnatari_protocollo_uscita')
                check = check and check_gruppi

            if uid==protocollo.user_id.id or uid==SUPERUSER_ID:
                check = check and True

            res.append((protocollo.id, check))

        return dict(res)


    def _assegna_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False

            if protocollo.state in ('registered', 'notified', 'waiting', 'sent', 'error') and not protocollo.assegnazione_competenza_ids:
                check = True

            if check:
                check_gruppi = False
                if protocollo.type == 'in':
                    check_gruppi = self.user_has_groups(cr, uid, 'seedoo_protocollo.group_assegna_protocollo_ingresso')
                elif protocollo.type == 'out':
                    check_gruppi = self.user_has_groups(cr, uid, 'seedoo_protocollo.group_assegna_protocollo_uscita')
                check = check and check_gruppi

            if uid==protocollo.user_id.id or uid==SUPERUSER_ID:
                check = check and True

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

            if uid == protocollo.user_id.id or uid == SUPERUSER_ID:
                check = check and True
            else:
                check_assegnatari = False
                if check:
                    check_assegnatari = self._check_stato_assegnatario_competenza(cr, uid, protocollo, 'preso')
                check = check and check_assegnatari

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
                check_gruppi = self.user_has_groups(cr, uid, 'seedoo_protocollo.group_invia_protocollo_sharedmail_uscita')
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
                        sender_receiver_obj = self.pool.get('protocollo.sender_receiver').browse(cr, uid, sender_receiver_id, context=context)
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

            if protocollo.type=='out' and protocollo.sharedmail==True and protocollo.state in ['sent', 'waiting', 'error']:
                check = True

            if check:
                check_gruppi = self.user_has_groups(cr, uid, 'seedoo_protocollo.group_modifica_destinatari_email_uscita')
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
        'bozza_creato_da_me_visibility': fields.function(_bozza_creato_da_me_visibility, fnct_search=_bozza_creato_da_me_visibility_search, type='boolean', string='Visibile'),
        'assegnato_a_me_visibility': fields.function(_assegnato_a_me_visibility, fnct_search=_assegnato_a_me_visibility_search, type='boolean', string='Visibile'),
        'assegnato_a_me_cc_visibility': fields.function(_assegnato_a_me_cc_visibility, fnct_search=_assegnato_a_me_cc_visibility_search, type='boolean', string='Visibile'),
        'assegnato_a_mio_ufficio_visibility': fields.function(_assegnato_a_mio_ufficio_visibility, fnct_search=_assegnato_a_mio_ufficio_visibility_search, type='boolean', string='Visibile'),
        'assegnato_a_mio_ufficio_cc_visibility': fields.function(_assegnato_a_mio_ufficio_cc_visibility, fnct_search=_assegnato_a_mio_ufficio_cc_visibility_search, type='boolean', string='Visibile'),
        'assegnato_da_me_in_attesa_visibility': fields.function(_assegnato_da_me_in_attesa_visibility, fnct_search=_assegnato_da_me_in_attesa_visibility_search, type='boolean', string='Visibile'),
        'assegnato_da_me_in_rifiutato_visibility': fields.function(_assegnato_da_me_in_rifiutato_visibility, fnct_search=_assegnato_da_me_in_rifiutato_visibility_search, type='boolean', string='Visibile'),

        # Visibilità dei button sui protocolli
        'registra_visibility': fields.function(_registra_visibility, type='boolean', string='Registra'),
        'annulla_visibility': fields.function(_annulla_visibility, type='boolean', string='Annulla'),
        'prendi_in_carico_visibility': fields.function(_prendi_in_carico_visibility, type='boolean', string='Prendi in Carico'),
        'rifiuta_visibility': fields.function(_rifiuta_visibility, type='boolean', string='Rifiuta'),
        'modifica_dati_generali_visibility': fields.function(_modifica_dati_generali_visibility, type='boolean', string='Modifica Dati Generali'),
        'classifica_visibility': fields.function(_classifica_visibility, type='boolean', string='Classifica'),
        'fascicola_visibility': fields.function(_fascicola_visibility, type='boolean', string='Fascicola'),
        'aggiungi_assegnatari_visibility': fields.function(_aggiungi_assegnatari_visibility, type='boolean', string='Aggiungi Assegnatari'),
        'assegna_visibility': fields.function(_assegna_visibility, type='boolean', string='Assegna'),
        'invio_pec_visibility': fields.function(_invio_pec_visibility, type='boolean', string='Invio PEC'),
        'invio_sharedmail_visibility': fields.function(_invio_sharedmail_visibility, type='boolean', string='Invio E-mail'),
        'invio_protocollo_visibility': fields.function(_invio_protocollo_visibility, type='boolean', string='Invio Protocollo'),
        'modifica_pec_visibility': fields.function(_modifica_pec_visibility, type='boolean', string='Modifica PEC'),
        # 'aggiungi_pec_visibility': fields.function(_aggiungi_pec_visibility, type='boolean', string='Aggiungi PEC'),
        'modifica_email_visibility': fields.function(_modifica_email_visibility, type='boolean', string='Modifica e-mail'),
        'protocollazione_riservata_visibility': fields.function(_protocollazione_riservata_visibility, type='boolean', string='Protocollazione Riservata'),
        'aggiungi_allegati_post_registrazione_visibility': fields.function(_aggiungi_allegati_post_registrazione_visibility, type='boolean', string='Aggiungi Allegati Post Registrazione'),
        'inserisci_testo_mailpec_visibility': fields.function(_inserisci_testo_mailpec_visibility, type='boolean', string='Abilita testo PEC')

    }

    def _default_aggiungi_assegnatari_visibility(self, cr, uid, context):
        return self.user_has_groups(cr, uid, 'seedoo_protocollo.group_aggiungi_assegnatari_protocollo_ingresso,seedoo_protocollo.group_aggiungi_assegnatari_protocollo_uscita')

    def _default_protocollazione_riservata_visibility(self, cr, uid, context):
        return self.user_has_groups(cr, uid, 'seedoo_protocollo.group_protocollazione_riservata')

    _defaults = {
        'aggiungi_assegnatari_visibility': _default_aggiungi_assegnatari_visibility,
        'protocollazione_riservata_visibility': _default_protocollazione_riservata_visibility,
    }

