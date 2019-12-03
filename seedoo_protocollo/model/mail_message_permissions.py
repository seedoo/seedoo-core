# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import orm, fields, osv
from openerp import SUPERUSER_ID


class MailMessage(osv.Model):
    _inherit = 'mail.message'

    def _crea_bozza_da_pec_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        res = []

        for message in self.browse(cr, uid, ids, {'skip_check': True}):
            check = False
            protocollo = message.pec_protocol_ref

            if message.pec_type == 'posta-certificata' and message.pec_state == 'new' and not protocollo:
                check = True

            if check:
                check_gruppi = self.user_has_groups(cr, uid, 'seedoo_protocollo.group_crea_protocollo_da_pec_ingresso')
                check = check and check_gruppi

            res.append((message.id, check))

        return dict(res)

    def _crea_bozza_da_email_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        res = []

        for message in self.browse(cr, uid, ids, {'skip_check': True}):
            check = False
            protocollo = message.sharedmail_protocol_ref

            if message.sharedmail_type == 'sharedmail' and message.sharedmail_state == 'new' and not protocollo:
                check = True

            if check:
                check_gruppi = self.user_has_groups(cr, uid, 'seedoo_protocollo.group_crea_protocollo_da_email_ingresso')
                check = check and check_gruppi

            res.append((message.id, check))

        return dict(res)

    def _ripristina_per_protocollazione_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        res = []
        protocollo_obj = self.pool.get('protocollo.protocollo')
        protocolli = protocollo_obj.search(cr, uid, ['|', ('mail_pec_ref', 'in', ids), ('mail_sharedmail_ref', 'in', ids)])
        for protocollo in protocollo_obj.browse(cr, uid, protocolli):
            check = False
            if protocollo.type == 'in' and protocollo.state in ['canceled'] and (protocollo.pec is True or protocollo.sharedmail is True):
                check = True

            if check:
                check_gruppi = self.user_has_groups(cr, uid, 'seedoo_protocollo.group_ripristina_per_protocollazione')
                check = check and check_gruppi

            if check:
                message_recovered_parents = self.pool.get('mail.message').search(cr, SUPERUSER_ID, [('recovered_message_parent', 'in', ids)])
                check = check and len(message_recovered_parents) == 0

            message_id = protocollo.mail_pec_ref.id if protocollo.mail_pec_ref.id else protocollo.mail_sharedmail_ref.id
            res.append((message_id, check))

        return dict(res)

    def _ripristina_da_protocollare_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        res = []
        for message in self.browse(cr, uid, ids):
            check = False

            if message.message_direction=='in' and (message.pec_state=='not_protocol' or message.sharedmail_state=='not_protocol'):
                check = True

            if check:
                check_gruppi = self.user_has_groups(cr, uid, 'seedoo_protocollo.group_ripristina_per_protocollazione')
                check = check and check_gruppi

            res.append((message.id, check))

        return dict(res)

    _columns = {
        'crea_bozza_da_pec_visibility': fields.function(_crea_bozza_da_pec_visibility, type='boolean', string='Crea bozza da PEC'),
        'crea_bozza_da_email_visibility': fields.function(_crea_bozza_da_email_visibility, type='boolean', string='Crea bozza da email'),
        'ripristina_per_protocollazione_visibility': fields.function(_ripristina_per_protocollazione_visibility, type='boolean', string='Ripristina per protocollazione'),
        'ripristina_da_protocollare_visibility': fields.function(_ripristina_da_protocollare_visibility, type='boolean', string='Ripristina da protocollare')
    }
