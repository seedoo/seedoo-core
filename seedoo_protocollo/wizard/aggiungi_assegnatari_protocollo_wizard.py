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
        'tipologia_assegnatario': fields.selection(TIPO_ASSEGNATARIO_SELECTION, 'Tipologia', readonly=True),

        'assegnatario_competenza_id': fields.many2one('protocollo.assegnatario',
                                                      'Assegnatario per Competenza',
                                                      required=True),

        'assegnatario_conoscenza_ids': fields.many2many('protocollo.assegnatario',
                                                        'protocollo_aggiungi_assegnatari_rel',
                                                        'wizard_id',
                                                        'assegnatario_id',
                                                        'Assegnatari per Conoscenza'),
        'motivation': fields.text('Motivazione'),
        'display_motivation': fields.boolean('Visualizza Motivazione', readonly=True),
    }

    def _default_reserved(self, cr, uid, context):
        protocollo_obj = self.pool.get('protocollo.protocollo')
        protocollo = protocollo_obj.browse(cr, uid, context['active_id'])
        if protocollo:
            return protocollo.reserved
        return False

    def _default_tipologia_assegnatario(self, cr, uid, context):
        protocollo_obj = self.pool.get('protocollo.protocollo')
        protocollo = protocollo_obj.browse(cr, uid, context['active_id'])
        if protocollo and protocollo.reserved:
            return 'department'
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
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'])
        if protocollo.registration_employee_id:
            return True
        else:
            return False

    _defaults = {
        'reserved': _default_reserved,
        'tipologia_assegnatario': _default_tipologia_assegnatario,
        'assegnatario_competenza_id': _default_assegnatario_competenza_id,
        'assegnatario_conoscenza_ids': _default_assegnatario_conoscenza_ids,
        'display_motivation': _default_display_motivation,
    }

    def action_save(self, cr, uid, ids, context=None):
        before = {'competenza': '', 'conoscenza': ''}
        after = {'competenza': '', 'conoscenza': ''}
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'])
        save_history = protocollo.state != 'draft'
        wizard = self.browse(cr, uid, ids[0], context)
        employee_ids = self.pool.get('hr.employee').search(cr, uid, [('user_id', '=', uid)])

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
            if wizard.motivation:
                body += "<li>%s: %s</li>" % ('Motivazione', wizard.motivation)
            body += "</ul></div>"
            post_vars = {
                'subject': "Modifica assegnatari",
                'body': body,
                'model': "protocollo.protocollo",
                'res_id': context['active_id']
            }
            new_context = dict(context).copy()
            new_context.update({'pec_messages': True})
            thread_pool = self.pool.get('protocollo.protocollo')
            thread_pool.message_post(cr, uid, context['active_id'], type="notification", context=new_context, **post_vars)

        return {'type': 'ir.actions.act_window_close'}
