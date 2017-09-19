# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp import SUPERUSER_ID
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


    def _check_stato_assegnatario_competenza(self, cr, uid, protocollo, stato):
        stato_dipendente_obj = self.pool.get('protocollo.stato.dipendente')
        employees = self._get_assegnatari_competenza(cr, uid, protocollo)
        for employee in employees:
            if employee.user_id and employee.user_id.id == uid:
                stato_dipendente_ids = stato_dipendente_obj.search(cr, uid, [
                    ('dipendente_id', '=', employee.id),
                    ('protocollo_id', '=', protocollo.id),
                ])
                if len(stato_dipendente_ids) > 0:
                    stato_dipendente = stato_dipendente_obj.browse(cr, uid, stato_dipendente_ids[0])
                    if stato_dipendente and stato_dipendente.state == stato:
                        return True
        return False


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

            if protocollo.state in ('waiting', 'sent', 'error') and protocollo.type == 'out' and protocollo.sender_receivers:
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

    def _invio_protocollo_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        res = []

        protocolli = self._get_protocolli(cr, uid, ids)
        for protocollo in protocolli:
            check = False
            if protocollo.state == 'registered' and protocollo.type == 'out' and protocollo.pec is False:
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