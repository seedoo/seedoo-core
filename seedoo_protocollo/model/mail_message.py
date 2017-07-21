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

    def create(self, cr, uid, vals, context=None):

        msg_obj = super(MailMessage, self).create(cr, uid, vals, context=context)
        if vals.get("pec_type") in ('accettazione', 'avvenuta-consegna', 'errore-consegna'):
            protocollo_obj = self.pool.get('protocollo.protocollo')
            protocollo_ids = protocollo_obj.search(cr, uid, [('mail_pec_ref', '=', vals.get('pec_msg_parent_id'))],
                                                   context=context)
            for protocollo_id in protocollo_ids:
                if protocollo_id:
                    protocollo_obj = protocollo_obj.browse(cr, uid, protocollo_id, context=context)
                    receivers = self.pool.get('protocollo.sender_receiver')
                    if vals.get("pec_type") == 'accettazione':
                        receivers_ids = receivers.search(cr, uid, [('protocollo_id', '=', protocollo_id)], context=context)
                    elif vals.get("pec_type") in ('avvenuta-consegna', 'errore-consegna'):
                        receivers_ids = receivers.search(cr, uid, [('protocollo_id', '=', protocollo_id), ('pec_mail', '=', vals.get('recipient_addr'))], context=context)

                    for receiver_id in receivers_ids:
                        msg_log = None
                        receiver = self.pool.get('protocollo.sender_receiver')
                        receiver_obj = receiver.browse(cr, uid, receiver_id, context=context)

                        # if receivers_obj.pec_mail ==
                        notification_vals = {}
                        action_class = "history_icon registration"

                        if vals.get("pec_type") == 'accettazione':
                            msg_log = "<div class='%s'><ul><li>PEC prot. %s inviata a %s e' stata accettata</li></ul></div>" \
                                             % (action_class, protocollo_obj.complete_name, receiver_obj.pec_mail)
                            notification_vals = {
                                'pec_ref': vals.get('pec_msg_parent_id'),
                                'pec_accettazione_ref': msg_obj
                            }
                        elif vals.get("pec_type") == 'avvenuta-consegna':
                            msg_log = "<div class='%s'><ul><li>PEC prot. %s inviata a %s e' stata consegnata</li></ul></div>" \
                                      % (action_class, protocollo_obj.complete_name, receiver_obj.pec_mail)
                            notification_vals = {
                                'pec_ref': vals.get('pec_msg_parent_id'),
                                'pec_consegna_ref': msg_obj
                            }
                        elif vals.get("pec_type") == 'errore-consegna':
                            if vals.get("errore-esteso"):
                                msg_log = "<div class='%s'><ul><li>PEC prot. %s inviata a %s non e' stata consegnata per il seguente errore: <strong>%s</strong></li></ul></div>" \
                                % (action_class, protocollo_obj.complete_name, receiver_obj.pec_mail, vals.get("errore-esteso"))
                            else:
                                msg_log = "<div class='%s'><ul><li>PEC prot. %s inviata a %s non e' stata consegnata a causa di un errore</li></ul></div>" \
                                % (action_class, protocollo_obj.complete_name, receiver_obj.pec_mail)
                            notification_vals = {
                                'pec_ref': vals.get('pec_msg_parent_id'),
                                'pec_errore-consegna_ref': msg_obj
                            }
                        receiver_obj.write(notification_vals)

                        post_vars = {'subject': "Ricevuta di %s" % vals.get("pec_type"),
                                     'body': str(msg_log),
                                     'model': "protocollo.protocollo",
                                     'res_id': protocollo_obj.id,
                                     }

                        thread_pool = self.pool.get('protocollo.protocollo')
                        thread_pool.message_post(cr, uid, protocollo_obj.id, type="notification", context=context, **post_vars)


        return msg_obj