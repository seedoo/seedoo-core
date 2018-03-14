# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import fields, osv, orm
from ..model.util.selection import *



class protocollo_aggiungi_assegnatari_conoscenza_wizard(osv.TransientModel):
    _name = 'protocollo.aggiungi.assegnatari.conoscenza.wizard'
    _description = 'Aggiungi Assegnatari Conoscenza'

    _columns = {
        'assegnatario_conoscenza_ids': fields.many2many('protocollo.assegnatario',
                                                        'protocollo_aggiungi_assegnatari_conoscenza_rel',
                                                        'wizard_id',
                                                        'assegnatario_id',
                                                        'Assegnatari Conoscenza'),
    }

    def action_save(self, cr, uid, ids, context=None):
        before = {'competenza': '', 'conoscenza': ''}
        after = {'competenza': '', 'conoscenza': ''}
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'])
        wizard = self.browse(cr, uid, ids[0], context)
        employee_ids = self.pool.get('hr.employee').search(cr, uid, [('user_id', '=', uid)])

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
            body = body + "<li>%s: <span style='color:#990000'> %s</span> -> <span style='color:#009900'> %s </span></li>" \
                          % (str('Assegnatari Conoscenza'), str(before['conoscenza']), str(after['conoscenza']))
            body += "</ul></div>"
            post_vars = {
                'subject': "Aggiunta assegnatari conoscenza",
                'body': body,
                'model': "protocollo.protocollo",
                'res_id': context['active_id']
            }
            new_context = dict(context).copy()
            new_context.update({'pec_messages': True})
            thread_pool = self.pool.get('protocollo.protocollo')
            thread_pool.message_post(cr, uid, context['active_id'], type="notification", context=new_context, **post_vars)

        return {'type': 'ir.actions.act_window_close'}
