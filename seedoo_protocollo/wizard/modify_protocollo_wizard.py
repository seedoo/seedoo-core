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

    def _get_write_date(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(
            cr,
            uid,
            context['active_id']
            )
        return protocollo.write_date

    def on_change_typology(self, cr, uid, ids, typology_id, context=None):
        values = {'pec': False, 'sharedmail': False, 'email_error': ''}
        if typology_id:
            typology_obj = self.pool.get('protocollo.typology')
            typology = typology_obj.browse(cr, uid, typology_id)
            protocollo_obj = self.pool.get('protocollo.protocollo')
            protocollo = protocollo_obj.browse(cr, uid, context['active_id'], {'skip_check': True})
            if typology.pec:
                values['pec'] = True
                values['sharedmail'] = False
                if protocollo.type == 'out':
                    for sender_receiver in protocollo.sender_receivers:
                        if not sender_receiver.pec_mail:
                            values['email_error'] = "Attenzione!\nIl mezzo di trasmissione 'PEC' non può essere usato perchè ci sono dei destinatari privi di email PEC!"
                            break
            if typology.sharedmail:
                values['pec'] = False
                values['sharedmail'] = True
                if protocollo.type == 'out':
                    for sender_receiver in protocollo.sender_receivers:
                        if not sender_receiver.email:
                            values['email_error'] = "Attenzione!\nIl mezzo di trasmissione 'Email' non può essere usato perchè ci sono dei destinatari privi di email!"
                            break

            if protocollo.typology.id != typology.id:
                if protocollo.typology.pec:
                    values['email_error'] = "Attenzione!\nIl mezzo di trasmissione 'PEC' non può essere modificato!"
                elif typology.pec:
                    values['email_error'] = "Attenzione!\nIl mezzo di trasmissione 'PEC' non può essere inserito in questa fase!"

        return {'value': values}

    _columns = {
        'name': fields.char('Numero Protocollo', size=256, required=True, readonly=True),
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
            'Mezzo di Trasmissione',
            help="Mezzo di Trasmissione: \
                Raccomandata, Fax, PEC, etc. \
                si possono inserire nuove tipologie \
                dal menu Tipologie."
        ),
        'pec': fields.related('typology', 'pec', type='boolean', string='PEC', readonly=False, store=False),
        'sharedmail': fields.related('typology', 'sharedmail', type='boolean', string='Sharedmail', readonly=False, store=False),
        'receiving_date': fields.datetime('Data Ricezione', required=False,),
        'subject': fields.text('Oggetto', required=True),
        'body': fields.html('Corpo della mail'),
        'classification': fields.many2one('protocollo.classification', 'Titolario di Classificazione', required=False,),
        'sender_protocol': fields.char('Protocollo Mittente', required=False,),
        'server_sharedmail_id': fields.many2one('fetchmail.server', 'Account Email', domain="[('sharedmail', '=', True),('user_sharedmail_ids', 'in', uid)]"),
        'server_pec_id': fields.many2one('fetchmail.server', 'Account PEC', domain="[('pec', '=', True),('user_ids', 'in', uid)]"),
        'dossier_ids': fields.many2many(
            'protocollo.dossier',
            'dossier_protocollo_pec_rel',
            'wizard_id', 'dossier_id',
            'Fascicoli'),
        'notes': fields.text('Note'),
        'cause': fields.text('Motivo della Modifica', required=True),
        'last_write_date': fields.datetime('Ultimo salvataggio', required=True),
        'email_error': fields.text('Errore', readonly=True),
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

    def _default_typology(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'], {'skip_check': True})
        return protocollo.typology.id

    def _default_receiving_date(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'], {'skip_check': True})
        return protocollo.receiving_date

    def _default_subject(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'], {'skip_check': True})
        return protocollo.subject

    def _default_body(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'], {'skip_check': True})
        return protocollo.body

    def _default_classification(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'], {'skip_check': True})
        return protocollo.classification.id

    def _default_sender_protocol(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'], {'skip_check': True})
        return protocollo.sender_protocol

    def _default_dossier_ids(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'], {'skip_check': True})
        dossier_ids = []
        for dossier_id in protocollo.dossier_ids:
            dossier_ids.append(dossier_id.id)
        return [(6, 0, dossier_ids)]

    def _default_notes(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'], {'skip_check': True})
        return protocollo.notes

    def _default_last_write_date(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'], {'skip_check': True})
        return protocollo.write_date

    def _default_server_sharedmail_id(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'], {'skip_check': True})
        return protocollo.server_sharedmail_id

    def _default_server_pec_id(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'], {'skip_check': True})
        return protocollo.server_pec_id

    _defaults = {
        'name': _default_name,
        'registration_date': _default_registration_date,
        'type': _default_type,
        'typology': _default_typology,
        'receiving_date': _default_receiving_date,
        'subject': _default_subject,
        'body': _default_body,
        'classification': _default_classification,
        'sender_protocol': _default_sender_protocol,
        'dossier_ids': _default_dossier_ids,
        'notes': _default_notes,
        'last_write_date': _default_last_write_date,
        'server_sharedmail_id': _default_server_sharedmail_id,
        'server_pec_id': _default_server_pec_id,
        'email_error': ''
    }

    def action_save(self, cr, uid, ids, context=None):
        vals = {}
        before = {}
        after = {}
        wizard = self.browse(cr, uid, ids[0], context)
        protocollo_obj = self.pool.get('protocollo.protocollo')
        protocollo = protocollo_obj.browse(cr, uid, context['active_id'], {'skip_check': True})

        if wizard.last_write_date != protocollo.write_date:
            raise osv.except_osv(
                _('Attenzione!'),
                _('Il protocollo corrente e\' stato modificato di recente da un altro utente.\nAggiornare la pagina prima di modificare il protocollo.')
            )

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

        if wizard.server_sharedmail_id.id != protocollo.server_sharedmail_id.id:
            before['Account E-mail'] = protocollo.server_sharedmail_id.name
            after['Account E-mail'] = wizard.server_sharedmail_id.name
            vals['server_sharedmail_id'] = wizard.server_sharedmail_id.id

        if wizard.server_pec_id.id != protocollo.server_pec_id.id:
            before['Account PEC'] = protocollo.server_pec_id.name
            after['Account PEC'] = wizard.server_pec_id.name
            vals['server_pec_id'] = wizard.server_pec_id.id

        if wizard.subject != protocollo.subject:
            vals['subject'] = wizard.subject
            before['Oggetto'] = protocollo.subject
            after['Oggetto'] = wizard.subject

        if wizard.body != protocollo.body:
            vals['body'] = wizard.body
            before['Corpo della mail'] = protocollo.body
            after['Corpo della mail'] = wizard.body

        if protocollo.receiving_date != wizard.receiving_date:
            vals['receiving_date'] = wizard.receiving_date
            before['Data ricezione'] = protocollo.receiving_date
            after['Data ricezione'] = wizard.receiving_date

        protocollo_obj.write(cr, uid, [context['active_id']], vals)


        body = ''
        for key, before_item in before.items():
            if before[key] != after[key]:
                body = body + "<li>%s: <span style='color:#990000'> %s</span> -> <span style='color:#009900'> %s </span></li>" \
                                % (str(key), before_item, after[key])
            else:
                body = body + "<li>%s: <span style='color:#666'> %s</span> -> <span style='color:#666'> %s </span></li>" \
                              % (str(key), before_item, after[key])
        if body:
            action_class = "history_icon update"
            body_complete = "<div class='%s'><ul>" % action_class
            body_complete += body + "</ul></div>"

            post_vars = {'subject': "Modifica dati generali: %s" % wizard.cause,
                         'body': body_complete,
                         'model': "protocollo.protocollo",
                         'res_id': context['active_id'],
                        }

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
                'type': 'ir.actions.act_window',
                'flags': {'initial_mode': 'edit'}
        }

