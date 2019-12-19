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

from openerp import models, fields


class IrMailServer(models.Model):

    _inherit = "ir.mail_server"

    replace_return_path = fields.Boolean(
        "Sovrascrivi Return-Path",
        help="Sovrascrive il Return-Path con il campo From nell'invio di una e-mail in uscita")

    def send_email(self, cr, uid, message, mail_server_id=None, smtp_server=None, smtp_port=None, smtp_user=None,
                   smtp_password=None, smtp_encryption=None, smtp_debug=False, context=None):

        if self.replace_return_path and 'Return-Path' in message and 'From' in message:
            message.replace_header('Return-Path', message.get('From'))

        return super(IrMailServer, self).send_email(cr, uid, message, mail_server_id, smtp_server, smtp_port,
                                                    smtp_user, smtp_password, smtp_encryption, smtp_debug,
                                                    context=context)