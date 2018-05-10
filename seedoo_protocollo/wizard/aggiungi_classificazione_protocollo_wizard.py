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
        'classification': fields.many2one('protocollo.classification', 'Titolario di Classificazione', required=True),
        'motivation': fields.text('Motivazione'),
        'display_motivation': fields.boolean('Visualizza Motivazione', readonly=True),
    }

    def _default_classification(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'], {'skip_check': True})
        return protocollo.classification.id

    def _default_display_motivation(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'], {'skip_check': True})
        if protocollo.registration_employee_id:
            return True
        else:
            return False

    _defaults = {
        'classification': _default_classification,
        'display_motivation': _default_display_motivation,
    }

    def classification_save(self, cr, uid, protocollo, classification, motivation, competenza_history, context):
        before = ''
        after = ''
        save_history = protocollo.state != 'draft'

        if save_history:
            before = protocollo.classification.name if protocollo.classification else ''
        self.pool.get('protocollo.protocollo').write(cr, uid, [context['active_id']], {
            'classification': classification.id
        })
        if save_history:
            after = classification.name

        if save_history:
            classification_history = ''
            if (before or after) and before != after:
                classification_history = "<li>%s: <span style='color:#990000'> %s</span> -> <span style='color:#009900'> %s </span></li>" \
                              % ('Titolario', before, after)

            if classification_history or motivation or competenza_history:
                action_class = "history_icon update"
                body = "<div class='%s'><ul>" % action_class
                body += classification_history
                body += competenza_history
                body += "</ul></div>"
                post_vars = {
                    'subject': "Modifica classificazione %s" % (": " + motivation if motivation else ""),
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
        save_history = protocollo.state != 'draft'
        employee_ids = self.pool.get('hr.employee').search(cr, uid, [('user_id', '=', uid)])

        if save_history:
            before = ', '.join([a.assegnatario_id.nome for a in protocollo.assegnazione_competenza_ids])
        self.pool.get('protocollo.assegnazione').salva_assegnazione_competenza(
            cr,
            uid,
            context.get('active_id', False),
            assegnatario.id if assegnatario else False,
            employee_ids[0] if employee_ids else False
        )
        if save_history:
            after = assegnatario.nome

        if save_history and (before or after) and before!=after:
            history = "<li>%s: <span style='color:#990000'> %s</span> -> <span style='color:#009900'> %s </span></li>" \
                          % ('Assegnatario Competenza', before, after)

        return history



    def action_save(self, cr, uid, ids, context=None):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'], {'skip_check': True})
        wizard = self.browse(cr, uid, ids[0], context)
        if protocollo and wizard.classification:
            configurazione_ids = self.pool.get('protocollo.configurazione').search(cr, uid, [])
            configurazione = self.pool.get('protocollo.configurazione').browse(cr, uid, configurazione_ids[0])

            if protocollo.state=='draft' or configurazione.sostituisci_assegnatari:
                if protocollo.state!='draft' and protocollo.assegnazione_competenza_ids:
                    context['display_replace_message'] = True
                else:
                    context['display_replace_message'] = False

                if protocollo.type=='in' and wizard.classification.assignee_default_in:
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
                elif protocollo.type=='out' and wizard.classification.assignee_default_out:
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

        return {
                'name': 'Protocollo',
                'view_type': 'form',
                'view_mode': 'form,tree',
                'res_model': 'protocollo.protocollo',
                'res_id': context['active_id'],
                'context': context,
                'type': 'ir.actions.act_window'
        }



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
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'])
        classification = self.pool.get('protocollo.classification').browse(cr, uid, context['classification_id'])
        assegnatario = self.pool.get('protocollo.assegnatario').browse(cr, uid, context['assignee_default_id'])
        history = self.pool.get('protocollo.aggiungi.classificazione.step1.wizard').competenza_save(
            cr, uid, protocollo, assegnatario, context
        )
        self.pool.get('protocollo.aggiungi.classificazione.step1.wizard').classification_save(
            cr, uid, protocollo, classification, context['motivation'], history, context
        )
        return {
                'name': 'Protocollo',
                'view_type': 'form',
                'view_mode': 'form,tree',
                'res_model': 'protocollo.protocollo',
                'res_id': context['active_id'],
                'context': context,
                'type': 'ir.actions.act_window'
        }

    def action_no(self, cr, uid, ids, context=None):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'])
        classification = self.pool.get('protocollo.classification').browse(cr, uid, context['classification_id'])
        self.pool.get('protocollo.aggiungi.classificazione.step1.wizard').classification_save(
            cr, uid, protocollo, classification, context['motivation'], '', context
        )
        return {
                'name': 'Protocollo',
                'view_type': 'form',
                'view_mode': 'form,tree',
                'res_model': 'protocollo.protocollo',
                'res_id': context['active_id'],
                'context': context,
                'type': 'ir.actions.act_window'
        }