# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

import logging
from openerp.osv import fields, osv
from openerp.osv import orm
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)


class protocollo_aggiungi_fascicolazione_wizard(osv.TransientModel):
    """
        A wizard to manage the modification of protocol object
    """
    _name = 'protocollo.aggiungi.fascicolazione.wizard'
    _description = 'Fascicola Protocollo'

    def  set_before(self, before, value):
        if not value:
            value = ''
        before += value + '\n'
        return before

    def set_after(self, after, value):
        after += value + '\n'
        return after

    _columns = {
        'name': fields.char('Numero Protocollo', size=256, readonly=True),
        'registration_date': fields.datetime('Data Registrazione', readonly=True),
        'cause': fields.text('Motivo della Modifica', required=False),
        'dossier_ids': fields.many2many('protocollo.dossier', 'protocollo_aggiungi_fascicolazione_dossier_rel', 'wizard_id', 'dossier_id', 'Fascicoli'),
        'display_motivation': fields.boolean('Visualizza Motivazione', readonly=True),
    }

    def _default_name(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'], {'skip_check': True})
        return protocollo.name

    def _default_registration_date(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'], {'skip_check': True})
        return protocollo.registration_date

    def _default_dossier_ids(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'], {'skip_check': True})
        dossier_ids = []
        for dossier_id in protocollo.dossier_ids:
            dossier_ids.append(dossier_id.id)
        return [(6, 0, dossier_ids)]

    def _default_display_motivation(self, cr, uid, context):
        protocollo_obj = self.pool.get('protocollo.protocollo')
        protocollo = protocollo_obj.browse(cr, uid, context['active_id'], {'skip_check': True})
        if protocollo.state in protocollo_obj.get_history_state_list(cr, uid) and protocollo.dossier_ids:
            return True
        else:
            return False

    _defaults = {
        'name': _default_name,
        'registration_date': _default_registration_date,
        'dossier_ids': _default_dossier_ids,
        'display_motivation': _default_display_motivation
    }

    def action_save(self, cr, uid, ids, context=None):
        vals = {}
        wizard = self.browse(cr, uid, ids[0], context)
        protocollo_obj = self.pool.get('protocollo.protocollo')
        protocollo = protocollo_obj.browse(cr, uid, context['active_id'], {'skip_check': True})

        before = ''
        after = ''
        save_history = True if protocollo.state in protocollo_obj.get_history_state_list(cr, uid) else False

        vals['dossier_ids'] = [[6, 0, [d.id for d in wizard.dossier_ids]]]
        if save_history:
            before = self.set_before('', ', '.join([d.name for d in protocollo.dossier_ids]))
            after = self.set_after('', ', '.join([dw.name for dw in wizard.dossier_ids]))
            operation_label = "Inserimento fascicolazione" if len(protocollo.dossier_ids.ids) == 0 else "Modifica fascicolazione"

        protocollo_obj.write(cr, uid, [context['active_id']], vals)

        if save_history:
            action_class = "history_icon update"
            body = "<div class='%s'><ul>" % action_class
            if before != after:
                body = body + "<li>%s: <span style='color:#990000'> %s</span> -> <span style='color:#007ea6'> %s </span></li>" \
                                % ('Fascicolo', before.encode("utf-8"), after.encode("utf-8"))
            else:
                body = body + "<li>%s: <span style='color:#999'> %s</span> -> <span style='color:#999'> %s </span></li>" \
                              % ('Fascicolo', before.encode("utf-8"), after.encode("utf-8"))

            post_vars = {
                'subject': "%s%s" % (operation_label, ": " + wizard.cause if wizard.cause else ""),
                'body': body,
                'model': "protocollo.protocollo",
                'res_id': context['active_id']
            }
            body += "</ul></div>"

            new_context = dict(context).copy()
            # if protocollo.typology.name == 'PEC':
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

