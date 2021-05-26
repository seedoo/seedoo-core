# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

import logging
from openerp.osv import fields, osv, orm

_logger = logging.getLogger(__name__)


class create_destinatari_da_gruppo_wizard(osv.TransientModel):

    _name = 'protocollo.create.destinatari.da.gruppo.wizard'
    _description = 'Crea Destinatari da Gruppo'

    _columns = {
        'gruppo_id': fields.many2one('res.partner.category', 'Gruppo'),
        'partner_ids': fields.many2many('res.partner',
                                        'protocollo_create_destinatari_da_gruppo_wizard_partner_rel',
                                        id1='wizard_id', id2='partner_id', string='Contatti'),
    }

    def onchange_gruppo_id(self, cr, uid, ids, gruppo_id, context=None):
        partner_ids = []
        if gruppo_id:
            gruppo = self.pool.get('res.partner.category').browse(cr, uid, gruppo_id)
            partner_ids = [(6, 0, gruppo.partner_ids.ids)]
        return {
            'value': {
                'partner_ids': partner_ids
            }
        }

    def create_destinatari_da_gruppo(self, cr, uid, ids, context=None):
        sender_receiver_obj = self.pool.get('protocollo.sender_receiver')
        wizard = self.browse(cr, uid, ids[0], context)
        if wizard.gruppo_id:
            for partner in wizard.gruppo_id.partner_ids:
                values = {
                    'source': 'receiver',
                    'type': partner.legal_type,
                    'pa_type': partner.pa_type,
                    'ident_code': partner.ident_code,
                    'ammi_code': partner.ammi_code,
                    'ipa_code': partner.ipa_code,
                    'name': partner.display_name,
                    'tax_code': partner.tax_code,
                    'vat': partner.vat,
                    'street': partner.street,
                    'city': partner.city,
                    'country_id': (partner.country_id and partner.country_id.id or False),
                    'email': partner.email,
                    'phone': partner.phone,
                    'mobile': partner.mobile,
                    'pec_mail': partner.pec_mail,
                    'fax': partner.fax,
                    'zip': partner.zip,
                    'street2': partner.street2,
                    'state_id': (partner.state_id and partner.state_id.id or False),
                    'function': partner.function,
                    'website': partner.website,
                    'title': (partner.title and partner.title.id or False),
                    'save_partner': False,
                    'partner_id': partner.id,
                    'protocollo_id': context['active_id']
                }
                sender_receiver_obj.create(cr, uid, values)

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
