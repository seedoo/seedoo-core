# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

import logging
from openerp import SUPERUSER_ID
from openerp.osv import fields, osv, orm

_logger = logging.getLogger(__name__)


class create_mittente_destinatario_wizard(osv.TransientModel):

    _name = 'protocollo.create.mittente.destinatario.wizard'
    _description = 'Crea Mittente Destinatario'
    _inherit = 'protocollo.sender_receiver'

    _columns = {
        'pec_messaggio_ids': fields.many2many('protocollo.messaggio.pec',
                                              'protocollo_create_mittente_destinatario_wizard_pec_rel', 'wizard_id',
                                              'messaggio_pec_id', 'Messaggi PEC'),
        'sharedmail_messaggio_ids': fields.many2many('mail.message',
                                                     'protocollo_create_mittente_destinatario_wizard_sharedmail_rel',
                                                     'wizard_id', 'mail_message_id', 'Messaggi Sharedmail'),
    }

    def create_sender_receiver(self, cr, uid, ids, context=None):
        sender_receiver_obj = self.pool.get('protocollo.sender_receiver')
        mail_message_obj = self.pool.get('mail.message')
        protocollo_messaggio_pec_obj = self.pool.get('protocollo.messaggio.pec')
        wizard = self.browse(cr, uid, ids[0], context)
        protocollo = wizard.protocollo_id

        pec_messaggio_ids = []
        sharedmail_messaggio_ids = []
        if protocollo.type == 'in':
            mail_message_ids = mail_message_obj.search(cr, SUPERUSER_ID, [('pec_protocol_ref', '=', protocollo.id)])
            pec_messaggio_ids = protocollo_messaggio_pec_obj.search(cr, uid, [('messaggio_ref', 'in', mail_message_ids)])
            sharedmail_messaggio_ids = mail_message_obj.search(cr, SUPERUSER_ID, [('sharedmail_protocol_ref', '=', protocollo.id)])

        if wizard:
            values = {
                'source': wizard.source,
                'type': wizard.type,
                'pa_type': wizard.pa_type,
                'ident_code': wizard.ident_code,
                'ammi_code': wizard.ammi_code,
                'ipa_code': wizard.ipa_code,
                'name': wizard.name,
                'tax_code': wizard.tax_code,
                'vat': wizard.vat,
                'street': wizard.street,
                'city': wizard.city,
                'country_id': (wizard.country_id and wizard.country_id.id or False),
                'email': wizard.email,
                'phone': wizard.phone,
                'mobile': wizard.mobile,
                'pec_mail': wizard.pec_mail,
                'fax': wizard.fax,
                'zip': wizard.zip,
                'street2': wizard.street2,
                'state_id': (wizard.state_id and wizard.state_id.id or False),
                'function': wizard.function,
                'website': wizard.website,
                'title': (wizard.title and wizard.title.id or False),
                'save_partner': wizard.save_partner,
                'partner_id': wizard.partner_id.id,
                'pec_messaggio_ids': [(6, 0, pec_messaggio_ids)],
                'sharedmail_messaggio_ids': [(6, 0, sharedmail_messaggio_ids)],
                'protocollo_id': protocollo.id
            }
            sender_receiver = sender_receiver_obj.create(cr, uid, values)

            if not wizard.partner_id and wizard.save_partner:
                sender_receiver_obj.create_partner_from_sender_receiver(cr, uid, sender_receiver)

        return {
            'name': 'Protocollo',
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'protocollo.protocollo',
            'res_id': context['default_protocollo_id'],
            'context': context,
            'type': 'ir.actions.act_window',
            'flags': {'initial_mode': 'edit'}
        }
