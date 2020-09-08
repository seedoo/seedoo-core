# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.
import datetime
import logging
import time
import functools

from openerp import SUPERUSER_ID, api, _
from openerp.osv import fields, osv
from openerp.exceptions import AccessError

_logger = logging.getLogger(__name__)


class protocollo_protocollo(osv.Model):
    _inherit = 'protocollo.protocollo'

    def _get_protocolli(self, cr, uid, ids):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]

        protocolli = self.browse(cr, uid, ids, {'skip_check': True})
        return protocolli

    def _check_stato_assegnatario_competenza(self, cr, uid, protocollo, stato, assegnatario_employee_id=None):
        department_domain = []
        domain = [
            ('protocollo_id', '=', protocollo.id),
            ('tipologia_assegnazione', '=', 'competenza'),
            ('tipologia_assegnatario', '=', 'employee'),
            ('state', '=', stato)
        ]
        if assegnatario_employee_id:
            domain.append(('assegnatario_employee_id.id', '=', assegnatario_employee_id))
            department_domain.append(('member_ids.id', '=', assegnatario_employee_id))
        else:
            domain.append(('assegnatario_employee_id.user_id.id', '=', uid))
            department_domain.append(('member_ids.user_id.id', '=', uid))
        assegnazione_obj = self.pool.get('protocollo.assegnazione')
        assegnazione_ids = assegnazione_obj.search(cr, uid, domain)
        department_ids = self.pool.get('hr.department').search(cr, uid, department_domain)
        for assegnazione_id in assegnazione_ids:
            assegnazione = assegnazione_obj.browse(cr, uid, assegnazione_id)
            if not assegnazione.parent_id or (assegnazione.parent_id and assegnazione.parent_id.assegnatario_department_id.id in department_ids):
                return True
        return False

    def _check_stato_assegnatore_competenza(self, cr, uid, protocollo, stato, assegnatore_employee_id=None, assegnazione_domain=[]):
        assegnazione_obj = self.pool.get('protocollo.assegnazione')
        domain = [
            ('protocollo_id', '=', protocollo.id),
            ('tipologia_assegnazione', '=', 'competenza')
        ]
        if assegnatore_employee_id:
            domain.append(('assegnatore_id.id', '=', assegnatore_employee_id))
        else:
            domain.append(('assegnatore_id.user_id.id', '=', uid))
        if stato:
            domain.append(('state', '=', stato))
        for assegnazione_domain_item in assegnazione_domain:
            domain.append(assegnazione_domain_item)
        assegnazione_ids = assegnazione_obj.search(cr, uid, domain)
        if len(assegnazione_ids) > 0:
            return True
        return False

    def _check_stato_assegnatario_competenza_ufficio(self, cr, uid, protocollo, stato, assegnatario_employee_id=None):
        if assegnatario_employee_id:
            cr.execute('''
                SELECT DISTINCT(pa.protocollo_id)
                FROM protocollo_assegnazione pa, hr_employee he, resource_resource rr
                WHERE pa.protocollo_id = %s AND
                      pa.tipologia_assegnatario = 'department' AND 
                      pa.tipologia_assegnazione = 'competenza' AND
                      pa.state = %s AND
                      pa.assegnatario_department_id = he.department_id AND
                      he.id = %s AND
                      he.resource_id = rr.id AND
                      rr.active = TRUE
            ''', (str(protocollo.id), stato, str(assegnatario_employee_id)))
        else:
            cr.execute('''
                SELECT DISTINCT(pa.protocollo_id)
                FROM protocollo_assegnazione pa, hr_employee he, resource_resource rr
                WHERE pa.protocollo_id = %s AND
                      pa.tipologia_assegnatario = 'department' AND 
                      pa.tipologia_assegnazione = 'competenza' AND
                      pa.state = %s AND
                      pa.assegnatario_department_id = he.department_id AND
                      he.resource_id = rr.id AND
                      rr.user_id = %s AND
                      rr.active = TRUE
            ''', (str(protocollo.id), stato, str(uid)))
        assegnazione_ids = [res[0] for res in cr.fetchall()]
        if len(assegnazione_ids) > 0:
            return True
        return False

    def _check_stato_assegnatario_conoscenza(self, cr, uid, protocollo, stato, assegnatario_uid=None):
        if not assegnatario_uid:
            assegnatario_uid = uid
        assegnazione_obj = self.pool.get('protocollo.assegnazione')
        assegnazione_ids = assegnazione_obj.search(cr, uid, [
            ('assegnatario_employee_id.user_id.id', '=', assegnatario_uid),
            ('protocollo_id', '=', protocollo.id),
            ('tipologia_assegnazione', '=', 'conoscenza'),
            ('tipologia_assegnatario', '=', 'employee'),
            ('state', '=', stato)
        ])
        department_ids = self.pool.get('hr.department').search(cr, uid, [('member_ids.user_id.id', '=', assegnatario_uid)])
        for assegnazione_id in assegnazione_ids:
            assegnazione = assegnazione_obj.browse(cr, uid, assegnazione_id)
            if not assegnazione.parent_id or (assegnazione.parent_id and assegnazione.parent_id.assegnatario_department_id.id in department_ids):
                return True
        return False

    def _check_stato_assegnatario_conoscenza_ufficio(self, cr, uid, protocollo, stato, assegnatario_uid=None):
        if not assegnatario_uid:
            assegnatario_uid = uid
        cr.execute('''
                    SELECT DISTINCT(pa.protocollo_id)
                    FROM protocollo_assegnazione pa, hr_employee he, resource_resource rr
                    WHERE pa.protocollo_id = %s AND
                          pa.tipologia_assegnatario = 'department' AND 
                          pa.tipologia_assegnazione = 'conoscenza' AND
                          pa.state = %s AND
                          pa.assegnatario_department_id = he.department_id AND
                          he.resource_id = rr.id AND
                          rr.user_id = %s AND
                          rr.active = TRUE AND 
                          pa.id NOT IN (
                                SELECT pa2.parent_id
                                FROM protocollo_assegnazione pa2
                                WHERE pa.protocollo_id = pa2.protocollo_id AND
                                      pa2.tipologia_assegnatario = 'employee' AND
                                      pa2.tipologia_assegnazione = 'conoscenza' AND
                                      pa2.state != %s AND
                                      pa2.parent_id IS NOT NULL AND
                                      pa2.assegnatario_employee_id = he.id
                          )
                ''', (str(protocollo.id), stato, str(assegnatario_uid), stato))
        assegnazione_ids = [res[0] for res in cr.fetchall()]
        if len(assegnazione_ids) > 0:
            return True
        return False

    def get_protocollo_types_by_group(self, cr, uid, module, group_xml_start_id, group_xml_end_id, mapping={'ingresso': 'in', 'uscita': 'out'}):
        types = []
        for type_key in mapping.keys():
            group_xml_id = module + '.' + group_xml_start_id + type_key + group_xml_end_id
            check_gruppo = self.user_has_groups(cr, uid, group_xml_id)
            if check_gruppo:
                types.append(mapping[type_key])
        return types

    ####################################################################################################################
    # Visibilità dei protocolli
    ####################################################################################################################
    def get_protocollo_base_visibile_ids(self, cr, uid, current_user_id, archivio_ids, archivio_ids_str,
                                          employee_ids, employee_ids_str,
                                          employee_department_ids, employee_department_ids_str, protocollo_ids_filter):
        protocollo_visible_ids = []

        start_time = time.time()
        # un utente deve poter vedere i protocolli in bozza (IN e OUT) creati da lui
        cr.execute('''
            SELECT DISTINCT(pp.id)
            FROM protocollo_protocollo pp
            WHERE pp.state = 'draft' AND 
                  pp.user_id = %s AND 
                  pp.archivio_id IN (''' + archivio_ids_str + ''')
                  ''' + protocollo_ids_filter + '''
        ''', (current_user_id, ))
        protocollo_ids_drafts = [res[0] for res in cr.fetchall()]
        protocollo_visible_ids.extend(protocollo_ids_drafts)
        _logger.debug("---Query draft %s seconds ---" % (time.time() - start_time))

        start_time = time.time()
        # un utente deve poter vedere i protocolli (IN e OUT) registrati da lui
        if employee_ids:
            cr.execute('''
                SELECT DISTINCT(pp.id)
                FROM protocollo_protocollo pp
                WHERE pp.registration_date IS NOT NULL AND
                      pp.registration_employee_id IN (''' + employee_ids_str + ''') AND
                      pp.archivio_id IN (''' + archivio_ids_str + ''')
                      ''' + protocollo_ids_filter + '''
            ''')
            protocollo_ids_created = [res[0] for res in cr.fetchall()]
            protocollo_visible_ids.extend(protocollo_ids_created)
        _logger.debug("---Query created %s seconds ---" % (time.time() - start_time))

        start_time = time.time()
        # un utente deve poter vedere i protocolli registrati (IN e OUT) assegnati a lui o al suo ufficio,
        # purchè lui o un dipendente del suo ufficio non abbia rifiutato la presa in carico
        if employee_ids and employee_department_ids:
            cr.execute('''
                SELECT DISTINCT(pa.protocollo_id)
                FROM protocollo_assegnazione pa, protocollo_protocollo pp
                WHERE pp.registration_date IS NOT NULL AND
                      pa.protocollo_id = pp.id AND
                      (
                          (pa.tipologia_assegnatario = 'employee' AND pa.assegnatario_employee_id IN (''' + employee_ids_str + ''') AND pa.parent_id IS NULL) OR 
                          (pa.tipologia_assegnatario = 'department' AND pa.assegnatario_department_id  IN (''' + employee_department_ids_str + '''))
                      ) AND
                      pa.state != 'rifiutato' AND 
                      pa.archivio_id IN (''' + archivio_ids_str + ''')
                      ''' + protocollo_ids_filter + '''
            ''')
            protocollo_ids_assigned_not_refused = [res[0] for res in cr.fetchall()]
            protocollo_visible_ids.extend(protocollo_ids_assigned_not_refused)
        _logger.debug("---Query assigned_not_refused %s seconds ---" % (time.time() - start_time))

        # start_time = time.time()
        # un utente deve poter vedere i protocolli (IN e OUT) registrati di cui è autore della assegnazione per
        # competenza (assegnatore)
        # if employee_ids:
        #     cr.execute('''
        #         SELECT DISTINCT(pa.protocollo_id)
        #         FROM protocollo_assegnazione pa, protocollo_protocollo pp
        #         WHERE pp.registration_date IS NOT NULL AND
        #               pa.protocollo_id = pp.id AND
        #               pa.assegnatore_id IN (''' + employee_ids_str + ''') AND
        #               pa.tipologia_assegnazione = 'competenza' AND
        #               pa.parent_id IS NULL AND
        #               pp.archivio_id IN (''' + archivio_ids_str + ''')
        #     ''')
        #     protocollo_ids_assegnatore = [res[0] for res in cr.fetchall()]
        #     protocollo_visible_ids.extend(protocollo_ids_assegnatore)
        # _logger.debug("---Query assegnatore %s seconds ---" % (time.time() - start_time))

        return protocollo_visible_ids


    def get_protocollo_configuration_visibile_ids(self, cr, uid, current_user_id, archivio_ids, archivio_ids_str,
                                          employee_ids, employee_ids_str,
                                          employee_department_ids, employee_department_ids_str,
                                          employee_department_child_ids, employee_department_child_ids_str, aoo_ids, protocollo_ids_filter):
        protocollo_visible_ids = []
        aoo_id_str = ', '.join(map(str, aoo_ids))
        assegnazione_obj = self.pool.get('protocollo.assegnazione')

        start_time = time.time()
        # un utente deve poter vedere i protocolli (IN, OUT, INTERNAL) REGISTRATI dal suo UFFICIO di appartenenza
        types = self.get_protocollo_types_by_group(cr, current_user_id, 'seedoo_protocollo', 'group_vedi_protocolli_', '_registrati_ufficio')
        if types and employee_department_ids:
            cr.execute('''
                SELECT DISTINCT(pp.id)
                FROM protocollo_protocollo pp
                WHERE pp.registration_date IS NOT NULL AND
                      pp.registration_employee_department_id IN (''' + employee_department_ids_str + ''') AND
                      pp.reserved=FALSE AND
                      pp.type IN (''' + str(types).strip('[]') + ''') AND
                      pp.archivio_id IN (''' + archivio_ids_str + ''')
                      ''' + protocollo_ids_filter + '''
            ''')
            protocollo_ids_department = [res[0] for res in cr.fetchall()]
            protocollo_visible_ids.extend(protocollo_ids_department)
        _logger.debug("---Query department  %s seconds ---" % (time.time() - start_time))

        start_time = time.time()
        # un utente deve poter vedere i protocolli (IN, OUT, INTERNAL) REGISTRATI da un UFFICIO FIGLIO del suo ufficio di appartenenza.
        types = self.get_protocollo_types_by_group(cr, current_user_id, 'seedoo_protocollo', 'group_vedi_protocolli_', '_registrati_ufficio_figlio')
        if types and employee_department_child_ids:
            cr.execute('''
                SELECT DISTINCT(pp.id)
                FROM protocollo_protocollo pp
                WHERE pp.registration_date IS NOT NULL AND
                      pp.registration_employee_department_id IN (''' + employee_department_child_ids_str + ''') AND
                      pp.reserved=FALSE AND
                      pp.type IN (''' + str(types).strip('[]') + ''') AND
                      pp.archivio_id IN (''' + archivio_ids_str + ''')
                      ''' + protocollo_ids_filter + '''
            ''')
            protocollo_ids_department_childs = [res[0] for res in cr.fetchall()]
            protocollo_visible_ids.extend(protocollo_ids_department_childs)
        _logger.debug("---Query ids_department_childs  %s seconds ---" % (time.time() - start_time))

        start_time = time.time()
        # un utente deve poter vedere QUALUNQUE protocollo (IN, OUT, INTERNAL) in stato BOZZA appartenente alla sua AOO
        types = self.get_protocollo_types_by_group(cr, current_user_id, 'seedoo_protocollo', 'group_vedi_protocolli_', '_bozza')
        if types and aoo_ids:
            cr.execute('''
                SELECT DISTINCT(pp.id)
                FROM protocollo_protocollo pp
                WHERE pp.type IN (''' + str(types).strip('[]') + ''') AND
                      pp.state = 'draft' AND
                      pp.aoo_id IN (''' + aoo_id_str + ''') AND
                      pp.archivio_id IN (''' + archivio_ids_str + ''')
                      ''' + protocollo_ids_filter + '''
            ''')
            protocollo_ids_aoo = [res[0] for res in cr.fetchall()]
            protocollo_visible_ids.extend(protocollo_ids_aoo)
        _logger.debug("---Query aoo  %s seconds ---" % (time.time() - start_time))

        start_time = time.time()
        # un utente deve poter vedere QUALUNQUE protocollo (IN, OUT, INTERNAL) REGISTRATO da un utente della sua AOO
        types = self.get_protocollo_types_by_group(cr, current_user_id, 'seedoo_protocollo', 'group_vedi_protocolli_', '_registrati')
        if types and aoo_ids:
            cr.execute('''
                SELECT DISTINCT(pp.id)
                FROM protocollo_protocollo pp
                WHERE pp.type IN (''' + str(types).strip('[]') + ''') AND
                      pp.registration_date IS NOT NULL AND
                      pp.aoo_id IN (''' + aoo_id_str + ''') AND
                      pp.archivio_id IN (''' + archivio_ids_str + ''')
                      ''' + protocollo_ids_filter + '''
            ''')
            protocollo_ids_aoo = [res[0] for res in cr.fetchall()]
            protocollo_visible_ids.extend(protocollo_ids_aoo)
        _logger.debug("---Query aoo 2  %s seconds ---" % (time.time() - start_time))

        start_time = time.time()
        # un utente deve poter vedere i protocolli (IN, OUT, INTERNAL) REGISTRATI e ASSEGNATI ad un UTENTE del suo UFFICIO di appartenenza
        types = self.get_protocollo_types_by_group(cr, current_user_id, 'seedoo_protocollo', 'group_vedi_protocolli_', '_registrati_ass_ut_uff')
        if types and employee_department_ids:
            cr.execute('''
                SELECT DISTINCT(pa.protocollo_id)
                FROM protocollo_assegnazione pa, protocollo_protocollo pp
                WHERE pp.type IN (''' + str(types).strip('[]') + ''') AND
                      pp.registration_date IS NOT NULL AND
                      pp.reserved = FALSE AND
                      pa.archivio_id IN (''' + archivio_ids_str + ''') AND 
                      pp.id = pa.protocollo_id AND
                      pa.tipologia_assegnatario = 'employee' AND
                      pa.parent_id IS NULL AND
                      pa.assegnatario_employee_department_id IN (''' + employee_department_ids_str + ''') AND
                      pa.state != 'rifiutato'
                      ''' + protocollo_ids_filter + '''
            ''')
            protocollo_ids_registrati_ass_ut_uff = [res[0] for res in cr.fetchall()]
            protocollo_visible_ids.extend(protocollo_ids_registrati_ass_ut_uff)
        _logger.debug("---Query registrati_ass_ut_uff  %s seconds ---" % (time.time() - start_time))

        start_time = time.time()
        # un utente deve poter vedere i protocolli (IN, OUT, INTERNAL) REGISTRATI e ASSEGNATI ad un suo UFFICIO FIGLIO
        types = self.get_protocollo_types_by_group(cr, current_user_id, 'seedoo_protocollo', 'group_vedi_protocolli_', '_registrati_ass_uff_fig')
        if types and employee_department_child_ids:
            cr.execute('''
                SELECT DISTINCT(pa.protocollo_id)
                FROM protocollo_assegnazione pa, protocollo_protocollo pp
                WHERE pp.type IN (''' + str(types).strip('[]') + ''') AND
                      pp.registration_date IS NOT NULL AND
                      pp.reserved = FALSE AND
                      pa.archivio_id IN (''' + archivio_ids_str + ''') AND 
                      pp.id = pa.protocollo_id AND
                      pa.tipologia_assegnatario = 'department' AND
                      pa.assegnatario_department_id IN (''' + employee_department_child_ids_str + ''') AND
                      pa.state != 'rifiutato'
                      ''' + protocollo_ids_filter + '''
            ''')
            protocollo_ids_ass_uff_fig = [res[0] for res in cr.fetchall()]
            protocollo_visible_ids.extend(protocollo_ids_ass_uff_fig)
        _logger.debug("---Query ass_uff_fig  %s seconds ---" % (time.time() - start_time))

        start_time = time.time()
        # un utente deve poter vedere i protocolli (IN e OUT) REGISTRATI e ASSEGNATI ad un UTENTE di un suo UFFICIO FIGLIO
        types = self.get_protocollo_types_by_group(cr, current_user_id, 'seedoo_protocollo', 'group_vedi_protocolli_', '_registrati_ass_ut_uff_fig')
        if types and employee_department_child_ids:
            cr.execute('''
                SELECT DISTINCT(pa.protocollo_id)
                FROM protocollo_assegnazione pa, protocollo_protocollo pp
                WHERE pp.type IN (''' + str(types).strip('[]') + ''') AND
                      pp.registration_date IS NOT NULL AND
                      pp.reserved = FALSE AND
                      pa.archivio_id IN (''' + archivio_ids_str + ''') AND 
                      pp.id = pa.protocollo_id AND
                      pa.tipologia_assegnatario = 'employee' AND
                      pa.parent_id IS NULL AND
                      pa.assegnatario_employee_department_id IN (''' + employee_department_child_ids_str + ''') AND
                      pa.state != 'rifiutato'
                      ''' + protocollo_ids_filter + '''
            ''')
            protocollo_ids_ass_ut_uff_fig = [res[0] for res in cr.fetchall()]
            protocollo_visible_ids.extend(protocollo_ids_ass_ut_uff_fig)
        _logger.debug("---Query ass_ut_uff_fig  %s seconds ---" % (time.time() - start_time))

        start_time = time.time()
        # un utente deve poter vedere i protocolli (IN, OUT, INTERNAL) REGISTRATI, ASSEGNATI e RIFIUTATI da un UTENTE del suo UFFICIO
        types = self.get_protocollo_types_by_group(cr, current_user_id, 'seedoo_protocollo', 'group_vedi_protocolli_', '_registrati_ass_rif_ut_uff')
        if types and employee_department_ids:
            cr.execute('''
                SELECT DISTINCT(pa.protocollo_id)
                FROM protocollo_assegnazione pa, protocollo_protocollo pp
                WHERE pp.type IN (''' + str(types).strip('[]') + ''') AND
                      pp.registration_date IS NOT NULL AND
                      pp.reserved = FALSE AND
                      pa.archivio_id IN (''' + archivio_ids_str + ''') AND 
                      pp.id = pa.protocollo_id AND
                      pa.tipologia_assegnatario = 'employee' AND
                      pa.assegnatario_employee_department_id IN (''' + employee_department_ids_str + ''') AND
                      pa.state = 'rifiutato'
                      ''' + protocollo_ids_filter + '''
            ''')
            protocollo_ids_ass_rif_ut_uff = [res[0] for res in cr.fetchall()]
            protocollo_visible_ids.extend(protocollo_ids_ass_rif_ut_uff)
        _logger.debug("---Query ass_rif_ut_uff  %s seconds ---" % (time.time() - start_time))

        return protocollo_visible_ids


    def _get_protocollo_visibile_ids(self, cr, uid, current_user_id, archivio_ids, protocollo_ids):
        protocollo_visible_ids = []

        employee_obj = self.pool.get('hr.employee')
        employee_ids = employee_obj.search(cr, uid, [('user_id', '=', current_user_id)])
        start_time = time.time()
        if len(employee_ids) > 0:

            employee_department_ids = []
            employee_department_child_ids = []
            aoo_ids = []
            for employee_id in employee_ids:
                employee = employee_obj.browse(cr, uid, employee_id)
                if employee.department_id:
                    employee_department = employee.department_id
                    employee_department_ids.append(employee_department.id)
                    for child in employee_department.all_child_ids:
                        employee_department_child_ids.append(child.id)
                    if employee_department.aoo_id:
                        aoo_ids.append(employee_department.aoo_id.id)

            employee_ids_str = ', '.join(map(str, employee_ids))
            employee_department_ids_str = ', '.join(map(str, employee_department_ids))
            employee_department_child_ids_str = ', '.join(map(str, employee_department_child_ids))
            archivio_ids_str = ', '.join(map(str, archivio_ids))
            protocollo_ids_str = ', '.join(map(str, protocollo_ids))
            protocollo_ids_filter = 'AND pp.id IN (%s)' % (protocollo_ids_str) if protocollo_ids else ''

            ############################################################################################################
            # Visibilità dei protocolli: casi base
            ############################################################################################################
            protocollo_base_visible_ids = self.get_protocollo_base_visibile_ids(
                cr, uid, current_user_id, archivio_ids, archivio_ids_str, employee_ids, employee_ids_str,
                employee_department_ids, employee_department_ids_str, protocollo_ids_filter)
            protocollo_visible_ids.extend(protocollo_base_visible_ids)
            ############################################################################################################

            ############################################################################################################
            # Visibilità dei protocolli: permessi in configurazione
            ############################################################################################################
            protocollo_configuration_visible_ids = self.get_protocollo_configuration_visibile_ids(
                cr, uid, current_user_id, archivio_ids, archivio_ids_str, employee_ids, employee_ids_str,
                employee_department_ids, employee_department_ids_str,
                employee_department_child_ids, employee_department_child_ids_str, aoo_ids, protocollo_ids_filter)
            protocollo_visible_ids.extend(protocollo_configuration_visible_ids)
            ############################################################################################################

            protocollo_visible_ids = list(set(protocollo_visible_ids))

        _logger.debug("--- %s start ---" % (start_time))
        _logger.debug("--- TEMPO ALGORTIMO: %s SECONDI ---" % (time.time() - start_time))
        _logger.debug("--- %s len ---" % (len(protocollo_visible_ids)))

        return protocollo_visible_ids


    def _get_protocollo_archivio_ids(self, cr, archivio_ids):
        protocollo_archivio_ids = []

        ############################################################################################################
        # Visibilità dei protocolli archiviati
        ############################################################################################################
        archivio_ids_str = ', '.join(map(str, archivio_ids))
        start_time = time.time()
        # un utente deve poter vedere i protocolli in bozza (IN e OUT) creati da lui
        cr.execute('''
             SELECT DISTINCT(pp.id)
             FROM protocollo_protocollo pp
             WHERE pp.archivio_id IN (''' + archivio_ids_str + ''')
         ''')
        protocollo_ids_archivio = [res[0] for res in cr.fetchall()]
        _logger.debug("---Query draft %s seconds ---" % (time.time() - start_time))

        # _logger.debug("--- %s seconds ---" % (time.time() - start_time_total))
        _logger.debug("--- %s start ---" % (start_time))
        _logger.debug("--- %s len ---" % (len(protocollo_ids_archivio)))

        return protocollo_ids_archivio

    def _is_visible(self, cr, uid, ids, name, arg, context=None):
        return {}

    def _is_visible_search(self, cr, uid, obj, name, args, domain=None, context=None):
        protocollo_visible_ids = []
        protocollo_archivio_obj = self.pool.get('protocollo.archivio')
        is_current = True
        if context and context.has_key('uid') and context['uid']:
            current_user_id = context['uid']
            if 'is_current_archive' in context:
                is_current = context['is_current_archive']
            archivio_ids = protocollo_archivio_obj._get_archivio_ids(cr, current_user_id, is_current)
            if len(archivio_ids) > 0:
                check_gruppo_archive = self.user_has_groups(cr, current_user_id, 'seedoo_protocollo.group_vedi_protocolli_archiviati')
                if is_current or not check_gruppo_archive:
                    protocollo_visible_ids = self._get_protocollo_visibile_ids(cr, SUPERUSER_ID, current_user_id, archivio_ids, [])
                else:
                    protocollo_visible_ids = self._get_protocollo_archivio_ids(cr, archivio_ids)

        return [('id', 'in', protocollo_visible_ids)]

    def filter_protocollo_ids(self, cr, uid, protocollo_ids, context):
        protocollo_visible_ids = []
        protocollo_archivio_obj = self.pool.get('protocollo.archivio')
        is_current = True
        if context and 'is_current_archive' in context:
            is_current = context['is_current_archive']
        archivio_ids = protocollo_archivio_obj._get_archivio_ids(cr, uid, is_current)
        if len(archivio_ids) > 0:
            check_gruppo_archive = self.user_has_groups(cr, uid, 'seedoo_protocollo.group_vedi_protocolli_archiviati')
            if is_current or not check_gruppo_archive:
                protocollo_visible_ids = self._get_protocollo_visibile_ids(cr, SUPERUSER_ID, uid, archivio_ids, protocollo_ids)
            else:
                protocollo_visible_ids = self._get_protocollo_archivio_ids(cr, archivio_ids)
        return protocollo_visible_ids

    # def check_access_rule(self, cr, uid, ids, operation, context=None):
    #     if context and context.has_key('skip_check') and context['skip_check']:
    #         return ids
    #     return super(protocollo_protocollo, self).check_access_rule(cr, uid, ids, operation, context=context)

    # def _apply_ir_rules(self, cr, uid, query, mode='read', context=None):
    #     if context and context.has_key('skip_check') and context['skip_check']:
    #         return
    #     return super(protocollo_protocollo, self)._apply_ir_rules(cr, uid, query, mode='read', context=context)

    def get_search_protocollo_ids(self, cr, uid, domain):
        search_protocollo_ids = []
        if not domain:
            domain = []
        for domain_condition in domain:
            if len(domain_condition)==3 and domain_condition[0]=='id':
                if domain_condition[1] == '=':
                    search_protocollo_ids = [domain_condition[2]]
                elif domain_condition[1] == 'in':
                    search_protocollo_ids = domain_condition[2]
        return search_protocollo_ids

    def search_read(self, cr, uid, domain=None, fields=None, offset=0, limit=None, order=None, context=None):
        search_ctx = dict(context or {})
        search_ctx['skip_check_read'] = True
        return super(protocollo_protocollo, self).search_read(cr, uid, domain, fields, offset, limit, order, search_ctx)

    def _search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False, access_rights_uid=None):
        if uid == SUPERUSER_ID or (context and context.has_key('skip_check') and context['skip_check']):
            return super(protocollo_protocollo, self)._search(cr, uid, args, offset, limit, order, context, count, access_rights_uid)

        if context and context.has_key('filtered_protocollo_ids'):
            filtered_protocollo_ids = context['filtered_protocollo_ids']
        else:
            search_protocollo_ids = self.get_search_protocollo_ids(cr, uid, args)
            filtered_protocollo_ids = self.filter_protocollo_ids(cr, uid, search_protocollo_ids, context)

        args = [('id', 'in', filtered_protocollo_ids)] + args
        return super(protocollo_protocollo, self)._search(cr, uid, args, offset, limit, order, context, count, access_rights_uid)

    def read(self, cr, uid, ids, fields=None, context=None, load='_classic_read'):
        if not context or not context.has_key('skip_check_read') or not context['skip_check_read']:
            self.check_access(cr, uid, ids, 'read', context)
        return super(protocollo_protocollo, self).read(cr, uid, ids, fields, context, load)

    def _write(self, cr, uid, ids, vals, context=None):
        self.check_access(cr, uid, ids, 'write', context)
        return super(protocollo_protocollo, self)._write(cr, uid, ids, vals, context)

    def unlink(self, cr, uid, ids, context=None):
        self.check_access(cr, uid, ids, 'unlink', context)
        return super(protocollo_protocollo, self).unlink(cr, uid, ids, context)

    def check_access(self, cr, uid, ids, operation, context):
        if uid == SUPERUSER_ID or (context and context.has_key('skip_check') and context['skip_check']):
            return None
        protocollo_ids = self.filter_protocollo_ids(cr, uid, ids, context)
        for id in ids:
            if id not in protocollo_ids:
                raise AccessError(_(
                    "The requested operation cannot be completed due to group security restrictions. "
                    "Please contact your system administrator.\n\n(Document type: %s, Operation: %s)"
                ) % (self._description, operation))

    ####################################################################################################################

    ####################################################################################################################
    # Visibilità dei protocolli nella dashboard
    ####################################################################################################################

    ####################################################################################################################

    def _non_classificati_query(self, cr, uid, type='search'):
        archivio_ids = self.pool.get('protocollo.archivio').search(cr, uid, [('is_current', '=', True)], limit=1)
        archivio_id = archivio_ids[0]
        query = 'SELECT DISTINCT(pp.id) '
        if type == 'count':
            query = 'SELECT COUNT(DISTINCT(pp.id)) '
        query += '''
            FROM protocollo_protocollo pp, hr_employee he, resource_resource rr
            WHERE pp.classification IS NULL AND 
                  pp.registration_employee_state = 'working' AND 
                  pp.registration_employee_id = he.id AND 
                  he.resource_id = rr.id AND 
                  rr.user_id = %s AND 
                  rr.active = TRUE AND 
                  pp.state IN ('registered', 'notified', 'waiting', 'sent', 'error') AND 
                  pp.is_imported = FALSE AND 
                  pp.archivio_id = %s 
        ''' % (uid, archivio_id)
        cr.execute(query)
        result = cr.fetchall()
        return result

    def _non_classificati_visibility(self, cr, uid, ids, name, arg, context=None):
        return {}

    def _non_classificati_visibility_search(self, cr, uid, obj, name, args, domain=None, context=None):
        time_start = time.time()
        results = self._non_classificati_query(cr, uid, 'search')
        protocollo_visible_ids = [res[0] for res in results]
        time_end = time.time()
        time_duration = time_end - time_start
        _logger.debug("_non_classificati_visibility_search: %s sec" % (time_duration,))
        return [('id', 'in', protocollo_visible_ids)]

    def _non_classificati_visibility_count(self, cr, uid):
        time_start = time.time()
        result = self._non_classificati_query(cr, uid, 'count')
        count_value = result[0][0]
        time_end = time.time()
        time_duration = time_end - time_start
        _logger.debug("_non_classificati_visibility_count: %s - %s sec" % (count_value, time_duration))
        return count_value

    ####################################################################################################################

    ####################################################################################################################

    def _non_fascicolati_query(self, cr, uid, type='search'):
        archivio_ids = self.pool.get('protocollo.archivio').search(cr, uid, [('is_current', '=', True)], limit=1)
        archivio_id = archivio_ids[0]
        dossier_condition = ''
        fascicolo_ids = self.pool.get('protocollo.dossier').search(cr, uid, [])
        if fascicolo_ids:
            dossier_condition = 'AND pp.id NOT IN (SELECT protocollo_id FROM dossier_protocollo_rel WHERE dossier_id IN (' + ', '.join(map(str, fascicolo_ids)) + '))'
        query = 'SELECT DISTINCT(p.id) '
        if type == 'count':
            query = 'SELECT COUNT(DISTINCT(p.id)) '
        query += '''
            FROM (
                SELECT DISTINCT(pa.protocollo_id) AS id
                FROM protocollo_protocollo pp, protocollo_assegnazione pa, hr_employee he, resource_resource rr
                WHERE pp.id = pa.protocollo_id AND 
                      pp.registration_date IS NOT NULL AND 
                      pp.state IN ('registered', 'notified', 'waiting', 'sent', 'error') AND
                      (
                            (pa.tipologia_assegnatario = 'employee' AND pa.parent_id IS NULL AND pa.assegnatario_employee_id = he.id AND he.resource_id = rr.id AND rr.user_id = %s AND rr.active = TRUE AND pa.state IN ('preso', 'letto')) OR 
                            (pa.tipologia_assegnatario = 'department' AND pa.assegnatario_department_id = he.department_id AND he.resource_id = rr.id AND rr.user_id = %s AND rr.active = TRUE AND pa.id IN (
                                SELECT pa2.parent_id
                                FROM protocollo_assegnazione pa2
                                WHERE pp.id = pa2.protocollo_id AND 
                                      pa2.tipologia_assegnatario = 'employee' AND
                                      pa2.parent_id IS NOT NULL AND
                                      pa2.assegnatario_employee_id = he.id AND 
                                      pa2.state IN ('preso', 'letto')
                            ))
                      ) AND
                      pa.archivio_id = %s 
                      %s
                    
                UNION
                
                SELECT DISTINCT(pp.id) AS id
                FROM protocollo_protocollo pp, hr_employee he, resource_resource rr
                WHERE pp.registration_employee_state = 'working' AND 
                      pp.registration_employee_id = he.id AND 
                      he.resource_id = rr.id AND 
                      rr.user_id = %s AND 
                      rr.active = TRUE AND 
                      pp.state IN ('registered', 'notified', 'waiting', 'sent', 'error') AND
                      pp.archivio_id = %s 
                      %s
                          
            ) p
        ''' % (uid, uid, archivio_id, dossier_condition, uid, archivio_id, dossier_condition)
        cr.execute(query)
        result = cr.fetchall()
        return result

    def _non_fascicolati_visibility(self, cr, uid, ids, name, arg, context=None):
        return {}

    def _non_fascicolati_visibility_search(self, cr, uid, obj, name, args, domain=None, context=None):
        time_start = time.time()
        results = self._non_fascicolati_query(cr, uid, 'search')
        protocollo_visible_ids = [res[0] for res in results]
        time_end = time.time()
        time_duration = time_end - time_start
        _logger.debug("_non_fascicolati_visibility_search: %s sec" % (time_duration,))
        return [('id', 'in', protocollo_visible_ids)]

    def _non_fascicolati_visibility_count(self, cr, uid):
        time_start = time.time()
        result = self._non_fascicolati_query(cr, uid, 'count')
        count_value = result[0][0]
        time_end = time.time()
        time_duration = time_end - time_start
        _logger.debug("_non_fascicolati_visibility_count: %s - %s sec" % (count_value, time_duration))
        return count_value

    ####################################################################################################################

    ####################################################################################################################

    def _bozza_creato_da_me_query(self, cr, uid, type='search'):
        archivio_ids = self.pool.get('protocollo.archivio').search(cr, uid, [('is_current', '=', True)], limit=1)
        archivio_id = archivio_ids[0]
        query = 'SELECT DISTINCT(pp.id) '
        if type == 'count':
            query = 'SELECT COUNT(DISTINCT(pp.id)) '
        query += '''
            FROM protocollo_protocollo pp
            WHERE pp.state = 'draft' AND 
                  pp.user_id = %s AND 
                  pp.archivio_id = %s 
        ''' % (uid, archivio_id)
        cr.execute(query)
        result = cr.fetchall()
        return result

    def _bozza_creato_da_me_visibility(self, cr, uid, ids, name, arg, context=None):
        return {}

    def _bozza_creato_da_me_visibility_search(self, cr, uid, obj, name, args, domain=None, context=None):
        time_start = time.time()
        results = self._bozza_creato_da_me_query(cr, uid, 'search')
        protocollo_visible_ids = [res[0] for res in results]
        time_end = time.time()
        time_duration = time_end - time_start
        _logger.debug("_bozza_creato_da_me_visibility_search: %s sec" % (time_duration,))
        return [('id', 'in', protocollo_visible_ids)]

    @api.cr_uid
    def _bozza_creato_da_me_visibility_count(self, cr, uid):
        time_start = time.time()
        result = self._bozza_creato_da_me_query(cr, uid, 'count')
        count_value = result[0][0]
        time_end = time.time()
        time_duration = time_end - time_start
        _logger.debug("_bozza_creato_da_me_visibility_count: %s - %s sec" % (count_value, time_duration))
        return count_value

    ####################################################################################################################

    ####################################################################################################################

    def _assegnato_a_me_query(self, cr, uid, type='search'):
        archivio_ids = self.pool.get('protocollo.archivio').search(cr, uid, [('is_current', '=', True)], limit=1)
        archivio_id = archivio_ids[0]
        query = 'SELECT DISTINCT(pa.protocollo_id) '
        if type == 'count':
            query = 'SELECT COUNT(DISTINCT(pa.protocollo_id)) '
        query += '''
            FROM protocollo_protocollo pp, protocollo_assegnazione pa, hr_employee he, resource_resource rr
            WHERE pp.id = pa.protocollo_id AND 
                  pa.assegnatario_employee_id = he.id AND
                  he.resource_id = rr.id AND
                  rr.user_id = %s AND
                  rr.active = TRUE AND
                  pp.registration_date IS NOT NULL AND
                  pa.tipologia_assegnatario = 'employee' AND 
                  pa.state = 'assegnato' AND
                  pa.parent_id IS NULL AND
                  pp.state IN ('registered', 'notified', 'waiting', 'sent', 'error') AND 
                  pa.archivio_id = %s 
        ''' % (uid, archivio_id)
        cr.execute(query)
        result = cr.fetchall()
        return result

    def _assegnato_a_me_visibility(self, cr, uid, ids, name, arg, context=None):
        return {}

    def _assegnato_a_me_visibility_search(self, cr, uid, obj, name, args, domain=None, context=None):
        time_start = time.time()
        results = self._assegnato_a_me_query(cr, uid, 'search')
        protocollo_visible_ids = [res[0] for res in results]
        time_end = time.time()
        time_duration = time_end - time_start
        _logger.debug("_assegnato_a_me_visibility_search: %s sec" % (time_duration, ))
        return [('id', 'in', protocollo_visible_ids)]

    @api.cr_uid
    def _assegnato_a_me_visibility_count(self, cr, uid):
        time_start = time.time()
        result = self._assegnato_a_me_query(cr, uid, 'count')
        count_value = result[0][0]
        time_end = time.time()
        time_duration = time_end - time_start
        _logger.debug("_assegnato_a_me_visibility_count: %s - %s sec" % (count_value, time_duration))
        return count_value

    ####################################################################################################################

    ####################################################################################################################

    def _assegnato_a_me_comp_query(self, cr, uid, type='search'):
        archivio_ids = self.pool.get('protocollo.archivio').search(cr, uid, [('is_current', '=', True)], limit=1)
        archivio_id = archivio_ids[0]
        query = 'SELECT DISTINCT(pa.protocollo_id) '
        if type == 'count':
            query = 'SELECT COUNT(DISTINCT(pa.protocollo_id)) '
        query += '''
            FROM protocollo_protocollo pp, protocollo_assegnazione pa, hr_employee he, resource_resource rr
            WHERE pp.id = pa.protocollo_id AND 
                  pa.assegnatario_employee_id = he.id AND
                  he.resource_id = rr.id AND
                  rr.user_id = %s AND
                  rr.active = TRUE AND
                  pp.registration_date IS NOT NULL AND
                  pa.tipologia_assegnatario = 'employee' AND 
                  pa.tipologia_assegnazione = 'competenza' AND
                  pa.state = 'assegnato' AND
                  pa.parent_id IS NULL AND
                  pp.state IN ('registered', 'notified', 'waiting', 'sent', 'error') AND 
                  pa.archivio_id = %s 
        ''' % (uid, archivio_id)
        cr.execute(query)
        result = cr.fetchall()
        return result

    def _assegnato_a_me_comp_visibility(self, cr, uid, ids, name, arg, context=None):
        return {}

    def _assegnato_a_me_comp_visibility_search(self, cr, uid, obj, name, args, domain=None, context=None):
        time_start = time.time()
        results = self._assegnato_a_me_comp_query(cr, uid, 'search')
        protocollo_visible_ids = [res[0] for res in results]
        time_end = time.time()
        time_duration = time_end - time_start
        _logger.debug("_assegnato_a_me_comp_visibility_search: %s sec" % (time_duration, ))
        return [('id', 'in', protocollo_visible_ids)]

    @api.cr_uid
    def _assegnato_a_me_comp_visibility_count(self, cr, uid):
        time_start = time.time()
        result = self._assegnato_a_me_comp_query(cr, uid, 'count')
        count_value = result[0][0]
        time_end = time.time()
        time_duration = time_end - time_start
        _logger.debug("_assegnato_a_me_comp_visibility_count: %s - %s sec" % (count_value, time_duration))
        return count_value

    ####################################################################################################################

    ####################################################################################################################

    def _assegnato_a_me_cc_query(self, cr, uid, type='search'):
        archivio_ids = self.pool.get('protocollo.archivio').search(cr, uid, [('is_current', '=', True)], limit=1)
        archivio_id = archivio_ids[0]
        query = 'SELECT DISTINCT(pa.protocollo_id) '
        if type == 'count':
            query = 'SELECT COUNT(DISTINCT(pa.protocollo_id)) '
        query += '''
            FROM protocollo_protocollo pp, protocollo_assegnazione pa, hr_employee he, resource_resource rr
            WHERE pp.id = pa.protocollo_id AND 
                  pa.assegnatario_employee_id = he.id AND
                  he.resource_id = rr.id AND
                  rr.user_id = %s AND
                  rr.active = TRUE AND
                  pp.registration_date IS NOT NULL AND
                  pa.tipologia_assegnatario = 'employee' AND 
                  pa.tipologia_assegnazione = 'conoscenza' AND
                  pa.state = 'assegnato' AND
                  pa.parent_id IS NULL AND
                  pp.state IN ('registered', 'notified', 'waiting', 'sent', 'error') AND
                  pa.archivio_id = %s
        ''' % (uid, archivio_id)
        cr.execute(query)
        result = cr.fetchall()
        return result

    def _assegnato_a_me_cc_visibility(self, cr, uid, ids, name, arg, context=None):
        return {}

    def _assegnato_a_me_cc_visibility_search(self, cr, uid, obj, name, args, domain=None, context=None):
        time_start = time.time()
        results = self._assegnato_a_me_cc_query(cr, uid, 'search')
        protocollo_visible_ids = [res[0] for res in results]
        time_end = time.time()
        time_duration = time_end - time_start
        _logger.debug("_assegnato_a_me_cc_visibility_search: %s sec" % (time_duration,))
        return [('id', 'in', protocollo_visible_ids)]

    def _assegnato_a_me_cc_visibility_count(self, cr, uid):
        time_start = time.time()
        result = self._assegnato_a_me_cc_query(cr, uid, 'count')
        count_value = result[0][0]
        time_end = time.time()
        time_duration = time_end - time_start
        _logger.debug("_assegnato_a_me_cc_visibility_count: %s - %s sec" % (count_value, time_duration))
        return count_value

    ####################################################################################################################

    ####################################################################################################################

    def _assegnato_a_mio_ufficio_query(self, cr, uid, type='search'):
        archivio_ids = self.pool.get('protocollo.archivio').search(cr, uid, [('is_current', '=', True)], limit=1)
        archivio_id = archivio_ids[0]
        query = 'SELECT DISTINCT(pp.id) '
        if type == 'count':
            query = 'SELECT COUNT(DISTINCT(pp.id)) '
        query += '''
			FROM protocollo_protocollo pp, protocollo_assegnazione pa, hr_department hd, hr_employee he, resource_resource rr
            WHERE pp.id = pa.protocollo_id AND
                  pa.assegnatario_department_id = hd.id AND
                  hd.id = he.department_id AND
                  he.resource_id = rr.id AND
                  rr.user_id = %s AND
                  rr.active = TRUE AND
                  pp.registration_date IS NOT NULL AND
                  pa.tipologia_assegnatario = 'department' AND
                  pa.state = 'assegnato' AND
                  pp.state IN ('registered', 'notified', 'waiting', 'sent', 'error') AND
                  pa.archivio_id = %s AND
                  pa.id NOT IN (
                      SELECT pa.parent_id
                      FROM protocollo_protocollo pp, protocollo_assegnazione pa, hr_department hd, hr_employee he, resource_resource rr
                      WHERE pp.id = pa.protocollo_id AND
                            pa.assegnatario_employee_id = he.id AND
                            he.resource_id = rr.id AND
                            rr.user_id = %s AND
                            rr.active = TRUE AND
                            pp.registration_date IS NOT NULL AND
                            pa.tipologia_assegnatario = 'employee' AND
                            pa.parent_id IS NOT NULL AND
                            pa.state != 'assegnato' AND
                            pp.state IN ('registered', 'notified', 'waiting', 'sent', 'error') AND
                            pa.archivio_id = %s
                  )
        ''' % (uid, archivio_id, uid, archivio_id)
        cr.execute(query)
        result = cr.fetchall()
        return result

    def _assegnato_a_mio_ufficio_visibility(self, cr, uid, ids, name, arg, context=None):
        return {}

    def _assegnato_a_mio_ufficio_visibility_search(self, cr, uid, obj, name, args, domain=None, context=None):
        time_start = time.time()
        results = self._assegnato_a_mio_ufficio_query(cr, uid, 'search')
        protocollo_visible_ids = [res[0] for res in results]
        time_end = time.time()
        time_duration = time_end - time_start
        _logger.debug("_assegnato_a_mio_ufficio_visibility_search: %s sec" % (time_duration,))
        return [('id', 'in', protocollo_visible_ids)]

    @api.cr_uid
    def _assegnato_a_mio_ufficio_visibility_count(self, cr, uid):
        time_start = time.time()
        result = self._assegnato_a_mio_ufficio_query(cr, uid, 'count')
        count_value = result[0][0]
        time_end = time.time()
        time_duration = time_end - time_start
        _logger.debug("_assegnato_a_mio_ufficio_visibility_count: %s - %s sec" % (count_value, time_duration))
        return count_value

    ####################################################################################################################

    ####################################################################################################################

    def _assegnato_a_mio_ufficio_comp_query(self, cr, uid, type='search'):
        archivio_ids = self.pool.get('protocollo.archivio').search(cr, uid, [('is_current', '=', True)], limit=1)
        archivio_id = archivio_ids[0]
        query = 'SELECT DISTINCT(pa.protocollo_id) '
        if type == 'count':
            query = 'SELECT COUNT(DISTINCT(pa.protocollo_id)) '
        query += '''
            FROM protocollo_protocollo pp, protocollo_assegnazione pa, hr_department hd, hr_employee he, resource_resource rr
            WHERE pp.id = pa.protocollo_id AND 
                  pa.assegnatario_department_id = hd.id AND
                  hd.id=he.department_id AND
                  he.resource_id = rr.id AND
                  rr.user_id = %s AND
                  rr.active = TRUE AND
                  pp.registration_date IS NOT NULL AND
                  pa.tipologia_assegnatario = 'department' AND 
                  pa.tipologia_assegnazione = 'competenza' AND
                  pa.state = 'assegnato' AND
                  pp.state IN ('registered', 'notified', 'waiting', 'sent', 'error') AND
                  pa.archivio_id = %s
        ''' % (uid, archivio_id)
        cr.execute(query)
        result = cr.fetchall()
        return result

    def _assegnato_a_mio_ufficio_comp_visibility(self, cr, uid, ids, name, arg, context=None):
        return {}

    def _assegnato_a_mio_ufficio_comp_visibility_search(self, cr, uid, obj, name, args, domain=None, context=None):
        time_start = time.time()
        results = self._assegnato_a_mio_ufficio_comp_query(cr, uid, 'search')
        protocollo_visible_ids = [res[0] for res in results]
        time_end = time.time()
        time_duration = time_end - time_start
        _logger.debug("_assegnato_a_mio_ufficio_comp_visibility_search: %s sec" % (time_duration,))
        return [('id', 'in', protocollo_visible_ids)]

    @api.cr_uid
    def _assegnato_a_mio_ufficio_comp_visibility_count(self, cr, uid):
        time_start = time.time()
        result = self._assegnato_a_mio_ufficio_comp_query(cr, uid, 'count')
        count_value = result[0][0]
        time_end = time.time()
        time_duration = time_end - time_start
        _logger.debug("_assegnato_a_mio_ufficio_comp_visibility_count: %s - %s sec" % (count_value, time_duration))
        return count_value

    ####################################################################################################################

    ####################################################################################################################

    def _assegnato_a_mio_ufficio_cc_query(self, cr, uid, type='search'):
        archivio_ids = self.pool.get('protocollo.archivio').search(cr, uid, [('is_current', '=', True)], limit=1)
        archivio_id = archivio_ids[0]
        query = 'SELECT DISTINCT(pa.protocollo_id) '
        if type == 'count':
            query = 'SELECT COUNT(DISTINCT(pa.protocollo_id)) '
        query += '''
            FROM protocollo_protocollo pp, protocollo_assegnazione pa, hr_department hd, hr_employee he, resource_resource rr
            WHERE pp.id = pa.protocollo_id AND 
                  pa.assegnatario_department_id = hd.id AND
                  hd.id=he.department_id AND
                  he.resource_id = rr.id AND
                  rr.user_id = %s AND
                  rr.active = TRUE AND
                  pp.registration_date IS NOT NULL AND
                  pa.tipologia_assegnatario = 'department' AND 
                  pa.tipologia_assegnazione = 'conoscenza' AND
                  pa.state = 'assegnato' AND
                  pp.state IN ('registered', 'notified', 'waiting', 'sent', 'error') AND
                  pa.archivio_id = %s
        ''' % (uid, archivio_id)
        cr.execute(query)
        result = cr.fetchall()
        return result

    def _assegnato_a_mio_ufficio_cc_visibility(self, cr, uid, ids, name, arg, context=None):
        return {}

    def _assegnato_a_mio_ufficio_cc_visibility_search(self, cr, uid, obj, name, args, domain=None, context=None):
        time_start = time.time()
        results = self._assegnato_a_mio_ufficio_cc_query(cr, uid, 'search')
        protocollo_visible_ids = [res[0] for res in results]
        time_end = time.time()
        time_duration = time_end - time_start
        _logger.debug("_assegnato_a_mio_ufficio_cc_visibility_search: %s sec" % (time_duration,))
        return [('id', 'in', protocollo_visible_ids)]

    @api.cr_uid
    def _assegnato_a_mio_ufficio_cc_visibility_count(self, cr, uid):
        time_start = time.time()
        result = self._assegnato_a_mio_ufficio_cc_query(cr, uid, 'count')
        count_value = result[0][0]
        time_end = time.time()
        time_duration = time_end - time_start
        _logger.debug("_assegnato_a_mio_ufficio_cc_visibility_count: %s - %s sec" % (count_value, time_duration))
        return count_value

    ####################################################################################################################

    ####################################################################################################################

    def _assegnato_cc_query(self, cr, uid, type='search'):
        archivio_ids = self.pool.get('protocollo.archivio').search(cr, uid, [('is_current', '=', True)], limit=1)
        archivio_id = archivio_ids[0]
        query = 'SELECT DISTINCT(pa.protocollo_id) '
        if type == 'count':
            query = 'SELECT COUNT(DISTINCT(pa.protocollo_id)) '
        query += '''
            FROM protocollo_protocollo pp, protocollo_assegnazione pa, hr_employee he, resource_resource rr
            WHERE pp.id = pa.protocollo_id AND
                  (
                       (pa.tipologia_assegnatario = 'employee' AND pa.parent_id IS NULL AND pa.assegnatario_employee_id = he.id AND he.resource_id = rr.id AND rr.user_id = %s AND rr.active = TRUE) OR
                       (pa.tipologia_assegnatario = 'department' AND pa.assegnatario_department_id = he.department_id AND he.resource_id = rr.id AND rr.user_id = %s AND rr.active = TRUE AND pa.id NOT IN (
                            SELECT pa2.parent_id 
                            FROM protocollo_assegnazione pa2
                            WHERE pp.id = pa2.protocollo_id AND 
                                  pa2.tipologia_assegnatario = 'employee' AND
                                  pa2.tipologia_assegnazione = 'conoscenza' AND
                                  pa2.state != 'assegnato' AND  
                                  pa2.parent_id IS NOT NULL AND 
                                  pa2.assegnatario_employee_id = he.id
                       ))
                  ) AND
                  pp.registration_date IS NOT NULL AND
                  pa.tipologia_assegnazione = 'conoscenza' AND
                  pa.state = 'assegnato' AND
                  pp.state IN ('registered', 'notified', 'waiting', 'sent', 'error') AND
                  pa.archivio_id = %s
        ''' % (uid, uid, archivio_id)
        cr.execute(query)
        result = cr.fetchall()
        return result

    def _assegnato_cc_visibility(self, cr, uid, ids, name, arg, context=None):
        return {}

    def _assegnato_cc_visibility_search(self, cr, uid, obj, name, args, domain=None, context=None):
        time_start = time.time()
        results = self._assegnato_cc_query(cr, uid, 'search')
        protocollo_visible_ids = [res[0] for res in results]
        time_end = time.time()
        time_duration = time_end - time_start
        _logger.debug("_assegnato_cc_visibility_search: %s sec" % (time_duration,))
        return [('id', 'in', protocollo_visible_ids)]

    @api.cr_uid
    def _assegnato_cc_visibility_count(self, cr, uid):
        time_start = time.time()
        result = self._assegnato_cc_query(cr, uid, 'count')
        count_value = result[0][0]
        time_end = time.time()
        time_duration = time_end - time_start
        _logger.debug("_assegnato_cc_visibility_count: %s - %s sec" % (count_value, time_duration))
        return count_value

    ####################################################################################################################

    ####################################################################################################################

    def _da_assegnare_query(self, cr, uid, type='search'):
        archivio_ids = self.pool.get('protocollo.archivio').search(cr, uid, [('is_current', '=', True)], limit=1)
        archivio_id = archivio_ids[0]
        query = 'SELECT DISTINCT(pp.id) '
        if type == 'count':
            query = 'SELECT COUNT(DISTINCT(pp.id)) '
        query += '''
            FROM protocollo_protocollo pp, hr_employee he, resource_resource rr
            WHERE pp.registration_employee_id = he.id AND
                  he.resource_id = rr.id AND
                  rr.user_id = %s AND
                  rr.active = TRUE AND
                  pp.registration_employee_state = 'working' AND
                  pp.registration_date IS NOT NULL AND
                  pp.state IN ('registered', 'notified', 'waiting', 'sent', 'error') AND
                  pp.da_assegnare = TRUE AND
                  pp.is_imported = FALSE AND
                  pa.archivio_id = %s
        ''' % (uid, archivio_id)
        cr.execute(query)
        result = cr.fetchall()
        return result

    def _da_assegnare_visibility(self, cr, uid, ids, name, arg, context=None):
        return {}

    def _da_assegnare_visibility_search(self, cr, uid, obj, name, args, domain=None, context=None):
        time_start = time.time()
        results = self._da_assegnare_query(cr, uid, 'search')
        protocollo_visible_ids = [res[0] for res in results]
        time_end = time.time()
        time_duration = time_end - time_start
        _logger.debug("_da_assegnare_visibility_search: %s sec" % (time_duration,))
        return [('id', 'in', protocollo_visible_ids)]

    @api.cr_uid
    def _da_assegnare_visibility_count(self, cr, uid):
        time_start = time.time()
        result = self._da_assegnare_query(cr, uid, 'count')
        count_value = result[0][0]
        time_end = time.time()
        time_duration = time_end - time_start
        _logger.debug("_da_assegnare_visibility_count: %s - %s sec" % (count_value, time_duration))
        return count_value

    ####################################################################################################################

    ####################################################################################################################

    def _assegnato_da_me_in_attesa_query(self, cr, uid, type, archivio_id=None):
        if not archivio_id:
            archivio_ids = self.pool.get('protocollo.archivio').search(cr, uid, [('is_current', '=', True)], limit=1)
            archivio_id = archivio_ids[0]
        query = 'SELECT DISTINCT(p.id) '
        if type == 'count':
            query = 'SELECT COUNT(DISTINCT(p.id)) '
        query += '''
            FROM (
                SELECT DISTINCT(pp.id) 
                FROM protocollo_protocollo pp, protocollo_assegnazione pa, hr_employee he, resource_resource rr
                WHERE pp.id = pa.protocollo_id AND 
                      pa.assegnatore_id = he.id AND 
                      he.resource_id = rr.id AND 
                      rr.user_id = %s AND
                      rr.active = TRUE AND
                      pp.registration_date IS NOT NULL AND
                      pp.registration_employee_state = 'working' AND
                      pa.tipologia_assegnazione = 'competenza' AND
                      pa.state = 'assegnato' AND
                      pa.parent_id IS NULL AND
                      pp.state IN ('registered', 'notified', 'waiting', 'sent', 'error') AND
                      pa.archivio_id = %s
                
                UNION
                
                SELECT DISTINCT(pp.id) 
                FROM protocollo_protocollo pp, protocollo_assegnazione pa1, protocollo_assegnazione pa2, hr_employee he, resource_resource rr
                WHERE pp.registration_date IS NOT NULL AND
                      pp.state IN ('registered', 'notified', 'waiting', 'sent', 'error') AND
                      pp.id = pa1.protocollo_id AND
                      pa1.assegnatario_employee_id = he.id AND
                      pa1.tipologia_assegnazione = 'competenza' AND
                      pa1.state = 'preso' AND
                      pp.id = pa2.protocollo_id AND
                      pa2.assegnatore_id = he.id AND
                      pa2.tipologia_assegnazione = 'competenza' AND
                      pa2.state = 'assegnato' AND
                      pa2.parent_id IS NULL AND
                      he.resource_id = rr.id AND
                      rr.user_id = %s AND
                      rr.active = TRUE AND
                      pa1.archivio_id = %s AND
                      pa2.archivio_id = %s
            ) p
        ''' % (uid, archivio_id, uid, archivio_id, archivio_id)
        cr.execute(query)
        result = cr.fetchall()
        return result

    def _assegnato_da_me_in_attesa_visibility(self, cr, uid, ids, name, arg, context=None):
        return {}

    def _assegnato_da_me_in_attesa_visibility_search(self, cr, uid, obj, name, args, domain=None, context=None):
        time_start = time.time()
        results = self._assegnato_da_me_in_attesa_query(cr, uid, 'search')
        protocollo_visible_ids = [res[0] for res in results]
        time_end = time.time()
        time_duration = time_end - time_start
        _logger.debug("_assegnato_da_me_in_attesa_visibility_search: %s sec" % (time_duration,))
        return [('id', 'in', protocollo_visible_ids)]

    @api.cr_uid
    def _assegnato_da_me_in_attesa_visibility_count(self, cr, uid):
        time_start = time.time()
        result = self._assegnato_da_me_in_attesa_query(cr, uid, 'count')
        count_value = result[0][0]
        time_end = time.time()
        time_duration = time_end - time_start
        _logger.debug("_assegnato_da_me_in_attesa_visibility_count: %s - %s sec" % (count_value, time_duration))
        return count_value

    ####################################################################################################################

    ####################################################################################################################

    def _assegnato_da_me_in_rifiutato_query(self, cr, uid, type, archivio_id=None):
        if not archivio_id:
            archivio_ids = self.pool.get('protocollo.archivio').search(cr, uid, [('is_current', '=', True)], limit=1)
            archivio_id = archivio_ids[0]
        query = 'SELECT DISTINCT(p.id) '
        if type == 'count':
            query = 'SELECT COUNT(DISTINCT(p.id)) '
        query += '''
            FROM (
                SELECT DISTINCT(pp.id) 
                FROM protocollo_protocollo pp, protocollo_assegnazione pa, hr_employee he, resource_resource rr
                WHERE pp.id = pa.protocollo_id AND 
                      pa.assegnatore_id = he.id AND 
                      he.resource_id = rr.id AND 
                      rr.user_id = %s AND
                      rr.active = TRUE AND
                      pp.registration_date IS NOT NULL AND
                      pp.registration_employee_state = 'working' AND
                      pa.tipologia_assegnazione = 'competenza' AND
                      pa.state = 'rifiutato' AND
                      pa.parent_id IS NULL AND
                      pp.state IN ('registered', 'notified', 'waiting', 'sent', 'error') AND
                      pa.archivio_id = %s

                UNION

                SELECT DISTINCT(pp.id) 
                FROM protocollo_protocollo pp, protocollo_assegnazione pa1, protocollo_assegnazione pa2, hr_employee he, resource_resource rr
                WHERE pp.registration_date IS NOT NULL AND
                      pp.state IN ('registered', 'notified', 'waiting', 'sent', 'error') AND
                      pp.id = pa1.protocollo_id AND
                      pa1.assegnatario_employee_id = he.id AND
                      pa1.tipologia_assegnazione = 'competenza' AND
                      pa1.state = 'preso' AND
                      pp.id = pa2.protocollo_id AND
                      pa2.assegnatore_id = he.id AND
                      pa2.tipologia_assegnazione = 'competenza' AND
                      pa2.state = 'rifiutato' AND
                      pa2.parent_id IS NULL AND
                      he.resource_id = rr.id AND
                      rr.user_id = %s AND
                      rr.active = TRUE AND
                      pa1.archivio_id = %s AND
                      pa2.archivio_id = %s
            ) p
        ''' % (uid, archivio_id, uid, archivio_id, archivio_id)
        cr.execute(query)
        result = cr.fetchall()
        return result

    def _assegnato_da_me_in_rifiutato_visibility(self, cr, uid, ids, name, arg, context=None):
        return {}

    def _assegnato_da_me_in_rifiutato_visibility_search(self, cr, uid, obj, name, args, domain=None, context=None):
        time_start = time.time()
        results = self._assegnato_da_me_in_rifiutato_query(cr, uid, 'search')
        protocollo_visible_ids = [res[0] for res in results]
        time_end = time.time()
        time_duration = time_end - time_start
        _logger.debug("_assegnato_da_me_in_rifiutato_visibility_search: %s sec" % (time_duration,))
        return [('id', 'in', protocollo_visible_ids)]

    @api.cr_uid
    def _assegnato_da_me_in_rifiutato_visibility_count(self, cr, uid):
        time_start = time.time()
        result = self._assegnato_da_me_in_rifiutato_query(cr, uid, 'count')
        count_value = result[0][0]
        time_end = time.time()
        time_duration = time_end - time_start
        _logger.debug("_assegnato_da_me_in_rifiutato_visibility_count: %s - %s sec" % (count_value, time_duration))
        return count_value

    ####################################################################################################################

    ####################################################################################################################

    def _da_inviare_query(self, cr, uid, type='search'):
        archivio_ids = self.pool.get('protocollo.archivio').search(cr, uid, [('is_current', '=', True)], limit=1)
        archivio_id = archivio_ids[0]
        query = 'SELECT DISTINCT(pp.id) '
        if type == 'count':
            query = 'SELECT COUNT(DISTINCT(pp.id)) '
        query += '''
            FROM protocollo_protocollo pp, hr_employee he, resource_resource rr
            WHERE pp.registration_employee_state = 'working' AND 
                  pp.registration_employee_id = he.id AND
                  he.resource_id = rr.id AND
                  rr.user_id = %s AND
                  rr.active = TRUE AND
                  pp.registration_date IS NOT NULL AND
                  pp.type = 'out' AND 
                  pp.state IN ('registered', 'error') AND
                  pp.archivio_id = %s
        ''' % (uid, archivio_id)
        cr.execute(query)
        result = cr.fetchall()
        return result

    def _da_inviare_visibility(self, cr, uid, ids, name, arg, context=None):
        return {}

    def _da_inviare_visibility_search(self, cr, uid, obj, name, args, domain=None, context=None):
        time_start = time.time()
        results = self._da_inviare_query(cr, uid, 'search')
        protocollo_visible_ids = [res[0] for res in results]
        time_end = time.time()
        time_duration = time_end - time_start
        _logger.debug("_da_inviare_visibility_search: %s sec" % (time_duration,))
        return [('id', 'in', protocollo_visible_ids)]

    @api.cr_uid
    def _da_inviare_visibility_count(self, cr, uid):
        time_start = time.time()
        result = self._da_inviare_query(cr, uid, 'count')
        count_value = result[0][0]
        time_end = time.time()
        time_duration = time_end - time_start
        _logger.debug("_da_inviare_visibility_count: %s - %s sec" % (count_value, time_duration))
        return count_value

    ####################################################################################################################

    ####################################################################################################################
    # Filtri sulle viste tree dei protocolli
    ####################################################################################################################

    def _da_assegnare_general_visibility(self, cr, uid, ids, name, arg, context=None):
        return {}

    def _da_assegnare_general_visibility_search(self, cr, uid, obj, name, args, domain=None, context=None):
        start = int(round(time.time() * 1000))
        if context and 'archivio_id' in context and context['archivio_id']:
            archivio_id = context['archivio_id']
        else:
            archivio_id = self.pool.get('protocollo.archivio').search(cr, uid, [('is_current', '=', True)], limit=1)[0]
        cr.execute('''
            SELECT DISTINCT(pp.id) 
            FROM protocollo_protocollo AS pp
            WHERE pp.state IN ('registered', 'notified', 'waiting', 'sent', 'error') AND 
                  pp.da_assegnare = TRUE AND 
                  pp.archivio_id = %s
        ''', (uid, archivio_id))
        protocollo_visible_ids = [res[0] for res in cr.fetchall()]
        end = int(round(time.time() * 1000))
        _logger.debug("_da_assegnare_general_visibility_search" + str(end - start))
        return [('id', 'in', protocollo_visible_ids)]

    def _get_protocollo_assegnazione_ids(self, cr, uid, tipologia_assegnazione, tipologia_assegnatario, nome, context=None):
        if context and 'archivio_id' in context and context['archivio_id']:
            archivio_id = context['archivio_id']
        else:
            archivio_id = self.pool.get('protocollo.archivio').search(cr, uid, [('is_current', '=', True)], limit=1)[0]
        cr.execute('''
            SELECT DISTINCT(pa.protocollo_id) 
            FROM protocollo_protocollo pp, protocollo_assegnazione pa, protocollo_assegnatario ass
            WHERE pp.id = pa.protocollo_id AND 
                  pa.tipologia_assegnazione = %s AND
                  pa.tipologia_assegnatario = %s AND
                  pa.parent_id IS NULL AND
                  pa.assegnatario_id = ass.id AND 
                  ass.nome ILIKE %s AND 
                  pa.archivio_id = %s
        ''', (tipologia_assegnazione, tipologia_assegnatario, '%' + nome + '%', archivio_id))
        protocollo_ids = [res[0] for res in cr.fetchall()]
        return protocollo_ids

    def _get_assegnazione_competenza_dipendente_ids(self, cr, uid, ids, field_names, arg=None, context=None):
        result = dict((res_id, []) for res_id in ids)
        return result

    def _search_assegnazione_competenza_dipendente_ids(self, cr, uid, obj, name, args, domain=None, context=None):
        #TODO: gestire gli altri casi della ricerca
        return [('id', 'in', self._get_protocollo_assegnazione_ids(cr, uid, 'competenza', 'employee', args[0][2], context))]

    def _get_assegnazione_competenza_ufficio_ids(self, cr, uid, ids, field_names, arg=None, context=None):
        result = dict((res_id, []) for res_id in ids)
        return result

    def _search_assegnazione_competenza_ufficio_ids(self, cr, uid, obj, name, args, domain=None, context=None):
        #TODO: gestire gli altri casi della ricerca
        return [('id', 'in', self._get_protocollo_assegnazione_ids(cr, uid, 'competenza', 'department', args[0][2], context))]

    def _get_assegnazione_conoscenza_dipendente_ids(self, cr, uid, ids, field_names, arg=None, context=None):
        result = dict((res_id, []) for res_id in ids)
        return result

    def _search_assegnazione_conoscenza_dipendente_ids(self, cr, uid, obj, name, args, domain=None, context=None):
        #TODO: gestire gli altri casi della ricerca
        return [('id', 'in', self._get_protocollo_assegnazione_ids(cr, uid, 'conoscenza', 'employee', args[0][2], context))]

    def _get_assegnazione_conoscenza_ufficio_ids(self, cr, uid, ids, field_names, arg=None, context=None):
        result = dict((res_id, []) for res_id in ids)
        return result

    def _search_assegnazione_conoscenza_ufficio_ids(self, cr, uid, obj, name, args, domain=None, context=None):
        #TODO: gestire gli altri casi della ricerca
        return [('id', 'in', self._get_protocollo_assegnazione_ids(cr, uid, 'conoscenza', 'department', args[0][2], context))]

    def _filtro_a_me_competenza_visibility(self, cr, uid, ids, name, arg, context=None):
        return {}

    def _filtro_a_me_competenza_visibility_search(self, cr, uid, obj, name, args, domain=None, context=None):
        start = int(round(time.time() * 1000))
        if context and 'archivio_id' in context and context['archivio_id']:
            archivio_id = context['archivio_id']
        else:
            archivio_id = self.pool.get('protocollo.archivio').search(cr, uid, [('is_current', '=', True)], limit=1)[0]
        cr.execute('''
            SELECT DISTINCT(pa.protocollo_id) 
            FROM protocollo_protocollo pp, protocollo_assegnazione pa, hr_employee he, resource_resource rr
            WHERE pp.id = pa.protocollo_id AND 
                  pa.assegnatario_employee_id = he.id AND
                  he.resource_id = rr.id AND
                  rr.user_id = %s AND
                  rr.active = TRUE AND
                  pp.registration_date IS NOT NULL AND
                  pa.tipologia_assegnatario = 'employee' AND 
                  pa.parent_id IS NULL AND
                  pa.tipologia_assegnazione = 'competenza' AND 
                  pa.archivio_id = %s
        ''', (uid, archivio_id))
        protocollo_visible_ids = [res[0] for res in cr.fetchall()]
        end = int(round(time.time() * 1000))
        _logger.debug("_filtro_a_me_competenza_visibility_search: " + str(end - start))
        return [('id', 'in', protocollo_visible_ids)]

    def _filtro_a_me_conoscenza_visibility(self, cr, uid, ids, name, arg, context=None):
        return {}

    def _filtro_a_me_conoscenza_visibility_search(self, cr, uid, obj, name, args, domain=None, context=None):
        start = int(round(time.time() * 1000))
        if context and 'archivio_id' in context and context['archivio_id']:
            archivio_id = context['archivio_id']
        else:
            archivio_id = self.pool.get('protocollo.archivio').search(cr, uid, [('is_current', '=', True)], limit=1)[0]
        cr.execute('''
            SELECT DISTINCT(pa.protocollo_id) 
            FROM protocollo_protocollo pp, protocollo_assegnazione pa, hr_employee he, resource_resource rr
            WHERE pp.id = pa.protocollo_id AND 
                  pa.assegnatario_employee_id = he.id AND
                  he.resource_id = rr.id AND
                  rr.user_id = %s AND
                  rr.active = TRUE AND
                  pp.registration_date IS NOT NULL AND
                  pa.tipologia_assegnatario = 'employee' AND 
                  pa.parent_id IS NULL AND
                  pa.tipologia_assegnazione = 'conoscenza' AND 
                  pa.archivio_id = %s
        ''', (uid, archivio_id))
        protocollo_visible_ids = [res[0] for res in cr.fetchall()]
        end = int(round(time.time() * 1000))
        _logger.debug("_filtro_a_me_conocenza_visibility_search: " + str(end - start))
        return [('id', 'in', protocollo_visible_ids)]

    def _filtro_a_mio_ufficio_visibility(self, cr, uid, ids, name, arg, context=None):
        return {}

    def _filtro_a_mio_ufficio_visibility_search(self, cr, uid, obj, name, args, domain=None, context=None):
        start = int(round(time.time() * 1000))
        if context and 'archivio_id' in context and context['archivio_id']:
            archivio_id = context['archivio_id']
        else:
            archivio_id = self.pool.get('protocollo.archivio').search(cr, uid, [('is_current', '=', True)], limit=1)[0]
        cr.execute('''
            SELECT DISTINCT(pa.protocollo_id) 
            FROM protocollo_protocollo pp, protocollo_assegnazione pa, hr_department hd, hr_employee he, resource_resource rr
            WHERE pp.id = pa.protocollo_id AND 
                  pa.assegnatario_department_id = hd.id AND
                  hd.id=he.department_id AND
                  he.resource_id = rr.id AND
                  rr.user_id = %s AND
                  rr.active = TRUE AND
                  pp.registration_date IS NOT NULL AND
                  pa.tipologia_assegnatario = 'department' AND 
                  pa.tipologia_assegnazione = 'competenza' AND 
                  pa.archivio_id = %s
        ''', (uid, archivio_id))
        protocollo_visible_ids = [res[0] for res in cr.fetchall()]
        end = int(round(time.time() * 1000))
        _logger.debug("_filtro_a_mio_ufficio_visibility_search: " + str(end - start))
        return [('id', 'in', protocollo_visible_ids)]

    def _filtro_a_mio_ufficio_cc_visibility(self, cr, uid, ids, name, arg, context=None):
        return {}

    def _filtro_a_mio_ufficio_cc_visibility_search(self, cr, uid, obj, name, args, domain=None, context=None):
        start = int(round(time.time() * 1000))
        if context and 'archivio_id' in context and context['archivio_id']:
            archivio_id = context['archivio_id']
        else:
            archivio_id = self.pool.get('protocollo.archivio').search(cr, uid, [('is_current', '=', True)], limit=1)[0]
        cr.execute('''
            SELECT DISTINCT(pa.protocollo_id) 
            FROM protocollo_protocollo pp, protocollo_assegnazione pa, hr_department hd, hr_employee he, resource_resource rr
            WHERE pp.id = pa.protocollo_id AND 
                  pa.assegnatario_department_id = hd.id AND
                  hd.id=he.department_id AND
                  he.resource_id = rr.id AND
                  rr.user_id = %s AND
                  rr.active = TRUE AND
                  pp.registration_date IS NOT NULL AND
                  pa.tipologia_assegnatario = 'department' AND 
                  pa.tipologia_assegnazione = 'conoscenza' AND 
                  pa.archivio_id = %s
        ''', (uid, archivio_id))
        protocollo_visible_ids = [res[0] for res in cr.fetchall()]
        end = int(round(time.time() * 1000))
        _logger.debug("_filtro_a_mio_ufficio_cc_visibility_search" + str(end - start))
        return [('id', 'in', protocollo_visible_ids)]

    def _filtro_da_me_visibility(self, cr, uid, ids, name, arg, context=None):
        return {}

    def _filtro_da_me_visibility_search(self, cr, uid, obj, name, args, domain=None, context=None):
        start = int(round(time.time() * 1000))
        if context and 'archivio_id' in context and context['archivio_id']:
            archivio_id = context['archivio_id']
        else:
            archivio_id = self.pool.get('protocollo.archivio').search(cr, uid, [('is_current', '=', True)], limit=1)[0]
        cr.execute('''
            SELECT DISTINCT(pa.protocollo_id) 
            FROM protocollo_protocollo pp, protocollo_assegnazione pa, hr_employee he, resource_resource rr
            WHERE pp.id = pa.protocollo_id AND 
                  pa.assegnatore_id = he.id AND
                  he.resource_id = rr.id AND
                  rr.user_id = %s AND
                  rr.active = TRUE AND
                  pp.registration_date IS NOT NULL AND
                  (pa.tipologia_assegnatario = 'department' OR (pa.tipologia_assegnatario = 'employee' AND pa.parent_id IS NULL)) AND 
                  pa.archivio_id = %s
        ''', (uid, archivio_id))
        protocollo_visible_ids = [res[0] for res in cr.fetchall()]
        end = int(round(time.time() * 1000))
        _logger.debug("_filtro_da_me_visibility_search: " + str(end - start))
        return [('id', 'in', protocollo_visible_ids)]

    def _filtro_competenza_visibility(self, cr, uid, ids, name, arg, context=None):
        return {}

    def _filtro_competenza_visibility_search(self, cr, uid, obj, name, args, domain=None, context=None):
        start = int(round(time.time() * 1000))
        if context and 'archivio_id' in context and context['archivio_id']:
            archivio_id = context['archivio_id']
        else:
            archivio_id = self.pool.get('protocollo.archivio').search(cr, uid, [('is_current', '=', True)], limit=1)[0]
        cr.execute('''
            SELECT DISTINCT(pa.protocollo_id) 
            FROM protocollo_protocollo pp, protocollo_assegnazione pa, hr_employee he, resource_resource rr
            WHERE pp.id = pa.protocollo_id AND 
                  pa.assegnatore_id = he.id AND
                  he.resource_id = rr.id AND
                  rr.active = TRUE AND
                  pp.registration_date IS NOT NULL AND
                  pa.tipologia_assegnazione = 'competenza' AND 
                  pa.archivio_id = %s
        ''', (archivio_id,))
        protocollo_visible_ids = [res[0] for res in cr.fetchall()]
        end = int(round(time.time() * 1000))
        _logger.debug("_filtro_competenza_visibility_search" + str(end - start))
        return [('id', 'in', protocollo_visible_ids)]

    def _filtro_conoscenza_visibility(self, cr, uid, ids, name, arg, context=None):
        return {}

    def _filtro_conoscenza_visibility_search(self, cr, uid, obj, name, args, domain=None, context=None):
        start = int(round(time.time() * 1000))
        if context and 'archivio_id' in context and context['archivio_id']:
            archivio_id = context['archivio_id']
        else:
            archivio_id = self.pool.get('protocollo.archivio').search(cr, uid, [('is_current', '=', True)], limit=1)[0]
        cr.execute('''
            SELECT DISTINCT(pa.protocollo_id) 
            FROM protocollo_protocollo pp, protocollo_assegnazione pa, hr_employee he, resource_resource rr
            WHERE pp.id = pa.protocollo_id AND 
                  pa.assegnatore_id = he.id AND
                  he.resource_id = rr.id AND
                  rr.active = TRUE AND
                  pp.registration_date IS NOT NULL AND
                  pa.tipologia_assegnazione = 'conoscenza' AND 
                  pa.archivio_id = %s
        ''', (archivio_id,))
        protocollo_visible_ids = [res[0] for res in cr.fetchall()]
        end = int(round(time.time() * 1000))
        _logger.debug("_filtro_conoscenza_visibility_search" + str(end - start))
        return [('id', 'in', protocollo_visible_ids)]

    def _filtro_da_me_in_attesa_visibility(self, cr, uid, ids, name, arg, context=None):
        return {}

    def _filtro_da_me_in_attesa_visibility_search(self, cr, uid, obj, name, args, domain=None, context=None):
        archivio_id = None
        if context and 'archivio_id' in context and context['archivio_id']:
            archivio_id = context['archivio_id']
        time_start = time.time()
        results = self._assegnato_da_me_in_attesa_query(cr, uid, 'search', archivio_id)
        protocollo_visible_ids = [res[0] for res in results]
        time_end = time.time()
        time_duration = time_end - time_start
        _logger.debug("_filtro_da_me_in_attesa_visibility_search: %s sec" % (time_duration,))
        return [('id', 'in', protocollo_visible_ids)]

    ####################################################################################################################
    # Visibilità dei button sui protocolli
    ####################################################################################################################

    def _registra_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        #start_time = time.time()
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False

            if protocollo.state == 'draft':
                check = True

            if check:
                types = self.get_protocollo_types_by_group(cr, uid, 'seedoo_protocollo', 'group_registra_protocollo_', '')
                check_gruppi = protocollo.type in types
                check = check and check_gruppi

            res.append((protocollo.id, check))

        #_logger.debug("--- TEMPO _registra_visibility: %s SECONDI ---" % (time.time() - start_time))
        return dict(res)

    def _elimina_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        #start_time = time.time()
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False

            if protocollo.state == 'draft' and \
                    (uid == protocollo.user_id.id or uid == SUPERUSER_ID) and \
                    not protocollo.mail_pec_ref and \
                    not protocollo.doc_imported_ref:
                check = True

            res.append((protocollo.id, check))

        #_logger.debug("--- TEMPO _elimina_visibility: %s SECONDI ---" % (time.time() - start_time))
        return dict(res)

    def _annulla_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        #start_time = time.time()
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False

            if protocollo.state in ['registered', 'notified', 'sent', 'waiting', 'error']:
                check = True

            if check:
                types = self.get_protocollo_types_by_group(cr, uid, 'seedoo_protocollo', 'group_annulla_protocollo_', '')
                check_gruppi = protocollo.type in types
                check = check and check_gruppi

            res.append((protocollo.id, check))

        #_logger.debug("--- TEMPO _annulla_visibility: %s SECONDI ---" % (time.time() - start_time))
        return dict(res)

    def assegnazione_validation(self, cr, uid, protocollo, action, context={}):
        if not (action in ['prendi_in_carico', 'rifiuta']):
            return False, _("non è possibile eseguire la action selezionata")

        if action == 'prendi_in_carico':
            group_id = 'group_prendi_in_carico_protocollo_'
            group_name = 'Presa in Carico Protocolli Assegnati Ufficio'
            action_name = 'preso in carico'
        else:
            group_id = 'group_rifiuta_protocollo_'
            group_name = 'Rifiuta Protocolli Assegnati Ufficio'
            action_name = 'rifiutato'

        if not (protocollo.state in ['registered', 'notified', 'waiting', 'sent', 'error']):
            return False, _("il protocollo non può essere %s nello stato attuale" % action_name)

        if not protocollo.assegnazione_competenza_ids:
            return False, _("il protocollo non ha nessuna assegnazione per competenza")

        assegnatario_employee_id = None
        employee_obj = self.pool.get('hr.employee')
        department_obj = self.pool.get('hr.department')
        if context and 'assegnatario_employee_id' in context and context['assegnatario_employee_id']:
            assegnatario_employee_id = context['assegnatario_employee_id']
            employee_ids = [assegnatario_employee_id]
            department_ids = department_obj.search(cr, uid, [('member_ids', '=', assegnatario_employee_id)])
        else:
            employee_ids = employee_obj.search(cr, uid, [('user_id', '=', uid)])
            department_ids = department_obj.search(cr, uid, [('member_ids.user_id', '=', uid)])

        check_competenza_ufficio = self._check_stato_assegnatario_competenza_ufficio(cr, uid, protocollo, 'assegnato', assegnatario_employee_id)
        check_competenza_dipendente = self._check_stato_assegnatario_competenza(cr, uid, protocollo, 'assegnato', assegnatario_employee_id)

        result = False
        result_description = _("il dipendente non è un assegnatario per competenza del protocollo")
        for assegnazione_competenza in protocollo.assegnazione_competenza_ids:
            if assegnazione_competenza.tipologia_assegnatario == 'department':
                if assegnazione_competenza.assegnatario_department_id.id in department_ids:
                    if check_competenza_ufficio:
                        if not assegnatario_employee_id:
                            types = self.get_protocollo_types_by_group(cr, uid, 'seedoo_protocollo', group_id, '')
                            if not (protocollo.type in types):
                                type_str = ''
                                for selection_tuple_value in self._fields['type'].selection:
                                    if protocollo.type == selection_tuple_value[0]:
                                        type_str = selection_tuple_value[1]
                                        break
                                result_description = _("l'utente non possiede il permesso '%s' per i protocolli di tipologia '%s'" % (group_name, type_str))
                            else:
                                return True, None
                        else:
                            return True, None
                    else:
                        result_description = _("lo stato dell'assegnazione per competenza deve essere 'Assegnato'")
            elif assegnazione_competenza.assegnatario_employee_id.id in employee_ids:
                if check_competenza_dipendente:
                    return True, None
                else:
                    result_description = _("lo stato dell'assegnazione per competenza deve essere 'Assegnato'")

        return result, result_description

    def _prendi_in_carico_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        #start_time = time.time()
        res = []
        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check, error = self.assegnazione_validation(cr, uid, protocollo, 'prendi_in_carico', context)
            res.append((protocollo.id, check))
        #_logger.debug("--- TEMPO _prendi_in_carico_visibility: %s SECONDI ---" % (time.time() - start_time))
        return dict(res)

    def _rifiuta_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        #start_time = time.time()
        res = []
        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check, error = self.assegnazione_validation(cr, uid, protocollo, 'rifiuta', context)
            res.append((protocollo.id, check))
        #_logger.debug("--- TEMPO _rifiuta_visibility: %s SECONDI ---" % (time.time() - start_time))
        return dict(res)

    def _segna_come_letto_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        #start_time = time.time()
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False

            #TODO: modificare controllando per singolo ufficio
            if protocollo.state in ('registered', 'notified', 'waiting', 'sent', 'error') and \
                     protocollo.assegnazione_conoscenza_ids:
                check = True

            if check:
                check_ufficio = self._check_stato_assegnatario_conoscenza_ufficio(cr, uid, protocollo, 'assegnato')
                check_dipendente = self._check_stato_assegnatario_conoscenza(cr, uid, protocollo, 'assegnato')
                check = check_ufficio or check_dipendente
                types = self.get_protocollo_types_by_group(cr, uid, 'seedoo_protocollo', 'group_segna_come_letto_protocollo_', '')
                check_gruppi = protocollo.type in types
                check = check and check_gruppi
            else:
                check = False

            res.append((protocollo.id, check))

        #_logger.debug("--- TEMPO _segna_come_letto_visibility: %s SECONDI ---" % (time.time() - start_time))
        return dict(res)

    def _modifica_dati_generali_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        #start_time = time.time()
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False

            if protocollo.state in ('registered', 'notified', 'error'):
                check = True

            if check:
                types = self.get_protocollo_types_by_group(cr, uid, 'seedoo_protocollo', 'group_modifica_protocollo_', '')
                check_gruppi = protocollo.type in types
                check = check and check_gruppi

            if (uid==protocollo.user_id.id and protocollo.registration_employee_state=='working') or uid == SUPERUSER_ID:
                check = check and True
            else:
                check = False
            # else:
            #     check_assegnatari = False
            # if check:
            #     check_assegnatari = self._check_stato_assegnatario_competenza(cr, uid, protocollo, 'preso')
            # check = check and check_assegnatari

            res.append((protocollo.id, check))

        #_logger.debug("--- TEMPO _modifica_dati_generali_visibility: %s SECONDI ---" % (time.time() - start_time))
        return dict(res)

    def _aggiungi_mittenti_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        #start_time = time.time()
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False

            if protocollo.type=='in' and protocollo.state in ['draft'] and not protocollo.senders:
                check = True

            res.append((protocollo.id, check))

        #_logger.debug("--- TEMPO _aggiungi_mittenti_visibility: %s SECONDI ---" % (time.time() - start_time))
        return dict(res)

    def _modifica_mittenti_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        #start_time = time.time()
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False

            if protocollo.type=='in' and protocollo.state in ['draft']:
                check = True

            res.append((protocollo.id, check))

        #_logger.debug("--- TEMPO _modifica_mittenti_visibility: %s SECONDI ---" % (time.time() - start_time))
        return dict(res)

    def _aggiungi_destinatari_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        #start_time = time.time()
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False

            if protocollo.type=='out' and protocollo.state in ['draft']:
                check = True

            res.append((protocollo.id, check))

        #_logger.debug("--- TEMPO _aggiungi_destinatari_visibility: %s SECONDI ---" % (time.time() - start_time))
        return dict(res)

    def _modifica_destinatari_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        #start_time = time.time()
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False

            if protocollo.type=='out' and protocollo.state in ['draft']:
                check = True

            res.append((protocollo.id, check))

        #_logger.debug("--- TEMPO _modifica_destinatari_visibility: %s SECONDI ---" % (time.time() - start_time))
        return dict(res)

    def _aggiungi_mittente_interno_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        #start_time = time.time()
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False

            if protocollo.type!='in' and protocollo.state in ['draft'] and not protocollo.sender_internal_name:
                check = True

            res.append((protocollo.id, check))

        #_logger.debug("--- TEMPO _aggiungi_mittente_interno_visibility: %s SECONDI ---" % (time.time() - start_time))
        return dict(res)

    def _modifica_mittente_interno_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        #start_time = time.time()
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False

            if protocollo.type!='in' and protocollo.state in ['draft'] and protocollo.sender_internal_name:
                check = True

            res.append((protocollo.id, check))

        #_logger.debug("--- TEMPO _modifica_mittente_interno_visibility: %s SECONDI ---" % (time.time() - start_time))
        return dict(res)

    def _aggiungi_classificazione_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        #start_time = time.time()
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False

            if protocollo.state in ['draft'] and not protocollo.classification:
                check = True

            res.append((protocollo.id, check))

        #_logger.debug("--- TEMPO _aggiungi_classificazione_visibility: %s SECONDI ---" % (time.time() - start_time))
        return dict(res)

    #TODO: attualmente rendiamo il button visibile solo al protocollatore, in futuro dovrà essere estesa anche all'assegnatore
    def _modifica_classificazione_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        #start_time = time.time()
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False

            if protocollo.classification and ((uid==protocollo.user_id.id and protocollo.registration_employee_state=='working') or uid==SUPERUSER_ID):
                if protocollo.state == 'draft':
                    check = True
                elif protocollo.state in ['registered', 'notified', 'waiting', 'sent', 'error']:
                    types = self.get_protocollo_types_by_group(cr, uid, 'seedoo_protocollo', 'group_modifica_classificazione_protocollo_', '')
                    check = protocollo.type in types

            res.append((protocollo.id, check))

        #_logger.debug("--- TEMPO _modifica_classificazione_visibility: %s SECONDI ---" % (time.time() - start_time))
        return dict(res)

    def _classifica_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        #start_time = time.time()
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False

            if protocollo.state in ('registered', 'notified', 'waiting', 'sent', 'error') and not protocollo.classification:
                check = True

            if check:
                types = self.get_protocollo_types_by_group(cr, uid, 'seedoo_protocollo', 'group_classifica_protocollo_', '')
                check_gruppi = protocollo.type in types
                check = check and check_gruppi

            if (uid==protocollo.user_id.id and protocollo.registration_employee_state=='working') or uid==SUPERUSER_ID:
                check = check and True
            else:
                check_assegnatari = False
                if check:
                    check_assegnatari = self._check_stato_assegnatario_competenza(cr, uid, protocollo, 'preso')
                check = check and check_assegnatari

            res.append((protocollo.id, check))

        #_logger.debug("--- TEMPO _classifica_visibility: %s SECONDI ---" % (time.time() - start_time))
        return dict(res)

    def _aggiungi_fascicolazione_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        #start_time = time.time()
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False

            if not protocollo.dossier_ids:
                if protocollo.state == 'draft':
                    check = (uid==protocollo.user_id.id and protocollo.registration_employee_state=='working') or uid==SUPERUSER_ID
                elif protocollo.state in ['registered', 'notified', 'waiting', 'sent', 'error']:
                    types = self.get_protocollo_types_by_group(cr, uid, 'seedoo_protocollo', 'group_modifica_fascicolazione_protocollo_', '')
                    check = protocollo.type in types
                    if check:
                        if (uid == protocollo.user_id.id and protocollo.registration_employee_state == 'working') or uid == SUPERUSER_ID:
                            check = True
                        else:
                            assegnazione_competenza = self._check_stato_assegnatario_competenza(cr, uid, protocollo, 'preso')
                            assegnazione_conoscenza = self._check_stato_assegnatario_conoscenza(cr, uid, protocollo, 'letto')
                            check = assegnazione_competenza or assegnazione_conoscenza

            res.append((protocollo.id, check))

        #_logger.debug("--- TEMPO _aggiungi_fascicolazione_visibility: %s SECONDI ---" % (time.time() - start_time))
        return dict(res)

    def _modifica_fascicolazione_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        #start_time = time.time()
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False

            if protocollo.dossier_ids:
                if protocollo.state == 'draft':
                    check = (uid==protocollo.user_id.id and protocollo.registration_employee_state=='working') or uid==SUPERUSER_ID
                elif protocollo.state in ['registered', 'notified', 'waiting', 'sent', 'error']:
                    types = self.get_protocollo_types_by_group(cr, uid, 'seedoo_protocollo', 'group_modifica_fascicolazione_protocollo_', '')
                    check = protocollo.type in types
                    if check:
                        if (uid == protocollo.user_id.id and protocollo.registration_employee_state == 'working') or uid == SUPERUSER_ID:
                            check = True
                        else:
                            assegnazione_competenza = self._check_stato_assegnatario_competenza(cr, uid, protocollo, 'preso')
                            assegnazione_conoscenza = self._check_stato_assegnatario_conoscenza(cr, uid, protocollo, 'letto')
                            check = assegnazione_competenza or assegnazione_conoscenza

            res.append((protocollo.id, check))

        #_logger.debug("--- TEMPO _modifica_fascicolazione_visibility: %s SECONDI ---" % (time.time() - start_time))
        return dict(res)

    def _fascicola_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        #start_time = time.time()
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False

            if protocollo.state in ('registered', 'notified', 'waiting', 'sent', 'error') and not protocollo.dossier_ids:
                check = True

            if check:
                types = self.get_protocollo_types_by_group(cr, uid, 'seedoo_protocollo', 'group_fascicola_protocollo_', '')
                check_gruppi = protocollo.type in types
                check = check and check_gruppi

            if check:
                if (uid==protocollo.user_id.id and protocollo.registration_employee_state=='working') or uid==SUPERUSER_ID:
                    check = True
                else:
                    assegnazione_competenza = self._check_stato_assegnatario_competenza(cr, uid, protocollo, 'preso')
                    assegnazione_conoscenza = self._check_stato_assegnatario_conoscenza(cr, uid, protocollo, 'letto')
                    check = assegnazione_competenza or assegnazione_conoscenza

            res.append((protocollo.id, check))

        #_logger.debug("--- TEMPO _fascicola_visibility: %s SECONDI ---" % (time.time() - start_time))
        return dict(res)

    def _aggiungi_assegnatari_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        #start_time = time.time()
        res = []
        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = self._check_aggiungi_assegnatari_visibility(cr, uid, protocollo)
            res.append((protocollo.id, check))
        #_logger.debug("--- TEMPO _aggiungi_assegnatari_visibility: %s SECONDI ---" % (time.time() - start_time))
        return dict(res)

    def _check_aggiungi_assegnatari_visibility(self, cr, uid, protocollo):
        check = False
        if protocollo.state == 'draft' and not protocollo.assegnazione_first_level_ids:
            check = True
        elif protocollo.state in ['registered', 'notified', 'waiting', 'sent', 'error'] and \
                uid==protocollo.user_id.id and \
                protocollo.registration_employee_state=='working' and \
                not protocollo.assegnazione_competenza_ids:
            check = True
        return check

    def _modifica_assegnatari_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        assegnazione_obj = self.pool.get('protocollo.assegnazione')
        #start_time = time.time()
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False

            count = assegnazione_obj.search(cr, uid, [('protocollo_id', '=', protocollo.id)], count=True)
            if count:

                if protocollo.state == 'draft' and (uid == protocollo.user_id.id or uid == SUPERUSER_ID):
                    check = True
                elif protocollo.state in ['registered', 'notified', 'waiting', 'sent', 'error']:
                    types = self.get_protocollo_types_by_group(cr, uid, 'seedoo_protocollo', 'group_modifica_assegnatari_protocollo_', '')
                    check = protocollo.type in types

            res.append((protocollo.id, check))

        #_logger.debug("--- TEMPO _modifica_assegnatari_visibility: %s SECONDI ---" % (time.time() - start_time))
        return dict(res)

    def _aggiungi_assegnatari_cc_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        #start_time = time.time()
        res = []
        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = self._check_aggiungi_assegnatari_cc_visibility(cr, uid, protocollo)
            res.append((protocollo.id, check))
        #_logger.debug("--- TEMPO _aggiungi_assegnatari_cc_visibility: %s SECONDI ---" % (time.time() - start_time))
        return dict(res)

    def _check_aggiungi_assegnatari_cc_visibility(self, cr, uid, protocollo):
        check = False

        if protocollo.state in ('registered', 'notified', 'waiting', 'sent', 'error') \
                and protocollo.assegnazione_competenza_ids and not protocollo.reserved:
            check = True

        if check:
            types = self.get_protocollo_types_by_group(cr, uid, 'seedoo_protocollo', 'group_aggiungi_assegnatari_cc_protocollo_', '')
            check_gruppi = protocollo.type in types
            check = check and check_gruppi

        if (uid==protocollo.user_id.id and protocollo.registration_employee_state=='working') or uid==SUPERUSER_ID:
            check = check and True
        else:
            check_assegnatari = False
            if check:
                check_assegnatari = self._check_stato_assegnatario_competenza(cr, uid, protocollo, 'preso')
            check = check and check_assegnatari

        return check

    def _assegna_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        #start_time = time.time()
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False

            if protocollo.state in ('registered', 'notified', 'waiting', 'sent', 'error') and \
                    not protocollo.assegnazione_competenza_ids:
                check = True

            if check:
                types = self.get_protocollo_types_by_group(cr, uid, 'seedoo_protocollo', 'group_assegna_protocollo_', '')
                check_gruppi = protocollo.type in types
                check = check and check_gruppi

            if (uid==protocollo.user_id.id and protocollo.registration_employee_state=='working') or uid==SUPERUSER_ID:
                check = check and True
            else:
                check = False

            res.append((protocollo.id, check))

        #_logger.debug("--- TEMPO _assegna_visibility: %s SECONDI ---" % (time.time() - start_time))
        return dict(res)

    def _riassegna_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        #start_time = time.time()
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False

            if protocollo.state in ('registered', 'notified', 'waiting', 'sent', 'error'):
                check = True

            if check:
                types = self.get_protocollo_types_by_group(cr, uid, 'seedoo_protocollo', 'group_riassegna_protocollo_', '')
                check_gruppi = protocollo.type in types
                check = check and check_gruppi

            if uid==SUPERUSER_ID or \
                    self._check_stato_assegnatore_competenza(cr, uid, protocollo, 'rifiutato') and \
                    (
                            (uid==protocollo.user_id.id and protocollo.registration_employee_state=='working') or \
                            self._check_stato_assegnatario_competenza(cr, uid, protocollo, 'preso')
                    ):
                check = check and True
            else:
                check = False

            res.append((protocollo.id, check))

        #_logger.debug("--- TEMPO _riassegna_visibility: %s SECONDI ---" % (time.time() - start_time))
        return dict(res)

    def _invio_pec_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        #start_time = time.time()
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False

            if protocollo.state == 'registered' and protocollo.type == 'out' and protocollo.pec is True:
                check = True

            if check:
                dipendente_id = False
                if context and 'dipendente_id' in context and context['dipendente_id']:
                    dipendente_id = context['dipendente_id']
                protocollatore_condition = uid==protocollo.user_id.id and protocollo.registration_employee_state=='working'
                if ((protocollatore_condition or uid==SUPERUSER_ID) and self.user_has_groups(cr, uid, 'seedoo_protocollo.group_invia_protocollo_pec_uscita')) or \
                    (protocollo.registration_employee_id.id==dipendente_id and protocollo.registration_employee_state=='working'):
                    check = True
                else:
                    check = False

            res.append((protocollo.id, check))

        #_logger.debug("--- TEMPO _invio_pec_visibility: %s SECONDI ---" % (time.time() - start_time))
        return dict(res)

    def _invio_sharedmail_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        #start_time = time.time()
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False

            if protocollo.state == 'registered' and protocollo.type == 'out' and protocollo.sharedmail is True:
                check = True

            if check:
                dipendente_id = False
                if context and 'dipendente_id' in context and context['dipendente_id']:
                    dipendente_id = context['dipendente_id']
                protocollatore_condition = uid==protocollo.user_id.id and protocollo.registration_employee_state=='working'
                if ((protocollatore_condition or uid==SUPERUSER_ID) and self.user_has_groups(cr, uid, 'seedoo_protocollo.group_invia_protocollo_sharedmail_uscita')) or \
                    (protocollo.registration_employee_id.id==dipendente_id and protocollo.registration_employee_state=='working'):
                    check = True
                else:
                    check = False

            res.append((protocollo.id, check))

        #_logger.debug("--- TEMPO _invio_sharedmail_visibility: %s SECONDI ---" % (time.time() - start_time))
        return dict(res)

    def _invio_protocollo_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        #start_time = time.time()
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False
            if protocollo.state == 'registered' and protocollo.type == 'out' and protocollo.pec is False and protocollo.sharedmail is False:
                check = True

            if check:
                dipendente_id = False
                if context and 'dipendente_id' in context and context['dipendente_id']:
                    dipendente_id = context['dipendente_id']
                protocollatore_condition = uid==protocollo.user_id.id and protocollo.registration_employee_state=='working'
                if ((protocollatore_condition or uid==SUPERUSER_ID) and self.user_has_groups(cr, uid, 'seedoo_protocollo.group_invia_protocollo_uscita')) or \
                    (protocollo.registration_employee_id.id==dipendente_id and protocollo.registration_employee_state=='working'):
                    check = True
                else:
                    check = False

            res.append((protocollo.id, check))

        #_logger.debug("--- TEMPO _invio_protocollo_visibility: %s SECONDI ---" % (time.time() - start_time))
        return dict(res)

    def _modifica_pec_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        #start_time = time.time()
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False
            if protocollo.type == 'out' and protocollo.pec is True and protocollo.state in ['waiting', 'sent', 'error']:
                if protocollo.sender_receivers:
                    for sender_receiver_id in protocollo.sender_receivers.ids:
                        sender_receiver_obj = self.pool.get('protocollo.sender_receiver').browse(cr, uid, sender_receiver_id, context=context)
                        if sender_receiver_obj.pec_errore_consegna_status or sender_receiver_obj.pec_non_accettazione_status:
                            check = True

            if check:
                if ((uid==protocollo.user_id.id and protocollo.registration_employee_state=='working') or uid==SUPERUSER_ID) and \
                        self.user_has_groups(cr, uid, 'seedoo_protocollo.group_modifica_destinatari_pec_uscita'):
                    check = True
                else:
                    check = False

            res.append((protocollo.id, check))

        #_logger.debug("--- TEMPO _modifica_pec_visibility: %s SECONDI ---" % (time.time() - start_time))
        return dict(res)

    def _modifica_email_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        #start_time = time.time()
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False

            if protocollo.type == 'out' and protocollo.sharedmail == True and protocollo.state in ['sent', 'waiting', 'error']:
                check = True

            if check:
                if ((uid==protocollo.user_id.id and protocollo.registration_employee_state=='working') or uid==SUPERUSER_ID) and \
                        self.user_has_groups(cr, uid, 'seedoo_protocollo.group_modifica_destinatari_email_uscita'):
                    check = True
                else:
                    check = False

            res.append((protocollo.id, check))

        #_logger.debug("--- TEMPO _modifica_email_visibility: %s SECONDI ---" % (time.time() - start_time))
        return dict(res)

    def _aggiungi_pec_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        #start_time = time.time()
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False
            if protocollo.type == 'out' and protocollo.pec is True and protocollo.state in ['waiting', 'sent', 'error']:
                check = True

            if check:
                if ((uid==protocollo.user_id.id and protocollo.registration_employee_state=='working') or uid==SUPERUSER_ID) and \
                        self.user_has_groups(cr, uid, 'seedoo_protocollo.group_aggiungi_destinatari_pec_uscita'):
                    check = True
                else:
                    check = False

            res.append((protocollo.id, check))

        #_logger.debug("--- TEMPO _aggiungi_pec_visibility: %s SECONDI ---" % (time.time() - start_time))
        return dict(res)

    def _protocollazione_riservata_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        #start_time = time.time()
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = self.user_has_groups(cr, uid, 'seedoo_protocollo.group_protocollazione_riservata')

            res.append((protocollo.id, check))

        #_logger.debug("--- TEMPO _protocollazione_riservata_visibility: %s SECONDI ---" % (time.time() - start_time))
        return dict(res)

    def _inserisci_testo_mailpec_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        #start_time = time.time()
        res = []
        check = False
        configurazione_ids = self.pool.get('protocollo.configurazione').search(cr, uid, [])
        configurazione = self.pool.get('protocollo.configurazione').browse(cr, uid, configurazione_ids[0])
        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:

            if configurazione.inserisci_testo_mailpec:
                check = True

            res.append((protocollo.id, check))

        #_logger.debug("--- TEMPO _inserisci_testo_mailpec_visibility: %s SECONDI ---" % (time.time() - start_time))
        return dict(res)

    def _carica_allegati_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        #start_time = time.time()
        res = []
        check = False
        configurazione_ids = self.pool.get('protocollo.configurazione').search(cr, uid, [])
        configurazione = self.pool.get('protocollo.configurazione').browse(cr, uid, configurazione_ids[0])
        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:

            if protocollo.state == 'draft' or \
                    (
                        protocollo.state in ('registered', 'notified', 'waiting', 'sent', 'error') and \
                        uid == protocollo.user_id.id and \
                        protocollo.registration_employee_state == 'working' and \
                        configurazione.aggiungi_allegati_post_registrazione
                    ):
                check = True

            res.append((protocollo.id, check))

        #_logger.debug("--- TEMPO _carica_allegati_visibility: %s SECONDI ---" % (time.time() - start_time))
        return dict(res)

    def _modifica_allegati_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        #start_time = time.time()
        res = []
        check = False
        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:

            if protocollo.state == 'draft':
                check = True

            res.append((protocollo.id, check))

        #_logger.debug("--- TEMPO _modifica_allegati_visibility: %s SECONDI ---" % (time.time() - start_time))
        return dict(res)

    def _carica_documento_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        #start_time = time.time()
        res = []
        check = False
        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:

            if not protocollo.doc_id and \
                    (protocollo.state in 'draft' or \
                     (uid==protocollo.user_id.id and protocollo.registration_employee_state=='working')
                    ):
                check = True

            res.append((protocollo.id, check))

        #_logger.debug("--- TEMPO _carica_documento_visibility: %s SECONDI ---" % (time.time() - start_time))
        return dict(res)

    def _modifica_documento_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        #start_time = time.time()
        res = []
        check = False
        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:

            if protocollo.doc_id and protocollo.state in ['draft']:
                check = True

            res.append((protocollo.id, check))

        #_logger.debug("--- TEMPO _modifica_documento_visibility: %s SECONDI ---" % (time.time() - start_time))
        return dict(res)

    ####################################################################################################################
    # Modificabilità dei campi
    ####################################################################################################################
    def _protocollo_fields_editability(self, cr, uid, ids, prop, unknow_none, context=None):
        res = []
        check = False
        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            if protocollo.state == 'draft':
                check = True
            res.append((protocollo.id, check))

        return dict(res)

    def _typology_editability(self, cr, uid, ids, prop, unknow_none, context=None):
        res = []
        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False
            if protocollo.protocollo_fields_editability and not protocollo.mail_pec_ref:
                check = True
            res.append((protocollo.id, check))
        return dict(res)
    ####################################################################################################################

    ####################################################################################################################
    # Obbligatorietà dei campi
    ####################################################################################################################
    def _server_sharedmail_id_required(self, cr, uid, ids, prop, unknow_none, context=None):
        res = []
        check = False
        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            if protocollo.sharedmail and protocollo.type=='out':
                check = True
            res.append((protocollo.id, check))
        return dict(res)

    def _server_pec_id_required(self, cr, uid, ids, prop, unknow_none, context=None):
        res = []
        check = False
        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            if protocollo.pec and protocollo.type=='out':
                check = True
            res.append((protocollo.id, check))
        return dict(res)
    ####################################################################################################################

    _columns = {
        # Visibilità dei protocolli
        'is_visible': fields.function(_is_visible, fnct_search=_is_visible_search, type='boolean', string='Visibile'),

        # Visibilità dei protocolli nella dashboard
        'non_classificati_visibility': fields.function(_non_classificati_visibility,
                                                         fnct_search=_non_classificati_visibility_search,
                                                         type='boolean', string='Non Classificati'),
        'non_fascicolati_visibility': fields.function(_non_fascicolati_visibility,
                                                         fnct_search=_non_fascicolati_visibility_search,
                                                         type='boolean', string='Non Fascicolati'),
        'bozza_creato_da_me_visibility': fields.function(_bozza_creato_da_me_visibility,
                                                         fnct_search=_bozza_creato_da_me_visibility_search,
                                                         type='boolean', string='Bozza Creata da me'),
        'assegnato_a_me_visibility': fields.function(_assegnato_a_me_visibility,
                                                     fnct_search=_assegnato_a_me_visibility_search, type='boolean',
                                                     string='Assegnato a me'),
        'assegnato_a_me_comp_visibility': fields.function(_assegnato_a_me_comp_visibility,
                                                          fnct_search=_assegnato_a_me_comp_visibility_search, type='boolean',
                                                          string='Assegnato a me per Competenza'),
        'assegnato_a_me_cc_visibility': fields.function(_assegnato_a_me_cc_visibility,
                                                        fnct_search=_assegnato_a_me_cc_visibility_search,
                                                        type='boolean', string='Assegnato a me per CC'),
        'assegnato_a_mio_ufficio_visibility': fields.function(_assegnato_a_mio_ufficio_visibility,
                                                              fnct_search=_assegnato_a_mio_ufficio_visibility_search,
                                                              type='boolean', string='Assegnato al mio Ufficio'),
        'assegnato_a_mio_ufficio_comp_visibility': fields.function(_assegnato_a_mio_ufficio_comp_visibility,
                                                                   fnct_search=_assegnato_a_mio_ufficio_comp_visibility_search,
                                                                   type='boolean', string='Assegnato al mio Ufficio per Competenza'),
        'assegnato_a_mio_ufficio_cc_visibility': fields.function(_assegnato_a_mio_ufficio_cc_visibility,
                                                                 fnct_search=_assegnato_a_mio_ufficio_cc_visibility_search,
                                                                 type='boolean', string='Assegnato al mio Ufficio per Conoscenza'),
        'assegnato_cc_visibility': fields.function(_assegnato_cc_visibility,
                                                   fnct_search=_assegnato_cc_visibility_search, type='boolean',
                                                   string='Assegnato per CC'),
        'da_assegnare_visibility': fields.function(_da_assegnare_visibility,
                                                                fnct_search=_da_assegnare_visibility_search,
                                                                type='boolean', string='Da Assegnare'),
        'da_assegnare_general_visibility': fields.function(_da_assegnare_general_visibility,
                                                                fnct_search=_da_assegnare_general_visibility_search,
                                                                type='boolean', string='Da Assegnare'),
        'assegnato_da_me_in_attesa_visibility': fields.function(_assegnato_da_me_in_attesa_visibility,
                                                                fnct_search=_assegnato_da_me_in_attesa_visibility_search,
                                                                type='boolean', string='In Attesa'),
        'assegnato_da_me_in_rifiutato_visibility': fields.function(_assegnato_da_me_in_rifiutato_visibility,
                                                                   fnct_search=_assegnato_da_me_in_rifiutato_visibility_search,
                                                                   type='boolean', string='Rifiutato'),
        'da_inviare_visibility': fields.function(_da_inviare_visibility,
                                                                fnct_search=_da_inviare_visibility_search,
                                                                type='boolean', string='Da Inviare'),

        'filtro_assegnazione_competenza_dipendente_ids': fields.function(_get_assegnazione_competenza_dipendente_ids,
                                                          fnct_search=_search_assegnazione_competenza_dipendente_ids,
                                                          method=True,
                                                          type='one2many',
                                                          relation='protocollo.assegnazione',
                                                          string='Assegnatario Dipendente Competenza'),
        'filtro_assegnazione_competenza_ufficio_ids': fields.function(_get_assegnazione_competenza_ufficio_ids,
                                                         fnct_search=_search_assegnazione_competenza_ufficio_ids,
                                                         method=True,
                                                         type='one2many',
                                                         relation='protocollo.assegnazione',
                                                         string='Assegnatario Ufficio Competenza'),
        'filtro_assegnazione_conoscenza_dipendente_ids': fields.function(_get_assegnazione_conoscenza_dipendente_ids,
                                                         fnct_search=_search_assegnazione_conoscenza_dipendente_ids,
                                                         method=True,
                                                         type='one2many',
                                                         relation='protocollo.assegnazione',
                                                         string='Assegnatario Dipendente Conoscenza'),
        'filtro_assegnazione_conoscenza_ufficio_ids': fields.function(_get_assegnazione_conoscenza_ufficio_ids,
                                                          fnct_search=_search_assegnazione_conoscenza_ufficio_ids,
                                                          method=True,
                                                          type='one2many',
                                                          relation='protocollo.assegnazione',
                                                          string='Assegnatario Ufficio Conoscenza'),

        'filtro_a_me_competenza_visibility': fields.function(_filtro_a_me_competenza_visibility,
                                                             fnct_search=_filtro_a_me_competenza_visibility_search,
                                                             type='boolean', string='Assegnato a me per Competenza'),
        'filtro_a_me_conoscenza_visibility': fields.function(_filtro_a_me_conoscenza_visibility,
                                                             fnct_search=_filtro_a_me_conoscenza_visibility_search,
                                                             type='boolean', string='Assegnato a me per CC'),
        'filtro_a_mio_ufficio_visibility': fields.function(_filtro_a_mio_ufficio_visibility,
                                                           fnct_search=_filtro_a_mio_ufficio_visibility_search,
                                                           type='boolean', string='Assegnato al mio Ufficio per CC'),
        'filtro_a_mio_ufficio_cc_visibility': fields.function(_filtro_a_mio_ufficio_cc_visibility,
                                                              fnct_search=_filtro_a_mio_ufficio_cc_visibility_search,
                                                              type='boolean', string='Assegnato al mio Ufficio per Conoscenza'),
        'filtro_da_me_visibility': fields.function(_filtro_da_me_visibility,
                                                   fnct_search=_filtro_da_me_visibility_search, type='boolean',
                                                   string='Assegnato da me'),
        'filtro_competenza_visibility': fields.function(_filtro_competenza_visibility,
                                                        fnct_search=_filtro_competenza_visibility_search,
                                                        type='boolean', string='Assegnato da me per Competenza'),
        'filtro_conoscenza_visibility': fields.function(_filtro_conoscenza_visibility,
                                                        fnct_search=_filtro_conoscenza_visibility_search,
                                                        type='boolean', string='Assegnato da me per Conoscenza'),
        'filtro_da_me_in_attesa_visibility': fields.function(_filtro_da_me_in_attesa_visibility,
                                                             fnct_search=_filtro_da_me_in_attesa_visibility_search,
                                                             type='boolean', string='Assegnato da me in attesa'),

        # Visibilità dei button sui protocolli
        'registra_visibility': fields.function(_registra_visibility, type='boolean', string='Registra'),
        'elimina_visibility': fields.function(_elimina_visibility, type='boolean', string='Elimina'),
        'annulla_visibility': fields.function(_annulla_visibility, type='boolean', string='Annulla'),
        'prendi_in_carico_visibility': fields.function(_prendi_in_carico_visibility, type='boolean',
                                                       string='Prendi in Carico'),
        'rifiuta_visibility': fields.function(_rifiuta_visibility, type='boolean', string='Rifiuta'),
        'segna_come_letto_visibility': fields.function(_segna_come_letto_visibility, type='boolean', string='Segna come letto'),
        'modifica_dati_generali_visibility': fields.function(_modifica_dati_generali_visibility, type='boolean',
                                                             string='Modifica Dati Generali'),
        'aggiungi_mittenti_visibility': fields.function(_aggiungi_mittenti_visibility, type='boolean', string='Aggiungi Mittenti'),
        'modifica_mittenti_visibility': fields.function(_modifica_mittenti_visibility, type='boolean', string='Modifica Mittenti'),
        'aggiungi_destinatari_visibility': fields.function(_aggiungi_destinatari_visibility, type='boolean', string='Aggiungi Destinatari'),
        'modifica_destinatari_visibility': fields.function(_modifica_destinatari_visibility, type='boolean', string='Modifica Destinatari'),
        'aggiungi_mittente_interno_visibility': fields.function(_aggiungi_mittente_interno_visibility, type='boolean', string='Aggiungi Mittente Interno'),
        'modifica_mittente_interno_visibility': fields.function(_modifica_mittente_interno_visibility, type='boolean', string='Modifica Mittente Interno'),
        'aggiungi_classificazione_visibility': fields.function(_aggiungi_classificazione_visibility, type='boolean', string='Aggiungi Classificazione'),
        'modifica_classificazione_visibility': fields.function(_modifica_classificazione_visibility, type='boolean', string='Modifica Classificazione'),
        'classifica_visibility': fields.function(_classifica_visibility, type='boolean', string='Classifica'),
        'aggiungi_fascicolazione_visibility': fields.function(_aggiungi_fascicolazione_visibility, type='boolean', string='Aggiungi Fascicolazione'),
        'modifica_fascicolazione_visibility': fields.function(_modifica_fascicolazione_visibility, type='boolean', string='Modifica Fascicolazione'),
        'fascicola_visibility': fields.function(_fascicola_visibility, type='boolean', string='Fascicola'),
        'aggiungi_assegnatari_visibility': fields.function(_aggiungi_assegnatari_visibility, type='boolean', string='Aggiungi Assegnatari'),
        'modifica_assegnatari_visibility': fields.function(_modifica_assegnatari_visibility, type='boolean', string='Modifica Assegnatari'),
        'aggiungi_assegnatari_cc_visibility': fields.function(_aggiungi_assegnatari_cc_visibility, type='boolean',
                                                              string='Aggiungi Assegnatari Conoscenza'),
        'assegna_visibility': fields.function(_assegna_visibility, type='boolean', string='Assegna'),
        'riassegna_visibility': fields.function(_riassegna_visibility, type='boolean', string='Riassegna per Rifiuto'),
        'invio_pec_visibility': fields.function(_invio_pec_visibility, type='boolean', string='Invio PEC'),
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
        'inserisci_testo_mailpec_visibility': fields.function(_inserisci_testo_mailpec_visibility, type='boolean',
                                                              string='Abilita testo PEC'),
        'carica_documento_visibility': fields.function(_carica_documento_visibility, type='boolean', string='Carica documento'),
        'modifica_documento_visibility': fields.function(_modifica_documento_visibility, type='boolean', string='Modifica documento'),
        'carica_allegati_visibility': fields.function(_carica_allegati_visibility, type='boolean', string='Carica Allegati'),
        'modifica_allegati_visibility': fields.function(_modifica_allegati_visibility, type='boolean', string='Modifica Allegati'),
        'protocollo_fields_editability': fields.function(_protocollo_fields_editability, type='boolean', string='Modificabilità Campi Protocollo'),
        'typology_editability': fields.function(_typology_editability, type='boolean', string='Modificabilità Campi Mezzo di Trasmissione'),
    }

    def _default_protocollazione_riservata_visibility(self, cr, uid, context):
        return self.user_has_groups(cr, uid, 'seedoo_protocollo.group_protocollazione_riservata')

    _defaults = {
        'protocollazione_riservata_visibility': _default_protocollazione_riservata_visibility,
        'carica_documento_visibility': True,
        'modifica_documento_visibility': True
    }

    def delete_indexes(self, cr):
        cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = \'idx_protocollo_protocollo_registration_date\'')
        if cr.fetchone():
            cr.execute('DROP INDEX idx_protocollo_protocollo_registration_date')

        cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = \'idx_protocollo_protocollo_registration_employee_id\'')
        if cr.fetchone():
            cr.execute('DROP INDEX idx_protocollo_protocollo_registration_employee_id')

        cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = \'idx_protocollo_protocollo_registration_employee_department_id\'')
        if cr.fetchone():
            cr.execute('DROP INDEX idx_protocollo_protocollo_registration_employee_department_id')

        cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = \'idx_protocollo_protocollo_archivio_id\'')
        if cr.fetchone():
            cr.execute('DROP INDEX idx_protocollo_protocollo_archivio_id')

    def create_indexes(self, cr):
        cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = \'idx_protocollo_protocollo_registration_date\'')
        if not cr.fetchone():
            cr.execute("""
                CREATE INDEX idx_protocollo_protocollo_registration_date
                ON public.protocollo_protocollo
                USING btree
                (registration_date);
            """)
        cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = \'idx_protocollo_protocollo_registration_employee_id\'')
        if not cr.fetchone():
            cr.execute("""
                CREATE INDEX idx_protocollo_protocollo_registration_employee_id
                ON public.protocollo_protocollo
                USING btree
                (registration_employee_id);
            """)
        cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = \'idx_protocollo_protocollo_registration_employee_department_id\'')
        if not cr.fetchone():
            cr.execute("""
                CREATE INDEX idx_protocollo_protocollo_registration_employee_department_id
                ON public.protocollo_protocollo
                USING btree
                (registration_employee_department_id);
            """)
        cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = \'idx_protocollo_protocollo_archivio_id\'')
        if not cr.fetchone():
            cr.execute("""
                CREATE INDEX idx_protocollo_protocollo_archivio_id
                ON public.protocollo_protocollo
                USING btree
                (archivio_id);
            """)

    def init(self, cr):
        self.create_indexes(cr)


    def fields_get(self, cr, uid, fields=None, context=None):
        # lista dei campi da nascondere nella ricerca avanzata
        fields_to_hide = [
            'is_visible',
            'registration_employee_id',
            'doc_fname',
            'assegnazione_first_level_ids',
            'assegnazione_competenza_ids',
            'assegnazione_conoscenza_ids',
            'filtro_assegnazione_competenza_dipendente_ids',
            'filtro_assegnazione_competenza_ufficio_ids',
            'filtro_assegnazione_conoscenza_dipendente_ids',
            'filtro_assegnazione_conoscenza_ufficio_ids',
            'filtro_a_me_conoscenza_visibility',
            'filtro_a_me_competenza_visibility',
            'filtro_a_mio_ufficio_visibility',
            'filtro_a_mio_ufficio_cc_visibility',
            'filtro_da_me_visibility',
            'filtro_competenza_visibility',
            'filtro_conoscenza_visibility',
            'bozza_creato_da_me_visibility',
            'assegnato_a_me_visibility',
            'assegnato_a_me_comp_visibility',
            'assegnato_a_me_cc_visibility',
            'assegnato_a_mio_ufficio_visibility',
            'assegnato_a_mio_ufficio_comp_visibility',
            'assegnato_a_mio_ufficio_cc_visibility',
            'assegnato_cc_visibility',
            'assegnato_da_me_in_attesa_visibility',
            'assegnato_da_me_in_rifiutato_visibility',
        ]
        res = super(protocollo_protocollo, self).fields_get(cr, uid, fields, context)
        for field in fields_to_hide:
            if field in res:
                res[field]['selectable'] = False
        return res