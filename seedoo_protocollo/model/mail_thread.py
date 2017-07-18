from openerp.osv import orm


class MailThread(orm.Model):
    _inherit = "mail.thread"

    def message_parse(self, cr, uid, message, save_original=False, context=None):

        if context is None:
            context = {}

        msg_dict = super(MailThread, self).message_parse(cr, uid, message, save_original=save_original, context=context)

        if (msg_dict['pec_type'] == 'accettazione' or msg_dict['pec_type'] == 'avvenuta-consegna') and msg_dict['pec_msg_parent_id']:
            protocollo_obj = self.pool.get('protocollo.protocollo')
            protocollo_ids = protocollo_obj.search(cr, uid, [('mail_pec_ref', '=', msg_dict['pec_msg_parent_id'])], context=context)
            for protocollo_id in protocollo_ids:
                if protocollo_id:
                    protocollo_obj = protocollo_obj.browse(cr, uid, protocollo_id, context=context)

                    if protocollo_obj.state == 'waiting':
                        action_class = "history_icon registration"
                        if msg_dict['pec_type'] == 'accettazione':
                            msg_type = 'accettata'
                        else:
                            msg_type = 'consegnata'
                        post_vars = {'subject': "Ricevuta di %s" % msg_dict['pec_type'],
                                     'body': "<div class='%s'><ul><li>PEC prot. %d inviata a %s e' stata %s</li></ul></div>" \
                                             % (action_class, protocollo_id, msg_dict['to'], msg_type),
                                     'model': "protocollo.protocollo",
                                     'res_id': protocollo_obj.id,
                                     }

                        thread_pool = self.pool.get('protocollo.protocollo')
                        thread_pool.message_post(cr, uid, protocollo_obj.id, type="notification", context=context, **post_vars)

        return msg_dict
