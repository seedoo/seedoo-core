# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp import models, api, fields, tools


class EmailTemplate(models.Model):
    _inherit = 'email.template'

    @api.model
    def generate_email(self, template_id, res_id):
        template_values = super(EmailTemplate, self).generate_email(template_id, res_id)

        if self._context and 'protocollo_attachments' in self._context and self._context['protocollo_attachments']:
            template_values['attachments'] = self._context['protocollo_attachments']

        if self._context and 'protocollo_mail_server_id' in self._context and self._context['protocollo_mail_server_id']:
            template_values['mail_server_id'] = self._context['protocollo_mail_server_id']

        body_html = template_values.get('body_html')
        if not body_html:
            return template_values

        template = self.env['ir.model.data'].search([
            ('res_id', '=', template_id),
            ('model', '=', 'email.template'),
            ('module', 'like', 'seedoo_protocollo%'),
        ], limit=1)
        if not template:
            return template_values

        body_html = self.env['protocollo.protocollo'].get_body_signature(body_html, False)
        template_values['body'] = body_html
        template_values['body_html'] = body_html

        return template_values