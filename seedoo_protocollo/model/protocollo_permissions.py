# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp import SUPERUSER_ID
from openerp import tools
from openerp.osv import orm, fields, osv


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
        employees = self._get_assegnatari_competenza(cr, uid, protocollo)
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
            if child_department.id == registration_department.id or self._is_registered_by_child_departments(cr, uid, child_department, registration_department):
                return True
        return False

    def _is_assigned_to_child_departments(self, cr, uid, department, assigned_department):
        for child_department in department.child_ids:
            if child_department.id == assigned_department.id or self._is_assigned_to_child_departments(cr, uid, child_department, assigned_department):
                return True
        return False

    def _check_visible(self, cr, uid, user_employee, protocollo_id):
        protocollo = self.browse(cr, uid, protocollo_id)
        user = user_employee.user_id
        user_department = user_employee.department_id if user_employee.department_id else None
        registration_employee = protocollo.registration_employee_id if protocollo.registration_employee_id else None
        registration_department = registration_employee.department_id if registration_employee and registration_employee.department_id else None

        ################################################################################################################
        # Visibilità dei protocolli stabilita dai casi base
        ################################################################################################################

        # un utente deve poter vedere i protocolli in bozza (IN e OUT) creati da lui
        if protocollo.state == 'draft' and protocollo.user_id and protocollo.user_id.id == user.id:
            return True

        # un utente deve poter vedere i protocolli (IN e OUT) registrati da lui
        if registration_employee and registration_employee.id == user_employee.id:
            return True

        # un utente deve poter vedere i protocolli (IN e OUT) assegnati a lui
        # purchè lui o un dipendente del suo ufficio non abbia rifiutato la presa in carico
        stato_dipendente_obj = self.pool.get('protocollo.stato.dipendente')

        is_assegnatario = False
        is_protocollo_rifiutato_by_department = False

        employees = self._get_assegnatari_competenza(cr, uid, protocollo)
        for employee in employees:
            if employee.id == user_employee.id:
                is_assegnatario = True

            if employee.department_id and user_department and employee.department_id.id == user_department.id:
                stato_dipendente_ids = stato_dipendente_obj.search(cr, uid, [
                    ('dipendente_id', '=', employee.id),
                    ('protocollo_id', '=', protocollo.id),
                    ('state', '=', 'rifiutato')
                ])
                if len(stato_dipendente_ids) > 0:
                    is_protocollo_rifiutato_by_department = True

        if not is_assegnatario:
            employees = self._get_assegnatari_conoscenza(cr, uid, protocollo)
            for employee in employees:
                if employee.id == user_employee.id:
                    is_assegnatario = True

        if is_assegnatario and not is_protocollo_rifiutato_by_department:
            return True

        ################################################################################################################
        # Visibilità dei protocolli stabilita tramite i permessi in configurazione
        ################################################################################################################

        # un utente deve poter vedere i protocolli (IN e OUT) REGISTRATI dal suo UFFICIO di appartenenza
        check_gruppo = False
        if protocollo.type == 'in':
            check_gruppo = self.user_has_groups(cr, user.id, 'seedoo_protocollo.group_vedi_protocolli_ingresso_registrati_ufficio')
        elif protocollo.type == 'out':
            check_gruppo = self.user_has_groups(cr, user.id, 'seedoo_protocollo.group_vedi_protocolli_uscita_registrati_ufficio')
        if check_gruppo and user_department and registration_department and user_department.id == registration_department.id:
            return True

        # un utente deve poter vedere i protocolli (IN e OUT) REGISTRATI da un UFFICIO FIGLIO del suo ufficio di appartenenza
        check_gruppo = False
        if protocollo.type == 'in':
            check_gruppo = self.user_has_groups(cr, user.id, 'seedoo_protocollo.group_vedi_protocolli_ingresso_registrati_ufficio_figlio')
        elif protocollo.type == 'out':
            check_gruppo = self.user_has_groups(cr, user.id, 'seedoo_protocollo.group_vedi_protocolli_uscita_registrati_ufficio_figlio')
        if check_gruppo and user_department and registration_department and self._is_registered_by_child_departments(cr, uid, user_department, registration_department):
            return True

        # un utente deve poter vedere QUALUNQUE protocollo (IN e OUT) in stato BOZZA appartenente alla sua AOO
        check_gruppo = False
        if protocollo.type == 'in':
            check_gruppo = self.user_has_groups(cr, user.id, 'seedoo_protocollo.group_vedi_protocolli_ingresso_bozza')
        elif protocollo.type == 'out':
            check_gruppo = self.user_has_groups(cr, user.id, 'seedoo_protocollo.group_vedi_protocolli_uscita_bozza')
        if check_gruppo and protocollo.state == 'draft' and protocollo.aoo_id and user_department.aoo_id and protocollo.aoo_id.id == user_department.aoo_id.id:
            return True

        # un utente deve poter vedere QUALUNQUE protocollo (IN e OUT) REGISTRATO da un utente della sua AOO
        check_gruppo = False
        if protocollo.type == 'in':
            check_gruppo = self.user_has_groups(cr, user.id, 'seedoo_protocollo.group_vedi_protocolli_ingresso_registrati')
        elif protocollo.type == 'out':
            check_gruppo = self.user_has_groups(cr, user.id, 'seedoo_protocollo.group_vedi_protocolli_uscita_registrati')
        if check_gruppo and protocollo.aoo_id and registration_department and registration_department.aoo_id and protocollo.aoo_id.id == registration_department.aoo_id.id:
            return True

        # un utente deve poter vedere i protocolli (IN e OUT) REGISTRATI e ASSEGNATI ad un UTENTE del suo UFFICIO di appartenenza
        check_gruppo = False
        if protocollo.type == 'in':
            check_gruppo = self.user_has_groups(cr, user.id, 'seedoo_protocollo.group_vedi_protocolli_ingresso_registrati_assegnati_utente_ufficio')
        elif protocollo.type == 'out':
            check_gruppo = self.user_has_groups(cr, user.id, 'seedoo_protocollo.group_vedi_protocolli_uscita_registrati_assegnati_utente_ufficio')
        if check_gruppo and registration_employee and user_department:
            for assegnatari_competenza_dipendente in protocollo.assegnatari_competenza_dipendenti_ids:
                employee = assegnatari_competenza_dipendente.dipendente_id
                if employee and employee.department_id and employee.department_id.id == user_department.id:
                    return True
            for assegnatari_conoscenza_dipendente in protocollo.assegnatari_conoscenza_dipendenti_ids:
                employee = assegnatari_conoscenza_dipendente.dipendente_id
                if employee and employee.department_id and employee.department_id.id == user_department.id:
                    return True

        # un utente deve poter vedere i protocolli (IN e OUT) REGISTRATI e ASSEGNATI ad un suo UFFICIO FIGLIO
        check_gruppo = False
        if protocollo.type == 'in':
            check_gruppo = self.user_has_groups(cr, user.id, 'seedoo_protocollo.group_vedi_protocolli_ingresso_registrati_assegnati_ufficio_figlio')
        elif protocollo.type == 'out':
            check_gruppo = self.user_has_groups(cr, user.id, 'seedoo_protocollo.group_vedi_protocolli_uscita_registrati_assegnati_ufficio_figlio')
        if check_gruppo and registration_employee and user_department:
            for assegnatari_competenza_ufficio in protocollo.assegnatari_competenza_uffici_ids:
                department = assegnatari_competenza_ufficio.department_id
                if department and self._is_assigned_to_child_departments(cr, uid, user_department, department):
                    return True
            for assegnatari_conoscenza_ufficio in protocollo.assegnatari_conoscenza_uffici_ids:
                department = assegnatari_conoscenza_ufficio.department_id
                if department and self._is_assigned_to_child_departments(cr, uid, user_department, department):
                    return True

        # un utente deve poter vedere i protocolli (IN e OUT) REGISTRATI e ASSEGNATI ad un UTENTE di un suo UFFICIO FIGLIO
        check_gruppo = False
        if protocollo.type == 'in':
            check_gruppo = self.user_has_groups(cr, user.id, 'seedoo_protocollo.group_vedi_protocolli_ingresso_registrati_assegnati_utente_ufficio_figlio')
        elif protocollo.type == 'out':
            check_gruppo = self.user_has_groups(cr, user.id, 'seedoo_protocollo.group_vedi_protocolli_uscita_registrati_assegnati_utente_ufficio_figlio')
        if check_gruppo and registration_employee and user_department:
            for assegnatari_competenza_dipendente in protocollo.assegnatari_competenza_dipendenti_ids:
                employee = assegnatari_competenza_dipendente.dipendente_id
                if employee and employee.department_id and self._is_assigned_to_child_departments(cr, uid, user_department, employee.department_id):
                    return True
            for assegnatari_conoscenza_dipendente in protocollo.assegnatari_conoscenza_dipendenti_ids:
                employee = assegnatari_conoscenza_dipendente.dipendente_id
                if employee and employee.department_id and self._is_assigned_to_child_departments(cr, uid, user_department, employee.department_id):
                    return True

        return False

    # def clear_cache(self):
    #     self._get_protocollo_visibile_ids.clear_cache(self)

    #@tools.ormcache()
    def _get_protocollo_visibile_ids(self, cr, uid, current_user_id):
        protocollo_visible_ids = []

        employee_obj = self.pool.get('hr.employee')
        employee_ids = employee_obj.search(cr, uid, [('user_id', '=', current_user_id)])
        if len(employee_ids) > 0:
            employee = employee_obj.browse(cr, uid, employee_ids[0])
            protocollo_ids = self.search(cr, uid, [])
            for protocollo_id in protocollo_ids:
                if self._check_visible(cr, uid, employee, protocollo_id):
                    protocollo_visible_ids.append(protocollo_id)

        return protocollo_visible_ids

    def _is_visible(self, cr, uid, ids, name, arg, context=None):
        return {}

    def _is_visible_search(self, cr, uid, obj, name, args, domain=None, context=None):
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

            if protocollo.state == 'registered':
                check = True

            if check:
                check_gruppi = False
                if protocollo.type == 'in':
                    check_gruppi = self.user_has_groups(cr, uid, 'seedoo_protocollo.group_prendi_in_carico_protocollo_ingresso')
                elif protocollo.type == 'out':
                    check_gruppi = self.user_has_groups(cr, uid, 'seedoo_protocollo.group_prendi_in_carico_protocollo_uscita')
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

            if protocollo.state == 'registered':
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

            if protocollo.state == 'registered':
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

            if protocollo.state == 'registered':
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

            if protocollo.state == 'registered':
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


    def _assegna_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False

            if protocollo.state == 'registered':
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

            if protocollo.state in ('waiting', 'sent', 'error') and protocollo.type == 'out' and protocollo.typology.name == 'PEC' and protocollo.sender_receivers:
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
                check_gruppi = self.user_has_groups(cr, uid, 'seedoo_protocollo.group_invia_protocollo_sharedmail_uscita')
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

            if protocollo.type=='out' and protocollo.pec==True and protocollo.state in ['waiting', 'error']:
                check = True

            if check:
                check_gruppi = self.user_has_groups(cr, uid, 'seedoo_protocollo.group_modifica_destinatari_pec_uscita')
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


    _columns = {
        'is_visible': fields.function(_is_visible, fnct_search=_is_visible_search, type='boolean', string='Visibile'),

        'registra_visibility': fields.function(_registra_visibility, type='boolean', string='Registra'),
        'annulla_visibility': fields.function(_annulla_visibility, type='boolean', string='Annulla'),
        'prendi_in_carico_visibility': fields.function(_prendi_in_carico_visibility, type='boolean', string='Prendi in Carico'),
        'rifiuta_visibility': fields.function(_rifiuta_visibility, type='boolean', string='Rifiuta'),
        'modifica_dati_generali_visibility': fields.function(_modifica_dati_generali_visibility, type='boolean', string='Modifica Dati Generali'),
        'classifica_visibility': fields.function(_classifica_visibility, type='boolean', string='Classifica'),
        'fascicola_visibility': fields.function(_fascicola_visibility, type='boolean', string='Fascicola'),
        'assegna_visibility': fields.function(_assegna_visibility, type='boolean', string='Assegna'),
        'invio_pec_visibility': fields.function(_invio_pec_visibility, type='boolean', string='Invio PEC'),
        'reinvio_pec_visibility': fields.function(_reinvio_pec_visibility, type='boolean', string='Invio PEC'),
        'invio_sharedmail_visibility': fields.function(_invio_sharedmail_visibility, type='boolean', string='Invio E-mail'),
        'invio_protocollo_visibility': fields.function(_invio_protocollo_visibility, type='boolean', string='Invio Protocollo'),
        'modifica_pec_visibility': fields.function(_modifica_pec_visibility, type='boolean', string='Modifica PEC'),
        'aggiungi_pec_visibility': fields.function(_aggiungi_pec_visibility, type='boolean', string='Aggiungi PEC'),
        'protocollazione_riservata_visibility': fields.function(_protocollazione_riservata_visibility, type='boolean', string='Protocollazione Riservata'),
    }

    def _default_protocollazione_riservata_visibility(self, cr, uid, context):
        return self.user_has_groups(cr, uid, 'seedoo_protocollo.group_protocollazione_riservata')

    _defaults = {
        'protocollazione_riservata_visibility': _default_protocollazione_riservata_visibility
    }