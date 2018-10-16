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

    def  set_before(self, before, label, value):
        if not value:
            value = ''
        before += value + '\n'
        return before

    def set_after(self, after, label, value):
        after += value + '\n'
        return after

    _columns = {
        'name': fields.char('Numero Protocollo', size=256, required=True, readonly=True),
        'registration_date': fields.datetime('Data Registrazione', readonly=True),
        'type': fields.selection([('out', 'Uscita'),('in', 'Ingresso'),('internal', 'Interno')], 'Tipo', size=32, required=True, readonly=True),
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

    def _default_type(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'], {'skip_check': True})
        return protocollo.type

    def _default_dossier_ids(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'], {'skip_check': True})
        dossier_ids = []
        for dossier_id in protocollo.dossier_ids:
            dossier_ids.append(dossier_id.id)
        return [(6, 0, dossier_ids)]

    def _default_display_motivation(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'], {'skip_check': True})
        if protocollo.registration_employee_id:
            return True
        else:
            return False

    _defaults = {
        'name': _default_name,
        'registration_date': _default_registration_date,
        'type': _default_type,
        'dossier_ids': _default_dossier_ids,
        'display_motivation': _default_display_motivation
    }

    def action_save(self, cr, uid, ids, context=None):
        vals = {}
        before = {}
        after = {}
        wizard = self.browse(cr, uid, ids[0], context)
        protocollo_obj = self.pool.get('protocollo.protocollo')
        protocollo = protocollo_obj.browse(cr, uid, context['active_id'], {'skip_check': True})
        operation_label = "Inserimento Fascicolazione" if len(protocollo.dossier_ids.ids) == 0 else "Modifica Fascicolazione"
        before['Fascicolo'] = ""
        after['Fascicolo'] = ""
        vals['dossier_ids'] = [[6, 0, [d.id for d in wizard.dossier_ids]]]
        before['Fascicolo'] = self.set_before(
            before['Fascicolo'],
            'Fascicolo',
            ', '.join([d.name for d in protocollo.dossier_ids])
        )
        after['Fascicolo'] = self.set_after(
            after['Fascicolo'],
            'Fascicolo',
            ', '.join([dw.name for dw in wizard.dossier_ids])
        )

        protocollo_obj.write(cr, uid, [context['active_id']], vals)

        action_class = "history_icon update"
        body = "<div class='%s'><ul>" % action_class
        for key, before_item in before.items():
            if before[key] != after[key]:
                body = body + "<li>%s: <span style='color:#990000'> %s</span> -> <span style='color:#009900'> %s </span></li>" \
                                % (str(key), before_item.encode("utf-8"), after[key].encode("utf-8"))
            else:
                body = body + "<li>%s: <span style='color:#999'> %s</span> -> <span style='color:#999'> %s </span></li>" \
                              % (str(key), before_item.encode("utf-8"), after[key].encode("utf-8"))


        post_vars = {'subject': "%s: \'%s\'" % (operation_label, wizard.cause),
                     'body': body,
                     'model': "protocollo.protocollo",
                     'res_id': context['active_id'],
                    }
        body += "</ul></div>"

        new_context = dict(context).copy()
        # if protocollo.typology.name == 'PEC':
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

