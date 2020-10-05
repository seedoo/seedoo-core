# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp import SUPERUSER_ID
from lxml import etree
from ..segnatura.conferma_xml_parser import ConfermaXMLParser
from openerp.osv import orm, fields, osv
from openerp.tools.translate import _
from openerp import tools

class MailMessage(orm.Model):
    _inherit = "mail.message"

    def _get_message_attachs(self, cr, uid, ids, field_name, arg, context=None):
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

    def _get_eml(self, cr, uid, ids, field_name, arg, context=None):
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

            res[message_id] = self.pool.get('ir.attachment').search(cr, uid, [('id', 'in', attachment_ids), ('name', 'like', '.eml')])
        return res

    def _get_message_to(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, False)
        for message in self.browse(cr, uid, ids):
            if message.type=='email' and message.sharedmail_to:
                res[message.id] = message.sharedmail_to[:50] + " ..."
            if message.type == 'email' and message.pec_to:
                res[message.id] = message.pec_to[:50] + " ..."
        return res

    def _get_message_direction(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, False)
        for message in self.browse(cr, uid, ids):
            if message.type=='email' and message.direction_sharedmail:
                res[message.id] = message.direction_sharedmail
            if message.type == 'email' and message.direction:
                res[message.id] = message.direction
        return res

    _columns = {
        'pec_protocol_ref': fields.many2one('protocollo.protocollo', 'Protocollo (PEC)'),
        'pec_state': fields.selection([
            ('new', 'Da protocollare'),
            ('protocol', 'Protocollato'),
            ('not_protocol', 'Non protocollato')
            ], 'Stato PEC', readonly=True),
        'message_attachs': fields.function(_get_message_attachs, type='one2many',
                                        obj='ir.attachment', string='Allegati'),
        'eml': fields.function(_get_eml, type='one2many',
                                        obj='ir.attachment', string='Messaggio'),
        'eml_fname': fields.related('eml', 'datas_fname', type='char', readonly=True),
        'eml_content': fields.related('eml', 'datas', type='binary', string='Messaggio completo', readonly=True),
        'sharedmail_protocol_ref': fields.many2one('protocollo.protocollo', 'Protocollo (SharedMail)'),
        'sharedmail_state': fields.selection([
            ('new', 'Da protocollare'),
            ('protocol', 'Protocollato'),
            ('not_protocol', 'Non protocollato')
        ], 'Stato E-mail', readonly=True),
        'recovered_message_parent': fields.many2one('mail.message', 'Messaggio originale ripristino per protocollazione', readonly=True),
        'message_to': fields.function(_get_message_to, type='char', string='To', store=False),
        'message_direction': fields.function(_get_message_direction, type='char', string='To', store=False),
        'server_received_datetime': fields.datetime('Data'),
    }

    _order = 'date desc'


    def action_not_protocol(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        message = self.pool.get('mail.message').browse(cr, SUPERUSER_ID, ids[0])
        if 'sharedmail_messages' in context and context['sharedmail_messages']:
            if message.sharedmail_state == 'new':
                self.write(cr, SUPERUSER_ID, ids[0], {'sharedmail_state': 'not_protocol'})
            else:
                raise orm.except_orm(_("Avviso"), _("Il messaggio è già stato archiviato in precedenza: aggiorna la pagina"))
        if 'pec_messages' in context and context['pec_messages']:
            if message.pec_state == 'new':
                self.write(cr, SUPERUSER_ID, ids[0], {'pec_state': 'not_protocol'})
            else:
                raise orm.except_orm(_("Avviso"), _("Il messaggio è già stato archiviato in precedenza: aggiorna la pagina"))
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
        new_context = dict(context or {})
        mail_obj = self.pool.get('mail.message')
        mail_ids = mail_obj.browse(cr, uid, vals.get('pec_msg_parent_id'))
        author_id = mail_ids.author_id.id
        if author_id:
            vals.update({"author_id" : author_id})
        # gestione dei messaggi privati in arrivo sui server sharedmail o pec: il campo partener_ids deve essere
        # valorizzato con il partner dell'utente associato all'alias del server fetchmail. Questo fix è dovuto al fatto
        # che nei messaggi privati non viene fatto il normale routing del messaggio con relativa associazione dell'alias
        if context and context.has_key('fetchmail_server_id') and context['fetchmail_server_id']:
            fetchmail_server_obj = self.pool.get('fetchmail.server')
            fetchmail_server = fetchmail_server_obj.browse(cr, uid, context['fetchmail_server_id'])
            if (fetchmail_server.sharedmail or fetchmail_server.pec) and 'parent_id' in vals and vals['parent_id'] and 'partner_ids' in vals and vals['partner_ids']:
                if fetchmail_server.sharedmail and fetchmail_server.sharedmail_account_alias and fetchmail_server.sharedmail_account_alias.alias_user_id:
                    vals['partner_ids'] = [(4, fetchmail_server.sharedmail_account_alias.alias_user_id.partner_id.id)]
                    new_context['mail_notify_noemail'] = True
                elif fetchmail_server.pec and fetchmail_server.pec_account_alias and fetchmail_server.pec_account_alias.alias_user_id:
                    vals['partner_ids'] = [(4, fetchmail_server.pec_account_alias.alias_user_id.partner_id.id)]
                    new_context['mail_notify_noemail'] = True
        msg_obj = super(MailMessage, self).create(cr, uid, vals, context=new_context)
        if 'pec_type' in vals and vals.get("pec_type") in ('accettazione', 'avvenuta-consegna', 'errore-consegna', 'preavviso-errore-consegna', 'non-accettazione'):
            protocollo_ids = mail_ids.pec_protocol_ref
            for protocollo in protocollo_ids:
                if protocollo:
                    receivers = self.pool.get('protocollo.sender_receiver')
                    if vals.get("pec_type") in ['accettazione', 'non-accettazione']:
                        receivers_ids = receivers.search(cr, uid, [('protocollo_id', '=', protocollo.id)], context=context)
                    else:
                        recipient_addr_list = vals.get('recipient_addr').split(', ')
                        if vals.get("pec_type") in ('avvenuta-consegna','errore-consegna','preavviso-errore-consegna') and "cert_datetime" in vals:
                            receivers_ids = []
                            recipient_addr_list_lowercase = [recipient_addr.lower() for recipient_addr in recipient_addr_list]
                            for receiver_id in receivers.search(cr, uid, [('protocollo_id', '=', protocollo.id)], context=context):
                                receiver_data = receivers.browse(cr, uid, receiver_id)
                                if receiver_data.pec_mail and receiver_data.pec_mail.lower() in recipient_addr_list_lowercase:
                                    receivers_ids.append(receiver_data.id)
                        elif vals.get("pec_type") in ('errore-consegna','preavviso-errore-consegna'):
                            recipent_address_in_error_mail_list = []
                            for address in recipient_addr_list:
                                if vals.get("body").find(address) > -1:
                                    recipent_address_in_error_mail_list.append(address)
                                else:
                                    for attachment_id in vals['attachment_ids']:
                                        attachment_values = attachment_id[2]
                                        if 'index_content' in attachment_values and attachment_values['index_content']:
                                            attachment_content = attachment_values['index_content'].replace('\r', '').replace('\n', '')
                                            if attachment_content.find(address)>-1 and attachment_content.find('unable to look up host')>-1:
                                                recipent_address_in_error_mail_list.append(address)
                                                break
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
                                                     % (action_class, protocollo.name, receiver.pec_mail)
                                    notification_vals = {
                                        'accettazione_ref': msg_obj
                                    }
                                elif vals.get("pec_type") == 'avvenuta-consegna':
                                    msg_log = "<div class='%s'><ul><li>PEC prot. %s inviata a %s e' stata consegnata</li></ul></div>" \
                                              % (action_class, protocollo.name, receiver.pec_mail)
                                    notification_vals = {
                                        'consegna_ref': msg_obj
                                    }
                                elif vals.get("pec_type") == 'non-accettazione':
                                    msg_log = "<div class='%s'><ul><li>PEC prot. %s inviata a %s non e' stata accettata</li></ul></div>" \
                                              % (action_class, protocollo.name, receiver.pec_mail)
                                    notification_vals = {
                                        'non_accettazione_ref': msg_obj
                                    }
                                elif vals.get("pec_type") == 'errore-consegna' or vals.get("pec_type") == 'preavviso-errore-consegna':
                                    if vals.get("errore-esteso"):
                                        msg_log = "<div class='%s'><ul><li>PEC prot. %s inviata a %s non e' stata consegnata per il seguente errore: <strong>%s</strong></li></ul></div>" \
                                        % (action_class, protocollo.name, receiver.pec_mail, vals.get("errore-esteso"))
                                    else:
                                        msg_log = "<div class='%s'><ul><li>PEC prot. %s inviata a %s non e' stata consegnata a causa di un errore</li></ul></div>" \
                                        % (action_class, protocollo.name, receiver.pec_mail)
                                    notification_vals = {
                                        'errore_consegna_ref': msg_obj
                                    }

                                pec_messaggio_obj.write(cr, uid, pec_messaggio.id, notification_vals)

                                post_vars = {'subject': "Ricevuta di %s" % vals.get("pec_type"),
                                             'body': msg_log,
                                             'model': "protocollo.protocollo",
                                             'res_id': protocollo.id,
                                             }

                                thread_pool = self.pool.get('protocollo.protocollo')
                                thread_pool.message_post(cr, uid, protocollo.id, type="notification", context=context, **post_vars)
        elif 'pec_type' in vals and vals.get("pec_type") and vals.get("pec_type") in ('posta-certificata'):
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

    def recovery_message_to_protocol_action(self, cr, uid, ids, context=None):
        message_obj = self.pool.get('mail.message')
        vals = {}
        for message in self.browse(cr, uid, ids):
            check_message = message_obj.search(cr, SUPERUSER_ID, [('recovered_message_parent', '=', message.id)])
            if check_message:
                raise orm.except_orm(_("Avviso"), _("Messaggio già ripristinato in precedenza"))

            if message.type != 'email' or message.direction != 'in':
                raise orm.except_orm(_("Errore"), _("Non è possibile ripristinare questo tipo di messaggio"))

            if message.pec_type:
                    vals = {
                        'pec_state': 'new',
                        'pec_protocol_ref': '',
                        'recovered_message_parent': message.id
                    }
            elif message.sharedmail_type:
                vals = {
                        'sharedmail_state': 'new',
                        'sharedmail_protocol_ref': None,
                        'recovered_message_parent': message.id
                    }
            if vals:
                try:
                    message_copy_id = self.pool.get('mail.message').copy(cr, uid, message.id, vals, context=context)
                except Exception as e:
                    raise orm.except_orm(_("Errore"), _("Non è possibile ripristinare questo messaggio"))

        return True

    def message_to_protocol_action(self, cr, uid, ids, context=None):
        vals = {}
        for message in self.browse(cr, uid, ids):
            if message.message_direction != 'in':
                raise orm.except_orm(_("Errore"), _("Non è possibile ripristinare questo tipo di messaggio"))

            if message.pec_type:
                    vals = {
                        'pec_state': 'new'
                    }
            elif message.sharedmail_type:
                vals = {
                        'sharedmail_state': 'new'
                }
            if vals:
                try:
                    self.write(cr, uid, [message.id], vals, context=context)
                except Exception as e:
                    raise orm.except_orm(_("Errore"), _("Non è possibile ripristinare questo messaggio"))
        return True

    def check_access_rule(self, cr, uid, ids, operation, context=None):
        new_context = dict(context or {})
        new_context['skip_check'] = True
        return super(MailMessage, self).check_access_rule(cr, uid, ids, operation, context=new_context)

    def _find_allowed_doc_ids(self, cr, uid, model_ids, context=None):
        new_context = dict(context or {})
        new_context['skip_check'] = True
        return super(MailMessage, self)._find_allowed_doc_ids(cr, uid, model_ids, context=new_context)


    def go_to_sharedmail_message_action(self, cr, uid, ids, context=None):
        model_data_obj = self.pool.get('ir.model.data')
        view_rec = model_data_obj.get_object_reference(cr, uid, 'seedoo_protocollo', 'protocollo_sharedmail_form')
        view_id = view_rec and view_rec[1] or False
        return {
            'name': 'Message',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [view_id],
            'res_model': 'mail.message',
            'target': 'new',
            'res_id': context.get('message_ref', False),
            'type': 'ir.actions.act_window',
            'flags': {'form': {'options': {'mode': 'view'}}}
        }

    def _needaction_count(self, cr, uid, domain, context=None):
        if context and 'count' in context:
            res = self.search(cr, uid, domain, limit=100, order='id DESC', context=context)
            return len(res)
        else:
            return super(MailMessage, self)._needaction_count(cr, uid, domain, context=context)

    def create_protocollo_mailpec_action(self, cr, uid, ids, context={}):
        wizard_obj = self.pool.get('protocollo.mailpec.wizard')
        for id in ids:
            context['active_id'] = id
            options = wizard_obj._get_doc_principale_option(cr, uid, context)
            required = wizard_obj._default_documento_descrizione_wizard_required(cr, uid, context)
            if options and len(options)==1 and options[0][0] in ['eml', 'testo'] and not required:
                wizard_id = wizard_obj.create(cr, uid, {'select_doc_principale': options[0][0]}, context)
                return wizard_obj.action_save(cr, uid, [wizard_id], context)
            else:
                return {
                    'name': 'Creazione Bozza Protocollo',
                    'view_type': 'form',
                    'view_mode': 'form,tree',
                    'res_model': 'protocollo.mailpec.wizard',
                    'context': context,
                    'type': 'ir.actions.act_window',
                    'target': 'new'
                }