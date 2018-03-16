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

_logger = logging.getLogger(__name__)


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
            data_obj = self.pool.get('ir.model.data')
            user_obj = self.pool.get('res.users')
            assegnatario_obj = self.pool.get('protocollo.assegnatario')
            employee_obj = self.pool.get('hr.employee')

            boolean_values = [True, False]

            type_values = ['in', 'out']

            typology_ids = self.pool.get('protocollo.typology').search(cr, uid, [])

            operatore_group_in = data_obj.get_object(cr, uid, 'seedoo_protocollo', 'group_crea_protocollo_ingresso')
            operatore_in_ids = user_obj.search(cr, SUPERUSER_ID, [('groups_id', '=', operatore_group_in.id)])
            operatore_in_ids.remove(SUPERUSER_ID)

            operatore_group_out = data_obj.get_object(cr, uid, 'seedoo_protocollo', 'group_crea_protocollo_uscita')
            operatore_out_ids = user_obj.search(cr, SUPERUSER_ID, [('groups_id', '=', operatore_group_out.id)])
            operatore_out_ids.remove(SUPERUSER_ID)

            assegnatario_ids = assegnatario_obj.search(cr, SUPERUSER_ID, [])


            count = 0
            total_count = wizard.count_bozza + wizard.count_registrati + wizard.count_presi_in_carico + wizard.count_rifiutati
            count_bozza = 0
            count_registrati = 0
            count_presi_in_carico = 0
            count_rifiutati = 0
            start_time = time.time()

            while count < total_count:
                _logger.info("%s/%s" % (count, total_count))
                # if count>0:
                #     elapsed = time.time() - start
                #     print 'Tempo impiegato per la generazione del protocollo ' + str(protocollo_id) + ': ' + str(elapsed)
                #
                # start = time.time()

                count = count + 1

                type = type_values[random.randint(0, len(type_values) - 1)]

                vals = {
                    'name': 'Nuovo Protocollo del ' + datetime.datetime.now().strftime(DSDF) + ' (%s)' % count,
                    'type': type,
                    'typology': typology_ids[random.randint(0, len(typology_ids) - 1)],
                    'subject': ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(32)]),
                    'sender_receivers': [(0, 0, {
                        'name': 'Test',
                        'type': 'individual',
                        'source': 'sender' if type == 'in' else 'receiver',
                        'pec_mail': 'test@email.com',
                        'email': 'test@email.com'
                    })]
                }

                if type == 'in':
                    operatore_id = operatore_in_ids[random.randint(0, len(operatore_in_ids) - 1)]
                else:
                    operatore_id = operatore_out_ids[random.randint(0, len(operatore_out_ids) - 1)]

                # il protocollo viene creato dall'operatore_id
                protocollo_id = protocollo_obj.create(cr, operatore_id, vals)

                assegnatore_ids = employee_obj.search(cr, SUPERUSER_ID, [('user_id', '=', operatore_id)])

                assegnatario_competenza_id = assegnatario_ids[random.randint(0, len(assegnatario_ids) - 1)]
                self.pool.get('protocollo.assegnazione').salva_assegnazione_competenza(
                    cr,
                    uid,
                    protocollo_id,
                    assegnatario_competenza_id,
                    assegnatore_ids[0]
                )


                assegnatari_conoscenza = []
                assegnatario_conoscenza_ids = assegnatario_obj.search(cr, SUPERUSER_ID, [
                    '|',
                    '&amp;',
                    ('id', '!=', assegnatario_competenza_id),
                    '|',
                    ('parent_id', '=', False),
                    ('parent_id', '!=', assegnatario_competenza_id),
                    '&amp;',
                    ('parent_id', '=', assegnatario_competenza_id),
                    ('tipologia', '=', 'department')
                ])
                assegnatari_conoscenza_number = random.randint(0, len(assegnatario_conoscenza_ids))
                for i in range(0, assegnatari_conoscenza_number):
                    assegnatario_conoscenza_id = assegnatario_conoscenza_ids[
                        random.randint(0, len(assegnatario_conoscenza_ids) - 1)
                    ]
                    assegnatario_conoscenza_ids.remove(assegnatario_conoscenza_id)
                    assegnatari_conoscenza.append(assegnatario_conoscenza_id)
                self.pool.get('protocollo.assegnazione').salva_assegnazione_conoscenza(
                    cr,
                    uid,
                    protocollo_id,
                    assegnatari_conoscenza,
                    assegnatore_ids[0]
                )


                if count_bozza < wizard.count_bozza:
                    count_bozza = count_bozza + 1
                    continue

                # il protocollo viene registrato dall'operatore_id
                protocollo_obj.action_register_process(cr, operatore_id, [protocollo_id], {})

                if count_registrati < wizard.count_registrati:
                    count_registrati = count_registrati + 1
                    continue

                protocollo = protocollo_obj.browse(cr, operatore_id, protocollo_id)
                assegnatari_competenza_disponibili = protocollo_obj._get_assegnatari_competenza(cr, operatore_id,
                                                                                                protocollo)

                if count_presi_in_carico < wizard.count_presi_in_carico:
                    assegnatari_competenza = []
                    for assegnatari_competenza_disponibile in assegnatari_competenza_disponibili:
                        if protocollo.type == 'in' and self.user_has_groups(cr,
                                                                            assegnatari_competenza_disponibile.user_id.id,
                                                                            'seedoo_protocollo.group_prendi_in_carico_protocollo_ingresso'):
                            assegnatari_competenza.append(assegnatari_competenza_disponibile)
                        if protocollo.type == 'out' and self.user_has_groups(cr,
                                                                             assegnatari_competenza_disponibile.user_id.id,
                                                                             'seedoo_protocollo.group_prendi_in_carico_protocollo_uscita'):
                            assegnatari_competenza.append(assegnatari_competenza_disponibile)
                    assegnatario = assegnatari_competenza[random.randint(0, len(assegnatari_competenza) - 1)]
                    # il protocollo viene preso in carico dall'assegnatario_id
                    protocollo_obj.prendi_in_carico(cr, assegnatario.user_id.id, [protocollo_id])

                    count_presi_in_carico = count_presi_in_carico + 1
                    continue

                if count_rifiutati < wizard.count_rifiutati:
                    assegnatari_competenza = []
                    for assegnatari_competenza_disponibile in assegnatari_competenza_disponibili:
                        if protocollo.type == 'in' and self.user_has_groups(cr,
                                                                            assegnatari_competenza_disponibile.user_id.id,
                                                                            'seedoo_protocollo.group_rifiuta_protocollo_ingresso'):
                            assegnatari_competenza.append(assegnatari_competenza_disponibile)
                        if protocollo.type == 'out' and self.user_has_groups(cr,
                                                                             assegnatari_competenza_disponibile.user_id.id,
                                                                             'seedoo_protocollo.group_rifiuta_protocollo_uscita'):
                            assegnatari_competenza.append(assegnatari_competenza_disponibile)
                    assegnatario = assegnatari_competenza[random.randint(0, len(assegnatari_competenza) - 1)]
                    try:
                        # il protocollo viene rifiutato dall'assegnatario_id
                        protocollo_obj.rifiuta_presa_in_carico(cr, assegnatario.user_id.id, [protocollo_id], 'Test')
                    except:
                        print 'errore'
                        # self.pool.get('protocollo.stato.dipendente').modifica_stato_dipendente(cr,
                        #                                                                        assegnatario.user_id.id,
                        #                                                                        [protocollo_id],
                        #                                                                        'rifiutato')

                    count_rifiutati = count_rifiutati + 1
                    continue

        finally:
            rule_obj.write(cr, SUPERUSER_ID, [rule.id], {'active': True})
        _logger.info("--- %s start ---" % start_time)
        _logger.info("--- %s minutes ---" % ((time.time() - start_time)/60))
        return self._close_window()
