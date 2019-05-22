# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.exceptions
from ..model.util.selection import *



class protocollo_aggiungi_assegnatari_conoscenza_wizard(osv.TransientModel):
    _name = 'protocollo.aggiungi.assegnatari.conoscenza.wizard'
    _description = 'Aggiungi Assegnatari Conoscenza'

    _columns = {
        'assegnatore_department_id': fields.many2one('hr.department',
                                          'Ufficio dell\'Assegnatore',
                                          domain="[('member_ids.user_id', '=', uid)]",
                                          required=True),
        'assegnatario_conoscenza_ids': fields.many2many('protocollo.assegnatario',
                                                        'protocollo_aggiungi_assegnatari_conoscenza_rel',
                                                        'wizard_id',
                                                        'assegnatario_id',
                                                        'Assegnatari Conoscenza',
                                                        domain="[('is_visible', '=', True)]"),
        'motivation': fields.text('Motivazione'),
        'assegnatari_empty': fields.boolean('Assegnatari Non Presenti'),
        'assegnatore_department_id_invisible': fields.boolean('Dipartimento Assegnatore Non Visibile', readonly=True),
    }

    def _default_assegnatore_department_id(self, cr, uid, context):
        return self.pool.get('protocollo.assegnazione').get_default_assegnatore_department_id(cr, uid, context['active_id'])

    def _default_assegnatore_department_id_invisible(self, cr, uid, context):
        department_id = self.pool.get('protocollo.assegnazione').get_default_assegnatore_department_id(cr, uid, context['active_id'])
        if department_id:
            return True
        return False

    def _default_assegnatari_empty(self, cr, uid, context):
        count = self.pool.get('protocollo.assegnatario').search(cr, uid, [], count=True, context=context)
        if count > 0:
            return False
        else:
            return True

    _defaults = {
        'assegnatari_empty': _default_assegnatari_empty,
        'assegnatore_department_id': _default_assegnatore_department_id,
        'assegnatore_department_id_invisible': _default_assegnatore_department_id_invisible
    }

    def action_save(self, cr, uid, ids, context=None):
        before = {'competenza': '', 'conoscenza': ''}
        after = {'competenza': '', 'conoscenza': ''}
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'])
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

        # assegnazione per conoscenza
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
            employee_ids[0] if employee_ids else False,
            False
        )
        after['conoscenza'] = ', '.join([a.assegnatario_id.nome for a in protocollo.assegnazione_conoscenza_ids])

        if (before['conoscenza'] or after['conoscenza']) and before['conoscenza']!=after['conoscenza']:
            action_class = "history_icon update"
            body = "<div class='%s'><ul>" % action_class
            body = body + "<li>%s: <span style='color:#990000'> %s</span> -> <span style='color:#007ea6'> %s </span></li>" \
                          % ('Assegnatari Conoscenza', before['conoscenza'], after['conoscenza'])
            body += "</ul></div>"
            post_vars = {
                'subject': "%s%s" % ("Aggiunta assegnatari conoscenza", ": " + wizard.motivation if wizard.motivation else ""),
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
                'type': 'ir.actions.act_window',
                'flags': {'initial_mode': 'edit'}
        }
