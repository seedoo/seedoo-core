# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import fields, orm
from openerp import SUPERUSER_ID


class MailMessage(orm.Model):
    _inherit = "mail.message"

    def _get_pec_attachs(self, cr, uid, ids, field_name, arg, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]

        res = {}
        for message_id in ids:
            cr.execute("SELECT distinct attachment_id from message_attachment_rel where message_id = " + str(message_id))
            message_attachment_ids = cr.dictfetchall()
            attachment_ids = []
            for message_attachment_id in message_attachment_ids:
                attachment_ids.append(message_attachment_id['attachment_id'])
            res[message_id] = self.pool.get('ir.attachment').search(cr, uid, [('id', 'in', attachment_ids),
                                                                              ('name', 'not like', '.eml')
                                                                              ])
        return res

    def _get_pec_eml(self, cr, uid, ids, field_name, arg, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        res = {}
        for message_id in ids:
            cr.execute("SELECT distinct attachment_id from message_attachment_rel where message_id = " + str(message_id))
            message_attachment_ids = cr.dictfetchall()
            attachment_ids = []
            for message_attachment_id in message_attachment_ids:
                attachment_ids.append(message_attachment_id['attachment_id'])

            res[message_id] = self.pool.get('ir.attachment').search(cr, uid, [('id', 'in', attachment_ids),
                                                                              ('name', 'like', '.eml')
                                                                              ])
        return res

    _columns = {
        'pec_state': fields.selection([
            ('new', 'To Protocol'),
            ('protocol', 'Protocols'),
            ('not_protocol', 'No Protocol')
            ], 'Pec State', readonly=True),
        'pec_attachs': fields.function(_get_pec_attachs, type='one2many',
                                        obj='ir.attachment', string='Allegati alla PEC'),
        'pec_eml': fields.function(_get_pec_eml, type='one2many',
                                        obj='ir.attachment', string='Messaggio PEC'),
        'pec_eml_fname': fields.related('pec_eml', 'datas_fname', type='char', readonly=True),
        'pec_eml_content': fields.related('pec_eml', 'datas', type='binary', string='Messaggio completo', readonly=True),
    }

    _defaults = {
        'pec_state': 'new',
    }

    def action_not_protocol(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        self.write(cr, SUPERUSER_ID, ids[0], {'pec_state': 'not_protocol'})
        return True

    def name_get(self, cr, user, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        result = self.browse(cr, user, ids, context=context)
        res = []
        for rs in result:
            name = "%s - %s" % (rs.email_from, rs.subject)
            res += [(rs.id, name)]
        return res

