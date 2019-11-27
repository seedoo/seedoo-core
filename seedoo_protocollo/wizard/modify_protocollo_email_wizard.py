# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

import logging
from openerp.osv import fields, osv
from openerp import netsvc
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)


class protocollo_sender_receiver_wizard(osv.TransientModel):
    _name = 'protocollo.sender_receiver.email.wizard'

    _columns = {
        'wizard_id': fields.many2one('protocollo.modify.email.wizard',
                                     'Modifica Protocollo'),
        'name': fields.char('Nome Cognome/Ragione Sociale',
                            size=512,
                            required=True),
        'email': fields.char('E-mail', size=240, required=True),
        'sender_receiver_id': fields.many2one('protocollo.sender_receiver',
                                              'Destinatario',
                                              required=False)
    }


class wizard(osv.TransientModel):
    """
        A wizard to manage the modification of document protocollo
    """
    _name = 'protocollo.modify.email.wizard'
    _description = 'Modify Protocollo E-mail Management'

    _columns = {
        'name': fields.char('Numero Protocollo',
                            size=256,
                            required=True,
                            readonly=True),
        'sender_receivers': fields.one2many(
            'protocollo.sender_receiver.email.wizard',
            'wizard_id',
            'Destinatari',
            required=True,),
        'cause': fields.text('Motivo della Modifica', required=False),
        'protocol_sent': fields.boolean('Mail Inviata'),
    }

    def _default_name(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'], {'skip_check': True})
        return protocollo.name

    def _default_sender_receivers(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'], {'skip_check': True})
        res = []
        for send_rec in protocollo.sender_receivers:
           res.append({
                'sender_receiver_id': send_rec.id,
                'name': send_rec.name,
                'email': send_rec.email,
                })
        return res

    def _default_protocol_sent(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'], {'skip_check': True})
        if protocollo.state == 'registered':
            return False
        return True

    _defaults = {
        'name': _default_name,
        'sender_receivers': _default_sender_receivers,
        'protocol_sent': _default_protocol_sent,
    }

    def _process_mail(self, cr, uid, ids, protocollo_obj, context=None):
        # check if waiting then resend e-mail
        protocollo = protocollo_obj.browse(cr, uid, context['active_id'], {'skip_check': True})
        if protocollo.state in ['sent', 'acts']:
            protocollo.action_mail_pec_send()
        return True

    def action_save(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids[0], context)
        vals = {}
        before = {}
        after = {}
        if not wizard.cause:
            raise osv.except_osv(
                _('Attenzione!'),
                _('Manca la causale della modifica!')
            )
        protocollo_obj = self.pool.get('protocollo.protocollo')
        sender_receiver_obj = self.pool.get('protocollo.sender_receiver')
        protocollo = protocollo_obj.browse(cr, uid, context['active_id'], {'skip_check': True})
        for send_rec in protocollo.sender_receivers:
            before[send_rec.id] = {'name': send_rec.name, 'mail': send_rec.email}

        for send_rec in wizard.sender_receivers:
            srvals = {'email': send_rec.email, 'to_resend': True}
            after[send_rec.sender_receiver_id.id] = {'name': send_rec.name, 'mail': send_rec.email}
            sender_receiver_obj.write(cr, uid, [send_rec.sender_receiver_id.id], srvals)

        protocollo_obj.write(cr, uid, [context['active_id']], vals)
        if protocollo.registration_date:
            protocollo_obj.aggiorna_segnatura_xml(cr, uid, [protocollo.id], force=True, log=False, commit=False, context=context)

        action_class = "history_icon update"
        body = "<div class='%s'><ul>" % action_class
        for key, after_item in after.items():
            body = body + "<li>%s: <span style='color:#990000'> %s</span> -> <span style='color:#007ea6'> %s </span></li>" \
                              % (after_item['name'], before[key]['mail'].encode("utf-8"), after_item['mail'].encode("utf-8"))
        body += "</ul></div>"
        post_vars = {'subject': "Modificato indirizzo E-mail: %s" % wizard.cause,
                     'body': body,
                     'model': "protocollo.protocollo",
                     'res_id': context['active_id'],
                    }

        thread_pool = self.pool.get('protocollo.protocollo')
        thread_pool.message_post(cr, uid, context['active_id'], type="notification", context=context, **post_vars)

        self._process_mail(cr, uid, ids, protocollo_obj, context)
        return {'type': 'ir.actions.act_window_close'}