# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.exceptions
from ..model.util.selection import *


class protocollo_aggiungi_classificazione_step1_wizard(osv.TransientModel):
    _name = 'protocollo.aggiungi.classificazione.step1.wizard'
    _description = 'Aggiungi Classificazione'

    _columns = {
        'classification': fields.many2one('protocollo.classification', 'Titolario di Classificazione', domain="[('is_visible', '=', True)]", required=False),
        'motivation': fields.text('Motivazione'),
        'display_motivation': fields.boolean('Visualizza Motivazione', readonly=True),
        'classification_empty': fields.boolean('Titolario Vuoto'),
        'classification_required': fields.boolean('Titolario Obbligatorio'),
    }

    def _default_classification(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'], {'skip_check': True})
        return protocollo.classification.id

    def _default_display_motivation(self, cr, uid, context):
        protocollo_obj = self.pool.get('protocollo.protocollo')
        protocollo = protocollo_obj.browse(cr, uid, context['active_id'], {'skip_check': True})
        if protocollo.state in protocollo_obj.get_history_state_list(cr, uid) and protocollo.classification:
            return True
        else:
            return False

    def _default_classification_empty(self, cr, uid, context):
        count = self.pool.get('protocollo.classification').search(cr, uid, [], count=True, context=context)
        if count > 0:
            return False
        else:
            return True

    def _default_classification_required(self, cr, uid, context):
        protocollo = None
        if context and 'active_id' in context:
            protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'], {'skip_check': True})
        if not protocollo or not protocollo.registration_date:
            return False
        else:
            return True


    _defaults = {
        'classification': _default_classification,
        'display_motivation': _default_display_motivation,
        'classification_empty': _default_classification_empty,
        'classification_required': _default_classification_required
    }

    def classification_save(self, cr, uid, protocollo, classification, motivation, competenza_history, context):
        before = ''
        after = ''
        protocollo_obj = self.pool.get('protocollo.protocollo')
        save_history = True if protocollo.state in protocollo_obj.get_history_state_list(cr, uid) else False

        if save_history:
            before = protocollo.classification.name if protocollo.classification else ''
        self.pool.get('protocollo.protocollo').write(cr, uid, [context['active_id']], {
            'classification': classification.id if classification else False,
            'classification_name': classification.path_name if classification else False,
        }, {'skip_check': True})
        if save_history:
            after = classification.name if classification else ''

        if save_history:
            operation_label = "Inserimento classificazione" if len(before) == 0 else "Modifica classificazione"

            classification_history = ''
            if (before or after) and before != after:
                classification_history = "<li>%s: <span style='color:#990000'> %s</span> -> <span style='color:#007ea6'> %s </span></li>" \
                              % ('Titolario', before, after)

            if classification_history or motivation or competenza_history:
                action_class = "history_icon update"
                body = "<div class='%s'><ul>" % action_class
                body += classification_history
                body += competenza_history
                body += "</ul></div>"
                post_vars = {
                    'subject': "%s%s" % (operation_label, ": " + motivation if motivation else ""),
                    'body': body,
                    'model': "protocollo.protocollo",
                    'res_id': context['active_id']
                }

                new_context = dict(context).copy()
                new_context.update({'pec_messages': True})
                thread_pool = self.pool.get('protocollo.protocollo')
                thread_pool.message_post(cr, uid, context['active_id'], type="notification", context=new_context,
                                         **post_vars)


    def competenza_save(self, cr, uid, protocollo, assegnatario, context=None):
        before = ''
        after = ''
        history = ''
        protocollo_obj = self.pool.get('protocollo.protocollo')
        save_history = True if protocollo.state in protocollo_obj.get_history_state_list(cr, uid) else False
        employee_ids = self.pool.get('hr.employee').search(cr, uid, [
            ('department_id', '=', protocollo.registration_employee_department_id.id),
            ('user_id', '=', uid)
        ])

        if save_history:
            before = ', '.join([a.assegnatario_id.nome for a in protocollo.assegnazione_competenza_ids])
        self.pool.get('protocollo.assegnazione').salva_assegnazione_competenza(
            cr,
            uid,
            context.get('active_id', False),
            assegnatario.id if assegnatario else False,
            employee_ids[0] if employee_ids else False,
            True
        )
        if save_history:
            after = assegnatario.nome

        if save_history and (before or after) and before!=after:
            history = "<li>%s: <span style='color:#990000'> %s</span> -> <span style='color:#007ea6'> %s </span></li>" \
                          % ('Assegnatario Competenza', before, after)

        return history



    def action_save(self, cr, uid, ids, context=None):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'], {'skip_check': True})
        wizard = self.browse(cr, uid, ids[0], context)
        if protocollo:
            configurazione_ids = self.pool.get('protocollo.configurazione').search(cr, uid, [])
            configurazione = self.pool.get('protocollo.configurazione').browse(cr, uid, configurazione_ids[0])

            if protocollo.registration_date or configurazione.sostituisci_assegnatari:
                if protocollo.registration_date and protocollo.assegnazione_competenza_ids:
                    context['display_replace_message'] = True
                else:
                    context['display_replace_message'] = False

                if protocollo.type=='in' and wizard.classification and wizard.classification.assignee_default_in and wizard.classification.assignee_default_in.is_visible:
                    context['assignee_default_id'] = wizard.classification.assignee_default_in.id
                    context['classification_id'] = wizard.classification.id
                    context['motivation'] = wizard.motivation
                    return {
                        'name': 'Aggiungi Classificazione',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'protocollo.aggiungi.classificazione.step2.wizard',
                        'type': 'ir.actions.act_window',
                        'target': 'new',
                        'context': context
                    }
                elif protocollo.type=='out' and wizard.classification and wizard.classification.assignee_default_out and wizard.classification.assignee_default_out.is_visible:
                    context['assignee_default_id'] = wizard.classification.assignee_default_in.id
                    context['classification_id'] = wizard.classification.id
                    context['motivation'] = wizard.motivation
                    return {
                        'name': 'Aggiungi Classificazione',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'protocollo.aggiungi.classificazione.step2.wizard',
                        'type': 'ir.actions.act_window',
                        'target': 'new',
                        'context': context
                    }

            self.classification_save(cr, uid, protocollo, wizard.classification, wizard.motivation, '', context)

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



class protocollo_aggiungi_classificazione_step2_wizard(osv.TransientModel):
    _name = 'protocollo.aggiungi.classificazione.step2.wizard'
    _description = 'Aggiungi Classificazione'

    _columns = {
        'assignee_default': fields.many2one('protocollo.assegnatario', 'Assegnatario Default'),
        'display_replace_message': fields.boolean('Visualizza Messaggio di Sostituzione', readonly=True),
    }

    def _default_assignee_default(self, cr, uid, context):
        assegnatario = self.pool.get('protocollo.assegnatario').browse(cr, uid, context['assignee_default_id'])
        return assegnatario.id

    def _default_display_replace_message(self, cr, uid, context):
        return context['display_replace_message']

    _defaults = {
        'assignee_default': _default_assignee_default,
        'display_replace_message': _default_display_replace_message,
    }

    def action_yes(self, cr, uid, ids, context=None):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'], {'skip_check': True})
        classification = self.pool.get('protocollo.classification').browse(cr, uid, context['classification_id'])
        assegnatario = self.pool.get('protocollo.assegnatario').browse(cr, uid, context['assignee_default_id'])
        history = self.pool.get('protocollo.aggiungi.classificazione.step1.wizard').competenza_save(
            cr, uid, protocollo, assegnatario, context
        )
        self.pool.get('protocollo.aggiungi.classificazione.step1.wizard').classification_save(
            cr, uid, protocollo, classification, context['motivation'], history, context
        )
        protocollo_action = {
                'name': 'Protocollo',
                'view_type': 'form',
                'view_mode': 'form,tree',
                'res_model': 'protocollo.protocollo',
                'res_id': context['active_id'],
                'context': context,
                'type': 'ir.actions.act_window'
        }
        if context and 'initial_mode' in context and context['initial_mode'] == 'edit':
            protocollo_action['flags'] = {'initial_mode': 'edit'}
        return protocollo_action

    def action_no(self, cr, uid, ids, context=None):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'], {'skip_check': True})
        classification = self.pool.get('protocollo.classification').browse(cr, uid, context['classification_id'])
        self.pool.get('protocollo.aggiungi.classificazione.step1.wizard').classification_save(
            cr, uid, protocollo, classification, context['motivation'], '', context
        )
        protocollo_action = {
                'name': 'Protocollo',
                'view_type': 'form',
                'view_mode': 'form,tree',
                'res_model': 'protocollo.protocollo',
                'res_id': context['active_id'],
                'context': context,
                'type': 'ir.actions.act_window'
        }
        if context and 'initial_mode' in context and context['initial_mode'] == 'edit':
            protocollo_action['flags'] = {'initial_mode': 'edit'}
        return protocollo_action