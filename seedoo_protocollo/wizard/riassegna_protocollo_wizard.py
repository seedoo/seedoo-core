# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.exceptions


class protocollo_riassegna_wizard(osv.TransientModel):
    _name = 'protocollo.riassegna.wizard'
    _description = 'Riassegna Protocollo'

    _columns = {
        'assegnatario_competenza_id': fields.many2one('protocollo.assegnatario',
                                                      'Assegnatario per Competenza',
                                                      required=True),
        'motivation': fields.text('Motivazione'),
    }

    def on_change_assegnatario_competenza_id(self, cr, uid, ids, assegnatario_competenza_id, context=None):
        data = {}
        if context and 'active_id' in context:
            assegnazione_obj = self.pool.get('protocollo.assegnazione')
            assegnazione_competenza_ids = assegnazione_obj.search(cr, uid, [
                ('protocollo_id', '=', context['active_id']),
                ('tipologia_assegnazione', '=', 'competenza'),
                ('parent_id', '=', False)
            ], limit=1)
            if assegnazione_competenza_ids:
                assegnazione_competenza = assegnazione_obj.browse(cr, uid, assegnazione_competenza_ids[0])
            if assegnazione_competenza and assegnazione_competenza.assegnatario_id.id==assegnatario_competenza_id:
                data = {
                    'warning': {
                        'title': 'Attenzione',
                        'message': 'Hai selezionato lo stesso Assegnatario per Competenza attualmente assegnato al Protocollo!'
                    }
                }
        return data

    def action_save(self, cr, uid, ids, context=None):
        before = {'competenza': '', 'conoscenza': ''}
        after = {'competenza': '', 'conoscenza': ''}
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'])
        wizard = self.browse(cr, uid, ids[0], context)
        employee_ids = self.pool.get('hr.employee').search(cr, uid, [('user_id', '=', uid)])
        check = False
        if protocollo.state in ('registered', 'notified', 'waiting', 'sent', 'error') and \
                protocollo.assegnazione_competenza_ids and \
                        protocollo.assegnazione_competenza_ids[0].state == 'rifiutato':
            check = True

        if not check:
            raise openerp.exceptions.Warning(_(
                '"Non è più possibile eseguire l\'operazione richiesta! Il protocollo è già stato riassegnato da un altro utente!'))

        # assegnazione per competenza
        before['competenza'] = ', '.join([a.assegnatario_id.nome for a in protocollo.assegnazione_competenza_ids])
        self.pool.get('protocollo.assegnazione').salva_assegnazione_competenza(
            cr,
            uid,
            context.get('active_id', False),
            wizard.assegnatario_competenza_id.id if wizard.assegnatario_competenza_id else False,
            employee_ids[0] if employee_ids else False,
            True
        )
        after['competenza'] = wizard.assegnatario_competenza_id.nome

        action_class = "history_icon update"
        body = "<div class='%s'><ul>" % action_class
        if before['competenza'] or after['competenza']:
            body = body + "<li>%s: <span style='color:#990000'> %s</span> -> <span style='color:#009900'> %s </span></li>" \
                          % ('Assegnatario Competenza', before['competenza'], after['competenza'])
        if wizard.motivation:
            body += "<li>%s: %s</li>" % ('Motivazione', wizard.motivation)
        body += "</ul></div>"
        post_vars = {
            'subject': "Riassegnazione",
            'body': body,
            'model': "protocollo.protocollo",
            'res_id': context['active_id']
        }
        new_context = dict(context).copy()
        new_context.update({'pec_messages': True})
        thread_pool = self.pool.get('protocollo.protocollo')
        thread_pool.message_post(cr, uid, context['active_id'], type="notification", context=new_context, **post_vars)

        return {'type': 'ir.actions.act_window_close'}
