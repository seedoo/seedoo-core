# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

import logging
from openerp.osv import fields, osv
from openerp.osv import orm
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)


class wizard(osv.TransientModel):
    """
        A wizard to manage the modification of protocol object
    """
    _name = 'protocollo.classifica.wizard'
    _description = 'Classifica Protocollo Wizard'

    def  set_before(self, before, label, value):
        if not value:
            value = ''
        before += value + '\n'
        return before

    def set_after(self, after, label, value):
        after += value + '\n'
        return after

    _columns = {
        'complete_name': fields.char('Numero Protocollo', size=256, required=True, readonly=True),
        'registration_date': fields.datetime('Data Registrazione', readonly=True),
        'type': fields.selection([('out', 'Uscita'), ('in', 'Ingresso'), ('internal', 'Interno')], 'Tipo', size=32, required=True, readonly=True),
        'cause': fields.text('Motivo della Modifica', required=True),
        'classification': fields.many2one('protocollo.classification', 'Titolario di Classificazione', required=False),
        'classification_name_and_code': fields.related('classification',
                                      'name_and_code',
                                      type="char",
                                      string="Codice e Nome Titolario",
                                      readonly=True),
    }

    def _default_complete_name(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'])
        return protocollo.complete_name

    def _default_registration_date(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'])
        return protocollo.registration_date

    def _default_type(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'])
        return protocollo.type

    def _default_classification(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'])
        return protocollo.classification.id

    def _default_classification_name_and_code(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'])
        return protocollo.classification.name_and_code

    _defaults = {
        'complete_name': _default_complete_name,
        'registration_date': _default_registration_date,
        'type': _default_type,
        'classification_name_and_code': _default_classification_name_and_code,
    }

    def action_save(self, cr, uid, ids, context=None):
        vals = {}
        before = {}
        after = {}
        wizard = self.browse(cr, uid, ids[0], context)
        protocollo_obj = self.pool.get('protocollo.protocollo')
        protocollo = protocollo_obj.browse(cr, uid, context['active_id'], context=context)
        historical_obj = self.pool.get('protocollo.history')
        before['Titolario'] = ""
        after['Titolario'] = ""
        vals['classification'] = wizard.classification.id
        before['Titolario'] = self.set_before(before['Titolario'], 'Titolario', protocollo.classification.name)
        after['Titolario'] = self.set_after(after['Titolario'], 'Titolario', wizard.classification.name)

        historical = {
            'user_id': uid,
            'description': wizard.cause,
            'type': 'modify',
            'before': before,
            'after': after,
        }
        history_id = historical_obj.create(cr, uid, historical)
        vals['history_ids'] = [[4, history_id]]
        protocollo_obj.write(cr, uid, [context['active_id']], vals)

        action_class = "history_icon update"
        body = "<div class='%s'><ul>" % action_class
        for key, before_item in before.items():
            if before[key] != after[key]:
                body = body + "<li>%s: <span style='color:#990000'> %s</span> -> <span style='color:#009900'> %s </span></li>" \
                                % (str(key), before_item.encode("utf-8"), after[key].encode("utf-8"))
        body += "</ul></div>"
        post_vars = {'subject': "Modifica Classificazione: '%s'" % wizard.cause,
                     'body': body,
                     'model': "protocollo.protocollo",
                     'res_id': context['active_id'],
                     }

        thread_pool = self.pool.get('protocollo.protocollo')
        thread_pool.message_post(cr, uid, context['active_id'], type="notification", context=context, **post_vars)

        return {'type': 'ir.actions.act_window_close'}