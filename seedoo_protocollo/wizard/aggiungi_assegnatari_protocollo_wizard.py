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

    _columns = {
        'reserved': fields.boolean('Riservato', readonly=True),
        'assegnatore_department_id': fields.many2one('hr.department',
                                          'Ufficio dell\'Assegnatore',
                                          domain="[('member_ids.user_id', '=', uid)]",
                                          required=True),
        'assegnatario_competenza_id': fields.many2one('protocollo.assegnatario',
                                                      'Assegnatario per Competenza',
                                                      domain="[('assignable', '=', True)]",
                                                      required=False),
        'assegnatario_conoscenza_ids': fields.many2many('protocollo.assegnatario',
                                                        'protocollo_aggiungi_assegnatari_rel',
                                                        'wizard_id',
                                                        'assegnatario_id',
                                                        'Assegnatari per Conoscenza',
                                                        domain="[('assignable', '=', True)]"),
        'motivation': fields.text('Motivazione'),
        'display_motivation': fields.boolean('Visualizza Motivazione', readonly=True),
        'conoscenza_reserved_error': fields.text('Errore Protocollazione Riservata', readonly=True),
        'assegnatari_empty': fields.boolean('Assegnatari Non Presenti'),
        'assegnatore_department_id_invisible': fields.boolean('Dipartimento Assegnatore Non Visibile', readonly=True),
        'assegnatario_competenza_id_required': fields.boolean('Assegnatario per Competenza Obbligatorio', readonly=True),
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
        return self.pool.get('protocollo.assegnazione').get_default_assegnatore_department_id(cr, uid, context['active_id'])

    def _default_assegnatore_department_id_invisible(self, cr, uid, context):
        department_id = self.pool.get('protocollo.assegnazione').get_default_assegnatore_department_id(cr, uid, context['active_id'])
        if department_id:
            return True
        return False

    def _default_assegnatario_competenza_id(self, cr, uid, context):
        assegnazione_obj = self.pool.get('protocollo.assegnazione')
        assegnazione_ids = assegnazione_obj.search(cr, uid, [
            ('protocollo_id', '=', context['active_id']),
            ('tipologia_assegnazione', '=', 'competenza'),
            ('parent_id', '=', False)
        ])
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

    def _default_display_motivation(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'], {'skip_check': True})
        if protocollo.registration_employee_id:
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
        if not protocollo or protocollo.state == 'draft':
            return False
        else:
            return True

    _defaults = {
        'reserved': _default_reserved,
        'conoscenza_reserved_error': _default_conoscenza_reserved_error,
        'assegnatore_department_id': _default_assegnatore_department_id,
        'assegnatario_competenza_id': _default_assegnatario_competenza_id,
        'assegnatario_conoscenza_ids': _default_assegnatario_conoscenza_ids,
        'display_motivation': _default_display_motivation,
        'assegnatari_empty': _default_assegnatari_empty,
        'assegnatore_department_id_invisible': _default_assegnatore_department_id_invisible,
        'assegnatario_competenza_id_required': _default_assegnatario_competenza_id_required
    }

    def action_save(self, cr, uid, ids, context=None):
        before = {'competenza': '', 'conoscenza': ''}
        after = {'competenza': '', 'conoscenza': ''}
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'], {'skip_check': True})
        save_history = protocollo.state != 'draft'
        wizard = self.browse(cr, uid, ids[0], context)
        employee_ids = self.pool.get('hr.employee').search(cr, uid, [
            ('department_id', '=', wizard.assegnatore_department_id.id),
            ('user_id', '=', uid)
        ])

        if 'assegnatari_initial_state' in context:
            check_assegnatari = []
            for item in context['assegnatari_initial_state']:
                check_assegnatari.append(item[1])
            if check_assegnatari != protocollo.assegnazione_first_level_ids.ids:
                raise openerp.exceptions.Warning(_(
                    'Non è più possibile eseguire l\'operazione richiesta! Il protocollo è già stato assegnato da un altro utente!'))

        # assegnazione per competenza
        if save_history:
            before['competenza'] = ', '.join([a.assegnatario_id.nome for a in protocollo.assegnazione_competenza_ids])
        self.pool.get('protocollo.assegnazione').salva_assegnazione_competenza(
            cr,
            uid,
            context.get('active_id', False),
            wizard.assegnatario_competenza_id.id if wizard.assegnatario_competenza_id else False,
            employee_ids[0] if employee_ids else False
        )
        if save_history:
            after['competenza'] = wizard.assegnatario_competenza_id.nome


        # assegnazione per conoscenza
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
            context.get('active_id', False),
            assegnatario_conoscenza_to_save_ids,
            employee_ids[0] if employee_ids else False
        )
        if save_history:
            after['conoscenza'] = ', '.join([a.assegnatario_id.nome for a in protocollo.assegnazione_conoscenza_ids])

        #if not protocollo.reserved:
            #self._salva_assegnatari_ufficio
        #self._salva_assegnatari_dipendente

        if save_history:
            action_class = "history_icon update"
            body = "<div class='%s'><ul>" % action_class
            if (before['competenza'] or after['competenza']) and before['competenza']!=after['competenza']:
                body = body + "<li>%s: <span style='color:#990000'> %s</span> -> <span style='color:#009900'> %s </span></li>" \
                              % ('Assegnatario Competenza', before['competenza'], after['competenza'])
            if (before['conoscenza'] or after['conoscenza']) and before['conoscenza']!=after['conoscenza']:
                body = body + "<li>%s: <span style='color:#990000'> %s</span> -> <span style='color:#009900'> %s </span></li>" \
                              % ('Assegnatari Conoscenza', before['conoscenza'], after['conoscenza'])
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

        return {
                'name': 'Protocollo',
                'view_type': 'form',
                'view_mode': 'form,tree',
                'res_model': 'protocollo.protocollo',
                'res_id': context['active_id'],
                'context': context,
                'type': 'ir.actions.act_window'
        }
