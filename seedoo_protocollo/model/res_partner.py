# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

import logging

from openerp import netsvc
from openerp.osv import *
from openerp.osv import orm

_logger = logging.getLogger(__name__)


class res_partner(orm.Model):
    # inherit partner because PEC mails are not supposed to be associate to
    # generic models
    _inherit = 'res.partner'

    def on_change_pa_type(self, cr, uid, ids, pa_type):
        res = {'value': {}}
        if pa_type == 'aoo':
            res['value']['super_type'] = 'pa'
        elif pa_type == 'uo':
            res['value']['super_type'] = 'aoo'
        return res

    def on_change_pa_type(self, cr, uid, ids, pa_type):
        res = {'value': {}}
        if pa_type == 'aoo':
            res['value']['super_type'] = 'pa'
        elif pa_type == 'uo':
            res['value']['super_type'] = 'aoo'
        return res

    _columns = {
        'legal_type': fields.selection([('individual', 'Persona Fisica'), ('legal', 'Azienda Privata'), ('government', 'Amministrazione Pubblica')],
                                       'Tipologia', size=32, required=False),
        'pa_type': fields.selection([('pa', 'Amministrazione Principale'), ('aoo', 'Area Organizzativa Omogenea'), ('uo', 'Unità Organizzativa')],
                                    'Tipologia amministrazione', size=5, required=False),
        'super_type': fields.char('super_type', size=5, required=False),
        'ident_code': fields.char('Codice AOO', size=256, required=False),
        'ammi_code': fields.char('Codice iPA', size=256, required=False),
        'ipa_code': fields.char('Codice Unità Organizzativa', size=256, required=False),
        'parent_pa_id': fields.many2one('res.partner', 'PA di Appartenenza', required=False),
        'parent_pa_type': fields.related('parent_pa_id', 'pa_type', type='char', readonly=True, string='Tipologia amministrazione padre'),
        'child_pa_ids': fields.one2many('res.partner', 'parent_pa_id', 'Strutture Afferenti', required=False)
    }

    def dispatch_email_error(self, values):
        error = ''
        for data in values:
            error = error + '\nEsiste già un contatto in rubrica con la stessa ' + data[0].encode() + ': ' + data[1].encode()
        if error:
            raise orm.except_orm('Errore!', error)

    def check_email_field(self, cr, uid, domain, field, value, dispatch=True):
        configurazione_obj = self.pool.get('protocollo.configurazione')
        configurazione_ids = configurazione_obj.search(cr, uid, [])
        configurazione = configurazione_obj.browse(cr, uid, configurazione_ids[0])
        if configurazione.email_pec_unique:
            if (self.search(cr, uid, domain)):
                if dispatch:
                    self.dispatch_email_error([(field, value)])
                else:
                    return True
        return False

    def check_field_in_create(self, cr, uid, vals):
        errors = []
        if vals.has_key('pec_mail') and vals['pec_mail']:
            pec_mail_error = self.check_email_field(cr, uid, [('pec_mail', '=', vals['pec_mail'])], 'Mail PEC', vals['pec_mail'], False)
            if pec_mail_error:
                errors.append(('Mail PEC', vals['pec_mail']))
        if vals.has_key('email') and vals['email']:
            email_error = self.check_email_field(cr, uid, [('email', '=', vals['email'])], 'Mail', vals['email'], False)
            if email_error:
                errors.append(('Mail', vals['email']))
        self.dispatch_email_error(errors)

    def check_field_in_write(self, cr, uid, ids, vals):
        errors = []
        if vals.has_key('pec_mail') and vals['pec_mail']:
            pec_mail_error = self.check_email_field(cr, uid, [('pec_mail', '=', vals['pec_mail'])], 'Mail PEC', vals['pec_mail'], False)
            if pec_mail_error:
                errors.append(('Mail PEC', vals['pec_mail']))
        if vals.has_key('email') and vals['email']:
            email_error = self.check_email_field(cr, uid, [('email', '=', vals['email'])], 'Mail', vals['email'], False)
            if email_error:
                errors.append(('Mail', vals['email']))
        self.dispatch_email_error(errors)

    def create(self, cr, uid, vals, context=None):
        self.check_field_in_create(cr, uid, vals)
        return super(res_partner, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        self.check_field_in_write(cr, uid, ids, vals)
        return super(res_partner, self).write(cr, uid, ids, vals, context=context)

    def message_post(self, cr, uid, thread_id, body='', subject=None, type='notification',
            subtype=None, parent_id=False, attachments=None, context=None,
            content_subtype='html', **kwargs):
        if context is None:
            context = {}
        msg_id = super(res_partner, self).message_post(
            cr, uid, thread_id, body=body, subject=subject, type=type,
            subtype=subtype, parent_id=parent_id, attachments=attachments,
            context=context, content_subtype=content_subtype, **kwargs)
        if (context.get('main_message_id') and (context.get('pec_type') or context.get('send_error'))):
            wf_service = netsvc.LocalService("workflow")
            _logger.info('workflow: mail message trigger')
            wf_service.trg_trigger(uid, 'mail.message',
                                   context['main_message_id'], cr)
        return msg_id