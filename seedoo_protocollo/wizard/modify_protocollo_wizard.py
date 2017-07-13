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
    _name = 'protocollo.modify.wizard'
    _description = 'Modify Protocollo Management'

    def  set_before(self, before, label, value):
        if not value:
            value = ''
        before += label + ': ' + value + '\n'
        return before

    def set_after(self, after, label, value):
        after += label + ': ' + value + '\n'
        return after

    _columns = {
        'complete_name': fields.char('Numero Protocollo', size=256, required=True, readonly=True),
        'registration_date': fields.datetime('Data Registrazione', readonly=True),
        'type': fields.selection(
            [
                ('out', 'Uscita'),
                ('in', 'Ingresso'),
                ('internal', 'Interno')
            ],
            'Tipo', size=32, required=True, readonly=True,
        ),
        'typology': fields.many2one(
            'protocollo.typology',
            'Tipologia',
            help="Tipologia invio/ricevimento: \
                Raccomandata, Fax, PEC, etc. \
                si possono inserire nuove tipologie \
                dal menu Tipologie."
        ),
        'receiving_date': fields.datetime('Data Ricezione', required=True,),
        'subject': fields.text('Oggetto', required=True,),
        'classification': fields.many2one('protocollo.classification', 'Titolario di Classificazione', required=False,),
        'sender_protocol': fields.char('Protocollo Mittente', required=False,),
        'dossier_ids': fields.many2many(
            'protocollo.dossier',
            'dossier_protocollo_pec_rel',
            'wizard_id', 'dossier_id',
            'Fascicoli'),
        'notes': fields.text('Note'),
        'cause': fields.text('Motivo della Modifica', required=True),
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

    def _default_typology(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'])
        return protocollo.typology.id

    def _default_receiving_date(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'])
        return protocollo.receiving_date

    def _default_subject(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'])
        return protocollo.subject

    def _default_classification(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'])
        return protocollo.classification.id

    def _default_sender_protocol(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'])
        return protocollo.sender_protocol

    def _default_dossier_ids(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'])
        dossier_ids = []
        for dossier_id in protocollo.dossier_ids:
            dossier_ids.append(dossier_id.id)
        return [(6, 0, dossier_ids)]

    def _default_notes(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'])
        return protocollo.notes

    _defaults = {
        'complete_name': _default_complete_name,
        'registration_date': _default_registration_date,
        'type': _default_type,
        'typology': _default_typology,
        'receiving_date': _default_receiving_date,
        'subject': _default_subject,
        'classification': _default_classification,
        'sender_protocol': _default_sender_protocol,
        'dossier_ids': _default_dossier_ids,
        'notes': _default_notes,
    }

    def action_save(self, cr, uid, ids, context=None):
        vals = {}
        before = {}
        after = {}
        wizard = self.browse(cr, uid, ids[0], context)
        protocollo_obj = self.pool.get('protocollo.protocollo')
        protocollo = protocollo_obj.browse(cr, uid, context['active_id'], context=context)
        historical_obj = self.pool.get('protocollo.history')
        vals['typology'] = wizard.typology.id
        if wizard.typology.id != protocollo.typology.id:
            if protocollo.typology.pec:
                raise orm.except_orm(
                    _('Attenzione!'),
                    _('Il metodo di spedizione PEC'
                      ' non puo\' essere modificato.')
                )
            elif wizard.typology.pec:
                raise orm.except_orm(
                    _('Attenzione!'),
                    _('Il metodo di spedizione PEC'
                      ' non puo\' essere inserito in questa fase.')
                )
            else:
                before['Tipologia'] = protocollo.typology.name
                after['Tipologia'] = wizard.typology.name

        vals['subject'] = wizard.subject
        before['Oggetto'] = protocollo.subject
        after['Oggetto'] = wizard.subject

        if protocollo.receiving_date != wizard.receiving_date :
            vals['receiving_date'] = wizard.receiving_date
            before['Data ricezione'] = protocollo.receiving_date
            after['Data ricezione'] = wizard.receiving_date

        historical = {
            'user_id': uid,
            'description': wizard.cause,
            'type': 'modify',
            'before': before,
            'after': after,
        }
        history_id = historical_obj.create(cr, uid, historical)
        vals['history_ids'] = [[4, history_id]]
        protocollo_obj.write(
            cr,
            uid,
            [context['active_id']],
            vals
        )

        action_class = "history_icon update"
        body = "<div class='%s'><ul>" % action_class
        for key, before_item in before.items():
            if before[key] != after[key]:
                body = body + "<li>%s: <span style='color:#990000'> %s</span> -> <span style='color:#009900'> %s </span></li>" \
                                % (str(key), before_item.encode("utf-8"), after[key].encode("utf-8"))
        body += "</ul></div>"

        post_vars = {'subject': "Modifica dati generali: \'%s\'" % wizard.cause,
                     'body': body,
                     'model': "protocollo.protocollo",
                     'res_id': context['active_id'],
                    }

        new_context = dict(context).copy()
        # if protocollo.typology.name == 'PEC':
        new_context.update({'pec_messages': True})

        thread_pool = self.pool.get('protocollo.protocollo')
        thread_pool.message_post(cr, uid, context['active_id'], type="notification", context=new_context, **post_vars)

        return {'type': 'ir.actions.act_window_close'}
