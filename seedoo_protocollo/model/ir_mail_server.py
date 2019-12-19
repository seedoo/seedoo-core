# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2017-2018 Flosslab http://www.flosslab.com
#    @authors
#       Andrea Peruzzu <andrea.peruzzu@flosslab.com>
#
#   About license see __openerp__.py
#
##############################################################################

from openerp import models, fields, SUPERUSER_ID


class IrMailServer(models.Model):

    _inherit = "ir.mail_server"

    replace_return_path = fields.Boolean(
        "Sovrascrivi Return-Path",
        help="Sovrascrive il Return-Path con il campo From nell'invio di una e-mail in uscita")

    def send_email(self, cr, uid, message, mail_server_id=None, smtp_server=None, smtp_port=None, smtp_user=None,
                       smtp_password=None, smtp_encryption=None, smtp_debug=False, context=None):

        # Get SMTP Server Details from Mail Server
        mail_server = None
        if mail_server_id:
            mail_server = self.browse(cr, SUPERUSER_ID, mail_server_id)
        elif not smtp_server:
            mail_server_ids = self.search(cr, SUPERUSER_ID, [], order='sequence', limit=1)
            if mail_server_ids:
                mail_server = self.browse(cr, SUPERUSER_ID, mail_server_ids[0])

        if mail_server.replace_return_path and 'From' in message:
            if 'Return-Path' in message:
                message.replace_header('Return-Path', message.get('From'))
            else:
                message.add_header('Return-Path', message.get('From'))

        return super(IrMailServer, self).send_email(cr, uid, message, mail_server_id, smtp_server, smtp_port,
                                                    smtp_user, smtp_password, smtp_encryption, smtp_debug,
                                                    context=context)