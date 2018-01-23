# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import fields, orm
from openerp import SUPERUSER_ID
from lxml import etree
from ..segnatura.conferma_xml_parser import ConfermaXMLParser

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
        'pec_protocol_ref': fields.many2one('protocollo.protocollo', 'Protocollo'),
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
        'pec_server_user': fields.related('server_id', 'user', type='char', readonly=True, string='Account'),
        'sharedmail_protocol_ref': fields.many2one('protocollo.protocollo', 'Protocollo'),
        'sharedmail_state': fields.selection([
            ('new', 'To Protocol'),
            ('protocol', 'Protocols'),
            ('not_protocol', 'No Protocol')
        ], 'SharedMail State', readonly=True),
        'sharedmail_server_user': fields.related('server_sharedmail_id', 'user', type='char', readonly=True, string='Account'),

    }

    _defaults = {
        'pec_state': 'new',
        'sharedmail_state': 'new',
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
        if context is None:
            context = {}
        mail_obj = self.pool.get('mail.message')
        mail_ids = mail_obj.browse(cr, uid, vals.get('pec_msg_parent_id'))
        author_id = mail_ids.author_id.id
        if author_id:
            vals.update({"author_id" : author_id})
        msg_obj = super(MailMessage, self).create(cr, uid, vals, context=context)
        if vals.get("pec_type") in ('accettazione', 'avvenuta-consegna', 'errore-consegna'):
            protocollo_ids = mail_ids.pec_protocol_ref
            for protocollo in protocollo_ids:
                if protocollo:
                    receivers = self.pool.get('protocollo.sender_receiver')
                    if vals.get("pec_type") == 'accettazione':
                        receivers_ids = receivers.search(cr, uid, [('protocollo_id', '=', protocollo.id)], context=context)
                    else:
                        recipient_addr_list = vals.get('recipient_addr').split(', ')
                        if vals.get("pec_type") in ('avvenuta-consegna','errore-consegna') and "cert_datetime" in vals:
                            receivers_ids = receivers.search(cr, uid, [('protocollo_id', '=', protocollo.id), ('pec_mail', 'in', recipient_addr_list)], context=context)
                        elif vals.get("pec_type") in ('errore-consegna'):
                            recipent_address_in_error_mail_list = []
                            for address in recipient_addr_list:
                                if vals.get("body").find(address) > -1:
                                    recipent_address_in_error_mail_list.append(address)
                            receivers_ids = receivers.search(cr, uid, [('protocollo_id', '=', protocollo.id), ('pec_mail', 'in', recipent_address_in_error_mail_list)], context=context)

                    for receiver_id in receivers_ids:
                        msg_log = None
                        receiver_obj = self.pool.get('protocollo.sender_receiver')
                        pec_messaggio_obj = self.pool.get('protocollo.messaggio.pec')
                        receiver = receiver_obj.browse(cr, uid, receiver_id, context=context)
                        for pec_messaggio in receiver.pec_messaggio_ids:
                            if pec_messaggio.messaggio_ref.ids[0] == vals.get('pec_msg_parent_id'):
                                # if receivers_obj.pec_mail ==
                                notification_vals = {}
                                action_class = "history_icon registration"

                                if vals.get("pec_type") == 'accettazione':
                                    msg_log = "<div class='%s'><ul><li>PEC prot. %s inviata a %s e' stata accettata</li></ul></div>" \
                                                     % (action_class, protocollo.complete_name, receiver.pec_mail)
                                    notification_vals = {
                                        'accettazione_ref': msg_obj
                                    }
                                elif vals.get("pec_type") == 'avvenuta-consegna':
                                    msg_log = "<div class='%s'><ul><li>PEC prot. %s inviata a %s e' stata consegnata</li></ul></div>" \
                                              % (action_class, protocollo.complete_name, receiver.pec_mail)
                                    notification_vals = {
                                        'consegna_ref': msg_obj
                                    }
                                elif vals.get("pec_type") == 'errore-consegna':
                                    if vals.get("errore-esteso"):
                                        msg_log = "<div class='%s'><ul><li>PEC prot. %s inviata a %s non e' stata consegnata per il seguente errore: <strong>%s</strong></li></ul></div>" \
                                        % (action_class, protocollo.complete_name, receiver.pec_mail, vals.get("errore-esteso"))
                                    else:
                                        msg_log = "<div class='%s'><ul><li>PEC prot. %s inviata a %s non e' stata consegnata a causa di un errore</li></ul></div>" \
                                        % (action_class, protocollo.complete_name, receiver.pec_mail)
                                    notification_vals = {
                                        'errore_consegna_ref': msg_obj
                                    }

                                pec_messaggio_obj.write(cr, uid, pec_messaggio.id, notification_vals)

                                post_vars = {'subject': "Ricevuta di %s" % vals.get("pec_type"),
                                             'body': str(msg_log),
                                             'model': "protocollo.protocollo",
                                             'res_id': protocollo.id,
                                             }

                                thread_pool = self.pool.get('protocollo.protocollo')
                                thread_pool.message_post(cr, uid, protocollo.id, type="notification", context=context, **post_vars)
        elif 'pec_type' in vals and vals.get("pec_type") in ('posta-certificata'):
            if "attachment_ids" in vals and len(vals.get("attachment_ids")) > 0:
                for attachment_id in vals.get("attachment_ids"):
                    for attach in attachment_id:
                        if isinstance(attach, dict) and attach.get("datas_fname").lower() == 'conferma.xml':
                            tree = etree.fromstring(attach.get("index_content"))
                            conferma_xml = ConfermaXMLParser(tree)
                            numero_registrazione = conferma_xml.getNumeroRegistrazioneMessaggioRicevuto()
                            protocollo_ids = self.pool.get('protocollo.protocollo').search(cr, uid, [('name', '=', numero_registrazione)])
                            protocollo_obj = self.pool.get('protocollo.protocollo')
                            messaggio_pec_obj = self.pool.get('protocollo.messaggio.pec')
                            for protocollo_id in protocollo_ids:
                                protocollo = protocollo_obj.browse(cr, uid, protocollo_id)
                                for sender_receiver in protocollo.sender_receivers:
                                    sender_receiver_obj = self.pool.get('protocollo.sender_receiver')
                                    if sender_receiver.pec_mail == vals['email_from']:
                                        msgvals = {}
                                        messaggio_pec_id = messaggio_pec_obj.create(cr, uid, {'type': 'conferma', 'messaggio_ref': msg_obj})
                                        msgvals['pec_messaggio_ids'] = [(4, [messaggio_pec_id])]
                                        sender_receiver_obj.write(cr, uid, sender_receiver.id, msgvals)
                                        self.write(cr, SUPERUSER_ID, msg_obj, {'pec_state': 'not_protocol'})

        return msg_obj