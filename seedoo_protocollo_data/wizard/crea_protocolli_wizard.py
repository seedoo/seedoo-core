# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

import logging
import random
import string
import datetime
import time
from openerp import SUPERUSER_ID, workflow
from openerp.osv import fields, osv
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DSDF


class crea_protocolli_wizard(osv.TransientModel):
    _name = 'crea.protocolli.wizard'
    _description = 'Crea Protocolli di Test'

    _columns = {
        'count_bozza': fields.integer('Numero di protocolli in Bozza', required=True),
        'count_registrati': fields.integer('Numero di protocolli Registrati', required=True),
        'count_presi_in_carico': fields.integer('Numero di protocolli Presi in Carico', required=True),
        'count_rifiutati': fields.integer('Numero di protocolli Rifiutati', required=True),
    }

    _defaults = {
        'count_bozza': 10,
        'count_registrati': 10,
        'count_presi_in_carico': 10,
        'count_rifiutati': 10
    }

    def _close_window(self):
        return {'type': 'ir.actions.act_window_close'}

    def action_create(self, cr, uid, ids, context=None):

        rule_obj = self.pool.get('ir.rule')
        rule = self.pool.get('ir.model.data').get_object(cr, SUPERUSER_ID, 'seedoo_protocollo', 'protocol_access_rule')
        rule_obj.write(cr, SUPERUSER_ID, [rule.id], {'active': False})

        try:

            wizard = self.browse(cr, uid, ids[0], context)
            protocollo_obj = self.pool.get('protocollo.protocollo')

            boolean_values = [True, False]

            type_values = ['in', 'out']

            typology_ids = self.pool.get('protocollo.typology').search(cr, uid, [])

            operatore_group = self.pool.get('ir.model.data').get_object(cr, uid, 'seedoo_protocollo', 'group_protocollo_operatore')
            operatore_ids = self.pool.get('res.users').search(cr, SUPERUSER_ID, [('groups_id', '=', operatore_group.id)])
            operatore_ids.remove(SUPERUSER_ID)

            responsabile_uor_group = self.pool.get('ir.model.data').get_object(cr, uid, 'seedoo_protocollo', 'group_protocollo_responsabile_uor')
            responsabile_uor_ids = self.pool.get('res.users').search(cr, SUPERUSER_ID, [('groups_id', '=', responsabile_uor_group.id)])
            responsabile_uor_ids.remove(SUPERUSER_ID)

            assegnatari_competenza_ids = self.pool.get('hr.employee').search(cr, SUPERUSER_ID, [('user_id', 'in', responsabile_uor_ids)])

            department_ids = self.pool.get('hr.department').search(cr, SUPERUSER_ID, [])

            count = 0
            total_count = wizard.count_bozza + wizard.count_registrati + wizard.count_presi_in_carico + wizard.count_rifiutati
            count_bozza = 0
            count_registrati = 0
            count_presi_in_carico = 0
            count_rifiutati = 0
            while count<total_count:
                # if count>0:
                #     elapsed = time.time() - start
                #     print 'Tempo impiegato per la generazione del protocollo ' + str(protocollo_id) + ': ' + str(elapsed)
                #
                # start = time.time()

                count = count + 1

                type = type_values[random.randint(0, len(type_values)-1)]

                vals = {
                    'name': 'Nuovo Protocollo del ' + datetime.datetime.now().strftime(DSDF) + ' (%s)' % count,
                    'type': type,
                    'typology': typology_ids[random.randint(0, len(typology_ids)-1)],
                    'subject': ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(32)]),
                    'sender_receivers': [(0, 0, {
                        'name': 'Test',
                        'type': 'individual',
                        'source': 'sender' if type=='in' else 'receiver',
                        'pec_mail': 'test@email.com',
                        'email': 'test@email.com'
                    })]
                }

                assegnatari_competenza_ufficio_id = None
                assegnatari_competenza_dipendente_id = None
                if boolean_values[random.randint(0, len(boolean_values)-1)]:
                    assegnatari_competenza_ufficio_id = department_ids[random.randint(0, len(department_ids)-1)]
                    vals['assegnatari_competenza_uffici_ids'] = [(0, 0, {
                        'department_id': assegnatari_competenza_ufficio_id,
                        'tipo': 'competenza',
                    })]
                else:
                    assegnatari_competenza_dipendente_id = assegnatari_competenza_ids[random.randint(0, len(assegnatari_competenza_ids) - 1)]
                    vals['assegnatari_competenza_dipendenti_ids'] = [(0, 0, {
                        'dipendente_id': assegnatari_competenza_dipendente_id,
                        'tipo': 'competenza',
                    })]

                uffici_ids = department_ids[:]
                if assegnatari_competenza_ufficio_id:
                    uffici_ids.remove(assegnatari_competenza_ufficio_id)
                assegnatari_conoscenza_ufficio_id = uffici_ids[random.randint(0, len(uffici_ids)-1)]
                uffici_ids.remove(assegnatari_conoscenza_ufficio_id)
                vals['assegnatari_conoscenza_uffici_ids'] = [(0, 0, {
                    'department_id': assegnatari_conoscenza_ufficio_id,
                    'tipo': 'conoscenza',
                })]

                domain_dipendenti = [('department_id', 'in', uffici_ids)]
                if assegnatari_competenza_dipendente_id:
                    domain_dipendenti.append(('id', '!=', assegnatari_competenza_dipendente_id))
                dipendenti_ids = self.pool.get('hr.employee').search(cr, SUPERUSER_ID, domain_dipendenti)
                vals['assegnatari_conoscenza_dipendenti_ids'] = []
                assegnatari_conoscenza_dipendenti_number = random.randint(0, len(dipendenti_ids))
                for i in range(0, assegnatari_conoscenza_dipendenti_number):
                    assegnatari_conoscenza_dipendente_id = dipendenti_ids[random.randint(0, len(dipendenti_ids)-1)]
                    dipendenti_ids.remove(assegnatari_conoscenza_dipendente_id)
                    vals['assegnatari_conoscenza_dipendenti_ids'].append((0, 0, {
                        'dipendente_id': assegnatari_conoscenza_dipendente_id,
                        'tipo': 'conoscenza',
                    }))

                operatore_id = operatore_ids[random.randint(0, len(operatore_ids) - 1)]
                # il protocollo viene creato dall'operatore_id
                protocollo_id = protocollo_obj.create(cr, operatore_id, vals)

                if count_bozza<wizard.count_bozza:
                    count_bozza = count_bozza + 1
                    continue

                # il protocollo viene registrato dall'operatore_id
                protocollo_obj.action_register_process(cr, operatore_id, [protocollo_id], {})

                if count_registrati<wizard.count_registrati:
                    count_registrati = count_registrati + 1
                    continue

                protocollo = protocollo_obj.browse(cr, operatore_id, protocollo_id)
                assegnatari_competenza_disponibili = protocollo_obj._get_assegnatari_competenza(cr, operatore_id, protocollo)

                if count_presi_in_carico<wizard.count_presi_in_carico:
                    assegnatari_competenza = []
                    for assegnatari_competenza_disponibile in assegnatari_competenza_disponibili:
                        if protocollo.type=='in' and self.user_has_groups(cr, assegnatari_competenza_disponibile.user_id.id, 'seedoo_protocollo.group_prendi_in_carico_protocollo_ingresso'):
                            assegnatari_competenza.append(assegnatari_competenza_disponibile)
                        if protocollo.type=='out' and self.user_has_groups(cr, assegnatari_competenza_disponibile.user_id.id, 'seedoo_protocollo.group_prendi_in_carico_protocollo_uscita'):
                            assegnatari_competenza.append(assegnatari_competenza_disponibile)
                    assegnatario = assegnatari_competenza[random.randint(0, len(assegnatari_competenza) - 1)]
                    # il protocollo viene preso in carico dall'assegnatario_id
                    protocollo_obj.prendi_in_carico(cr, assegnatario.user_id.id, [protocollo_id])

                    count_presi_in_carico = count_presi_in_carico + 1
                    continue

                if count_rifiutati < wizard.count_rifiutati:
                    assegnatari_competenza = []
                    for assegnatari_competenza_disponibile in assegnatari_competenza_disponibili:
                        if protocollo.type == 'in' and self.user_has_groups(cr, assegnatari_competenza_disponibile.user_id.id, 'seedoo_protocollo.group_rifiuta_protocollo_ingresso'):
                            assegnatari_competenza.append(assegnatari_competenza_disponibile)
                        if protocollo.type == 'out' and self.user_has_groups(cr, assegnatari_competenza_disponibile.user_id.id, 'seedoo_protocollo.group_rifiuta_protocollo_uscita'):
                            assegnatari_competenza.append(assegnatari_competenza_disponibile)
                    assegnatario = assegnatari_competenza[random.randint(0, len(assegnatari_competenza) - 1)]
                    try:
                        # il protocollo viene rifiutato dall'assegnatario_id
                        protocollo_obj.rifiuta_presa_in_carico(cr, assegnatario.user_id.id, [protocollo_id])
                    except:
                        self.pool.get('protocollo.stato.dipendente').modifica_stato_dipendente(cr, assegnatario.user_id.id, [protocollo_id], 'rifiutato')

                    count_rifiutati = count_rifiutati + 1
                    continue

        finally:
            rule_obj.write(cr, SUPERUSER_ID, [rule.id], {'active': True})


        return self._close_window()