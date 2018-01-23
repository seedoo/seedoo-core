# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

import logging
from openerp.osv import fields, osv
from openerp import netsvc
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)


class protocollo_sender_receiver_wizard(osv.TransientModel):
    _name = 'protocollo.sender_receiver.pec.wizard'

    _columns = {
        'wizard_id': fields.many2one('protocollo.modify.pec.wizard',
                                     'Modifica Protocollo'),
        'name': fields.char('Nome Cognome/Ragione Sociale',
                            size=512,
                            required=True),
        'pec_mail': fields.char('PEC', size=240, required=True),
        'sender_receiver_id': fields.many2one('protocollo.sender_receiver',
                                              'Destinatario',
                                              required=False)
    }


class wizard(osv.TransientModel):
    """
        A wizard to manage the modification of document protocollo
    """
    _name = 'protocollo.modify.pec.wizard'
    _description = 'Modify Protocollo PEC Management'

    def set_before(self, before, label, value):
        before += label + ': ' + value + '\n'
        return before

    def set_after(self, after, label, value):
        after += label + ': ' + value + '\n'
        return after

    _columns = {
        'name': fields.char('Numero Protocollo',
                            size=256,
                            required=True,
                            readonly=True),
        'sender_receivers': fields.one2many(
            'protocollo.sender_receiver.pec.wizard',
            'wizard_id',
            'Destinatari',
            required=True,),
        'cause': fields.text('Motivo della Modifica', required=False),
        'protocol_sent': fields.boolean('Mail Inviata'),
    }

    def _default_name(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(
            cr,
            uid,
            context['active_id']
            )
        return protocollo.name

    def _default_sender_receivers(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(
            cr,
            uid,
            context['active_id']
            )
        res = []
        for send_rec in protocollo.sender_receivers:
            if send_rec.pec_errore_consegna_status:
                res.append({
                    'sender_receiver_id': send_rec.id,
                    'name': send_rec.name,
                    'pec_mail': send_rec.pec_mail,
                    })
        return res

    def _default_protocol_sent(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(
            cr,
            uid,
            context['active_id']
            )
        if protocollo.state == 'registered':
            return False
        return True

    _defaults = {
        'name': _default_name,
        'sender_receivers': _default_sender_receivers,
        'protocol_sent': _default_protocol_sent,
    }

    def _process_mail(self, cr, uid, ids,
                      protocollo_obj, context=None):
        # check if waiting then resend pec mail
        protocollo = protocollo_obj.browse(cr, uid, context['active_id'],
                                           context=context)
        if protocollo.state in ('waiting', 'error'):
            wf_service = netsvc.LocalService('workflow')
            wf_service.trg_validate(uid, 'protocollo.protocollo',
                                    context['active_id'],
                                    'resend',
                                    cr)
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
        protocollo = protocollo_obj.browse(cr, uid, context['active_id'])
        res = []
        for send_rec in protocollo.sender_receivers:
            res.append({
                'sender_receiver_id': send_rec.id,
                'name': send_rec.name,
                'pec_mail': send_rec.pec_mail,
                })
        # before['Destinatari'] = self.set_before(before['pec_mail'], 'pec_mail', protocollo.classification.name)
        # before = self.set_before(
        #     before,
        #     'Destinatari',
        #     '/n'.join(['pec_mail: ' + str(r['pec_mail']) for r in res])
        #     )
        # after += 'Destinatari \n'

        for send_rec in wizard.sender_receivers:
            srvals = {'name': send_rec.name, 'pec_mail': send_rec.pec_mail, 'to_resend': True}
            # after = self.set_after(after, '', 'pec_mail: ' + send_rec.pec_mail + ', ')
            sender_receiver_obj.write(cr, uid, [send_rec.sender_receiver_id.id], srvals)

        protocollo_obj.write(cr, uid, [context['active_id']], vals)

        action_class = "history_icon update"
        # body = "<div class='%s'><ul><li><span style='color:#990000'> %s</span> " \
        #         u"\u2192" \
        #         "<span style='color:#009900'>%s</span></li></ul></div>" \
        #         % (action_class, str(before), str(after))

        # post_vars = {'subject': "Modificati  mittenti/destinatari: \'%s\'" % wizard.cause,
        #              'body': body,
        #              'model': "protocollo.protocollo",
        #              'res_id': context['active_id'],
        #             }

        # thread_pool = self.pool.get('protocollo.protocollo')
        # thread_pool.message_post(cr, uid, context['active_id'], type="notification", context=context, **post_vars)

        self._process_mail(cr, uid, ids, protocollo_obj, context)
        return {'type': 'ir.actions.act_window_close'}

    def action_resend(self, cr, uid, ids, context=None):
        protocollo_obj = self.pool.get('protocollo.protocollo')
        self._process_mail(cr, uid, ids, protocollo_obj, context)
