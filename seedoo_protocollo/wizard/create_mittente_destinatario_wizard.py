# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

import logging
from openerp.osv import fields, osv, orm

_logger = logging.getLogger(__name__)


class create_mittente_destinatario_wizard(osv.TransientModel):

    _name = 'protocollo.create.mittente.destinatario.wizard'
    _description = 'Crea Mittente Destinatario'
    _inherit = 'protocollo.sender_receiver'

    def create_sender_receiver(self, cr, uid, ids, context=None):
        sender_receiver_obj = self.pool.get('protocollo.sender_receiver')
        wizard = self.browse(cr, uid, ids[0], context)
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
                'partner_id': False,
                'protocollo_id': wizard.protocollo_id.id
            }
            sender_receiver_obj.create(cr, uid, values)

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
