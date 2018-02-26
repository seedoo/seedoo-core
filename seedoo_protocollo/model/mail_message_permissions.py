# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import orm, fields, osv



class MailMessage(osv.Model):
    _inherit = 'mail.message'

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

            #To DO nascondere button dopo il ripristino
            message_id = protocollo.mail_pec_ref.id if protocollo.mail_pec_ref.id else protocollo.mail_sharedmail_ref.id
            res.append((message_id, check))

        return dict(res)

    _columns = {
        'ripristina_per_protocollazione_visibility': fields.function(_ripristina_per_protocollazione_visibility, type='boolean', string='Ripristina per protocollazione')
    }
