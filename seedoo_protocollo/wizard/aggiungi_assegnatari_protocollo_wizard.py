# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.exceptions
from ..model.util.selection import *


class protocollo_aggiungi_assegnatari_wizard(osv.TransientModel):
    _name = 'protocollo.aggiungi.assegnatari.wizard'
    _description = 'Aggiungi Assegnatari'

    def _get_assegnatore_call_by_modifica_assegnatari(self, cr, uid, protocollo):
        assegnatore = False
        # if protocollo.assegnazione_competenza_ids:
        #     assegnatore = protocollo.assegnazione_competenza_ids[0].assegnatore_id
        # elif protocollo.assegnazione_conoscenza_ids:
        #     assegnatore = protocollo.assegnazione_conoscenza_ids[0].assegnatore_id
        employee_obj = self.pool.get('hr.employee')
        employee_ids = employee_obj.search(cr, uid, [('user_id', '=', uid)])
        employee_count = len(employee_ids)
        if employee_count == 1:
            employee = employee_obj.browse(cr, uid, employee_ids[0])
            return employee
        return False


    _columns = {
        'reserved': fields.boolean('Riservato', readonly=True),
        'assegnatore_department_id': fields.many2one('hr.department',
                                          'Ufficio dell\'Assegnatore',
                                          domain="[('member_ids.user_id', '=', uid)]",
                                          required=True),
        'assegnatario_competenza_id': fields.many2one('protocollo.assegnatario',
                                                      'Assegnatario per Competenza',
                                                      domain="[('is_visible', '=', True)]",
                                                      required=False),
        'assegnatario_conoscenza_ids': fields.many2many('protocollo.assegnatario',
                                                        'protocollo_aggiungi_assegnatari_rel',
                                                        'wizard_id',
                                                        'assegnatario_id',
                                                        'Assegnatari per Conoscenza',
                                                        domain="[('is_visible', '=', True)]"),
        'assegnatario_conoscenza_disable_ids': fields.many2many('protocollo.assegnatario',
                                                                'protocollo_aggiungi_assegnatari_disable_rel',
                                                                'wizard_id',
                                                                'assegnatario_id',
                                                                'Assegnatari Conoscenza Disabilitati',
                                                                domain="[('is_visible', '=', True)]"),
        'motivation': fields.text('Motivazione'),
        'display_motivation': fields.boolean('Visualizza Motivazione', readonly=True),
        'conoscenza_reserved_error': fields.text('Errore Protocollazione Riservata', readonly=True),
        'assegnatari_empty': fields.boolean('Assegnatari Non Presenti'),
        'assegnatore_department_id_invisible': fields.boolean('Dipartimento Assegnatore Non Visibile', readonly=True),
        'assegnatario_competenza_id_required': fields.boolean('Assegnatario per Competenza Obbligatorio', readonly=True),
        'assegnatari_change': fields.boolean('Assegnatari Modificati'),
        'prima_assegnazione': fields.boolean('Prima Assegnazione'),
    }

    def _default_reserved(self, cr, uid, context):
        protocollo_obj = self.pool.get('protocollo.protocollo')
        protocollo = protocollo_obj.browse(cr, uid, context['active_id'], {'skip_check': True})
        if protocollo:
            return protocollo.reserved
        return False

    def _default_conoscenza_reserved_error(self, cr, uid, context):
        return '''
I protocollo riservati non possono avere assegnatari per conoscenza.
Se sono presenti assegnatari per conoscenza verranno rimossi al completamento della procedura.
'''

    def _default_assegnatore_department_id(self, cr, uid, context):
        assegnatore_department_id = False
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'], {'skip_check': True})
        if context and 'call_by_modifica_assegnatari' in context and protocollo.registration_date:
            assegnatore = self._get_assegnatore_call_by_modifica_assegnatari(cr, uid, protocollo)
            if assegnatore:
                assegnatore_department_id = assegnatore.department_id.id
        else:
            assegnatore_department_id = self.pool.get('protocollo.assegnazione').get_default_assegnatore_department_id(cr, uid, context['active_id'])
        return assegnatore_department_id

    def _default_assegnatore_department_id_invisible(self, cr, uid, context):
        department_id = self._default_assegnatore_department_id(cr, uid, context)
        if department_id:
            return True
        return False

    def _default_assegnatario_competenza_id(self, cr, uid, context):
        assegnazione_obj = self.pool.get('protocollo.assegnazione')
        assegnazione_ids = assegnazione_obj.search(cr, uid, [
            ('protocollo_id', '=', context['active_id']),
            ('tipologia_assegnazione', '=', 'competenza'),
            ('parent_id', '=', False)
        ], order='create_date')
        if assegnazione_ids:
            assegnazione = assegnazione_obj.browse(cr, uid, assegnazione_ids[0])
            return assegnazione.assegnatario_id.id
        return False

    def _default_assegnatario_conoscenza_ids(self, cr, uid, context):
        assegnazione_obj = self.pool.get('protocollo.assegnazione')
        assegnazione_ids = assegnazione_obj.search(cr, uid, [
            ('protocollo_id', '=', context['active_id']),
            ('tipologia_assegnazione', '=', 'conoscenza'),
            ('parent_id', '=', False)
        ])
        if assegnazione_ids:
            assegnatario_ids = []
            assegnazione_ids = assegnazione_obj.browse(cr, uid, assegnazione_ids)
            for assegnazione in assegnazione_ids:
                assegnatario_ids.append(assegnazione.assegnatario_id.id)
            return assegnatario_ids
        return False

    def _default_assegnatario_conoscenza_disable_ids(self, cr, uid, context):
        protocollo_obj = self.pool.get('protocollo.protocollo')
        protocollo = protocollo_obj.browse(cr, uid, context['active_id'], {'skip_check': True})
        assegnatario_conoscenza_disable_ids = []
        # se il protocollo è stato già registrato e l'utente che sta aggiungendo gli assegnatari non ha il permesso di
        # modifica, allora le vecchie assegnazioni per conoscenza non devono essere modificabili.
        if protocollo.registration_date and not protocollo.modifica_assegnatari_visibility:
            assegnazione_obj = self.pool.get('protocollo.assegnazione')
            assegnazione_conoscenza_domain = [
                ('protocollo_id', '=', context['active_id']),
                ('tipologia_assegnazione', '=', 'conoscenza')
            ]
            assegnazione_conoscenza_ids = assegnazione_obj.search(cr, uid, assegnazione_conoscenza_domain)
            if assegnazione_conoscenza_ids:
                assegnazione_conoscenza_list = assegnazione_obj.browse(cr, uid, assegnazione_conoscenza_ids)
                for assegnazione in assegnazione_conoscenza_list:
                    assegnatario_conoscenza_disable_ids.append(assegnazione.assegnatario_id.id)
                    # se l'assegnazione per conoscenza è di tipo employee allora anche l'ufficio di appartenenza non
                    # deve essere selezionabile, mentre gli altri appartenenti all'ufficio possono esserlo
                    if assegnazione.tipologia_assegnatario == 'employee' and assegnazione.assegnatario_id.parent_id:
                        assegnatario_conoscenza_disable_ids.append(assegnazione.assegnatario_id.parent_id.id)
        return assegnatario_conoscenza_disable_ids

    def _default_display_motivation(self, cr, uid, context):
        protocollo_obj = self.pool.get('protocollo.protocollo')
        protocollo = protocollo_obj.browse(cr, uid, context['active_id'], {'skip_check': True})
        if protocollo.state in protocollo_obj.get_history_state_list(cr, uid) and protocollo.assegnazione_competenza_ids:
            return True
        else:
            return False

    def _default_assegnatari_empty(self, cr, uid, context):
        count = self.pool.get('protocollo.assegnatario').search(cr, uid, [], count=True, context=context)
        if count > 0:
            return False
        else:
            return True

    def _default_assegnatario_competenza_id_required(self, cr, uid, context):
        protocollo = None
        if context and 'active_id' in context:
            protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'], {'skip_check': True})
        # l'assegnatario per competenza è obbligatorio solo se il protocollo è stato registrato e chi sta facendo
        # l'assegnazione viene fatta da un utente che ha il permesso di modifica assegnatari
        if not protocollo or not protocollo.registration_date or (context and 'call_by_modifica_assegnatari' in context):
            return False
        else:
            return True

    def _default_prima_assegnazione(self, cr, uid, context={}):
        if not context.get('active_id', False):
            return False
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'], {'skip_check': True})
        # se il protocollo non è registrato è sicuramente la prima assegnazione
        if not protocollo.registration_date:
            return True
        # se il protocollo è registrato ma non ha assegnazioni per competenza e la procedura non è stata chiamata da un
        # utente che ha il permesso di modifica assegnatari, allora è una prima assegnazione
        if not protocollo.assegnazione_competenza_ids and not context.get('call_by_modifica_assegnatari', False):
            return True
        # se nessuno dei precedenti casi è verificato allora è un'assegnazione successiva alla prima
        return False

    _defaults = {
        'reserved': _default_reserved,
        'conoscenza_reserved_error': _default_conoscenza_reserved_error,
        'assegnatore_department_id': _default_assegnatore_department_id,
        'assegnatario_competenza_id': _default_assegnatario_competenza_id,
        'assegnatario_conoscenza_ids': _default_assegnatario_conoscenza_ids,
        'assegnatario_conoscenza_disable_ids': _default_assegnatario_conoscenza_disable_ids,
        'display_motivation': _default_display_motivation,
        'assegnatari_empty': _default_assegnatari_empty,
        'assegnatore_department_id_invisible': _default_assegnatore_department_id_invisible,
        'assegnatario_competenza_id_required': _default_assegnatario_competenza_id_required,
        'assegnatari_change': False,
        'prima_assegnazione': _default_prima_assegnazione,
    }

    def on_change_assegnatario_competenza_id(self, cr, uid, ids, assegnatario_competenza_id, context=None):
        # si controlla se la chiave 'reserved' è all'interno del context in modo da distinguere quando il metodo
        # on_change viene chiamato dal default oppure dall'interfaccia tramite il click dell'utente
        if context and 'reserved' in context:
            return {'value': {'assegnatari_change': True}}
        return {}

    def on_change_assegnatario_conoscenza_ids(self, cr, uid, ids, assegnatario_conoscenza_ids, context=None):
        # si controlla se la chiave 'reserved' è all'interno del context in modo da distinguere quando il metodo
        # on_change viene chiamato dal default oppure dall'interfaccia tramite il click dell'utente
        if context and 'reserved' in context:
            return {'value': {'assegnatari_change': True}}
        return {}

    def salva_assegnazione_competenza(self, cr, uid, protocollo, wizard, assegnatore_id, save_history, before, after):
        old_assegnatario_id = self._default_assegnatario_competenza_id(cr, uid, {'active_id': protocollo.id})
        new_assegnatario_id = wizard.assegnatario_competenza_id.id if wizard.assegnatario_competenza_id else False
        # Se il protocollo è registrato e il nuovo assegnatario coincide con il vecchio, allora gli assegnatari per
        # competenza non devono essere modificati. In pratica un utente con il permesso di modifica assegnatari, sta
        # salvando l'assegnazione senza però cambiarla. Solamente se il nuovo assegnatario è diverso dal vecchio, si
        # devono eliminare tutti i vecchi assegnatari, compresi quelli inseriti tramite lo smistamento
        if protocollo.registration_date and old_assegnatario_id and new_assegnatario_id and old_assegnatario_id==new_assegnatario_id:
            return

        if save_history:
            before['competenza'] = ', '.join([a.assegnatario_id.nome for a in protocollo.assegnazione_competenza_ids])
        self.pool.get('protocollo.assegnazione').salva_assegnazione_competenza(
            cr,
            uid,
            protocollo.id,
            [new_assegnatario_id] if new_assegnatario_id else [],
            assegnatore_id
        )
        if save_history:
            after['competenza'] = wizard.assegnatario_competenza_id.nome if wizard.assegnatario_competenza_id else ''

    def salva_assegnazione_conoscenza(self, cr, uid, protocollo, wizard, assegnatore_id, save_history, before, after):
        if save_history:
            before['conoscenza'] = ', '.join([a.assegnatario_id.nome for a in protocollo.assegnazione_conoscenza_ids])
        assegnatario_conoscenza_to_save_ids = []
        if not protocollo.reserved:
            assegnatario_conoscenza_ids = wizard.assegnatario_conoscenza_ids.ids
            for assegnatario in wizard.assegnatario_conoscenza_ids:
                if assegnatario.tipologia=='department' or (assegnatario.parent_id and assegnatario.parent_id.id not in assegnatario_conoscenza_ids):
                    assegnatario_conoscenza_to_save_ids.append(assegnatario.id)
        self.pool.get('protocollo.assegnazione').salva_assegnazione_conoscenza(
            cr,
            uid,
            protocollo.id,
            assegnatario_conoscenza_to_save_ids,
            assegnatore_id
        )
        if save_history:
            after['conoscenza'] = ', '.join([a.assegnatario_id.nome for a in protocollo.assegnazione_conoscenza_ids])

    def action_save(self, cr, uid, ids, context=None):
        before = {'competenza': '', 'conoscenza': ''}
        after = {'competenza': '', 'conoscenza': ''}
        protocollo_obj = self.pool.get('protocollo.protocollo')
        protocollo = protocollo_obj.browse(cr, uid, context['active_id'], {'skip_check': True})
        save_history = True if protocollo.state in protocollo_obj.get_history_state_list(cr, uid) else False
        wizard = self.browse(cr, uid, ids[0], context)

        assegnatore_id = False
        if context and 'call_by_modifica_assegnatari' in context and protocollo.registration_date:
            assegnatore = self._get_assegnatore_call_by_modifica_assegnatari(cr, uid, protocollo)
            if assegnatore:
                assegnatore_id = assegnatore.id
        if not assegnatore_id:
            employee_ids = self.pool.get('hr.employee').search(cr, uid, [
                ('department_id', '=', wizard.assegnatore_department_id.id),
                ('user_id', '=', uid)
            ])
            assegnatore_id = employee_ids[0] if employee_ids else False

        if 'assegnatari_initial_state' in context:
            check_assegnatari = []
            for item in context['assegnatari_initial_state']:
                check_assegnatari.append(item[1])
            if check_assegnatari != protocollo.assegnazione_first_level_ids.ids:
                raise openerp.exceptions.Warning(_(
                    'Non è più possibile eseguire l\'operazione richiesta! Il protocollo è già stato assegnato da un altro utente!'))

        # assegnazione per competenza
        self.salva_assegnazione_competenza(cr, uid, protocollo, wizard, assegnatore_id, save_history, before, after)

        # assegnazione per conoscenza
        self.salva_assegnazione_conoscenza(cr, uid, protocollo, wizard, assegnatore_id, save_history, before, after)

        if save_history:
            action_class = "history_icon update"
            body = "<div class='%s'><ul>" % action_class
            data_modified = False
            if (before['competenza'] or after['competenza']) and before['competenza']!=after['competenza']:
                data_modified = True
                body = body + "<li>%s: <span style='color:#990000'> %s</span> -> <span style='color:#007ea6'> %s </span></li>" \
                              % (protocollo_obj.get_label_competenza(cr, uid), before['competenza'], after['competenza'])
            if (before['conoscenza'] or after['conoscenza']) and before['conoscenza']!=after['conoscenza']:
                data_modified = True
                body = body + "<li>%s: <span style='color:#990000'> %s</span> -> <span style='color:#007ea6'> %s </span></li>" \
                              % ('Assegnatari Conoscenza', before['conoscenza'], after['conoscenza'])
            if data_modified:
                history_body_append = context.get('history_body_append', False)
                if history_body_append:
                    body += history_body_append
                body += "</ul></div>"
                subject_label = "Modifica assegnatari" if before['competenza'] or before['conoscenza'] else "Aggiunta assegnatari"
                post_vars = {
                    'subject': "%s%s" % (subject_label, ": " + wizard.motivation if wizard.motivation else ""),
                    'body': body,
                    'model': "protocollo.protocollo",
                    'res_id': context['active_id']
                }
                new_context = dict(context).copy()
                new_context.update({'pec_messages': True})
                thread_pool = self.pool.get('protocollo.protocollo')
                thread_pool.message_post(cr, uid, context['active_id'], type="notification", context=new_context, **post_vars)

        protocollo_action = {
                'name': 'Protocollo',
                'view_type': 'form',
                'view_mode': 'form,tree',
                'res_model': 'protocollo.protocollo',
                'res_id': context['active_id'],
                'context': context,
                'type': 'ir.actions.act_window'
        }
        if context and 'initial_mode' in context and context['initial_mode']=='edit':
            protocollo_action['flags'] = {'initial_mode': 'edit'}
        return protocollo_action
