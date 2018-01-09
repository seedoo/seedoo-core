# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

import logging
import re

from openerp import netsvc
from openerp.osv import *
from openerp.osv import orm

_logger = logging.getLogger(__name__)


class res_partner(orm.Model):
    # inherit partner because PEC mails are not supposed to be associate to
    # generic models
    _inherit = 'res.partner'

    def on_change_legal_type(self, cr, uid, ids, legal_type):
        res = {'value': {}}
        if legal_type=='legal' or legal_type=='government':
            res['value']['is_company'] = True
        else:
            res['value']['is_company'] = False
        return res

    def on_change_pa_type(self, cr, uid, ids, pa_type):
        res = {'value': {}}
        if pa_type == 'aoo':
            res['value']['super_type'] = 'pa'
        elif pa_type == 'uo':
            res['value']['super_type'] = 'aoo'
        return res

    def _is_visible_parent_id(self, cr, uid, ids, name, arg, context=None):
        return {}

    def _is_visible_parent_id_search(self, cr, uid, obj, name, args, domain=None, context=None):
        partner_ids = []
        if context and context.has_key('legal_type') and context['legal_type']:
            if context['legal_type'] == 'individual':
                partner_ids = self.pool.get('res.partner').search(cr, uid, [('legal_type','=', 'legal')])
            elif context['legal_type'] == 'government' and context.has_key('pa_type'):
                partner_ids = self.pool.get('res.partner').search(cr, uid, [('pa_type','!=', False),('pa_type','!=', context['pa_type']),('pa_type','!=', 'uo')])
        return [('id', 'in', partner_ids)]

    _columns = {
        'legal_type': fields.selection([('individual', 'Persona Fisica'), ('legal', 'Azienda Privata'), ('government', 'Amministrazione Pubblica')],
                                       'Tipologia', size=32, required=False),
        'pa_type': fields.selection([('pa', 'Amministrazione Principale'), ('aoo', 'Area Organizzativa Omogenea'), ('uo', 'Unità Organizzativa')],
                                    'Tipologia amministrazione', size=5, required=False),
        'super_type': fields.char('super_type', size=5, required=False),
        'ident_code': fields.char('Codice AOO', size=256, required=False),
        'ammi_code': fields.char('Codice iPA', size=256, required=False),
        'ipa_code': fields.char('Codice Unità Organizzativa', size=256, required=False),
        #'parent_pa_id': fields.many2one('res.partner', 'PA di Appartenenza', required=False),
        #'parent_pa_type': fields.related('parent_pa_id', 'pa_type', type='char', readonly=True, string='Tipologia amministrazione padre'),
        #'child_pa_ids': fields.one2many('res.partner', 'parent_pa_id', 'Strutture Afferenti', required=False)

        'is_visible_parent_id': fields.function(_is_visible_parent_id, fnct_search=_is_visible_parent_id_search, type='boolean', string='Visibile'),
    }

    def _get_default_legal_type(self, cr, uid, context=None):
        if context and context.has_key('legal_type') and context['legal_type']:
            return context['legal_type']
        return False

    def _get_default_pa_type(self, cr, uid, context=None):
        if context and context.has_key('pa_type') and context['pa_type']:
            return context['pa_type']
        return False

    _defaults = {
        'legal_type': _get_default_legal_type,
        'pa_type': _get_default_pa_type,
    }

    def dispatch_email_error(self, errors):
        if errors:
            raise orm.except_orm('Errore!', errors)

    def check_email_validity(self, field, value, dispatch=True):
        if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", value) == None:
            error = 'Il campo ' + field.encode() + ' contiene un indirizzo email non valido: ' + value.encode()
            if dispatch:
                self.dispatch_email_error(error)
            else:
                return error

    def check_email_field(self, cr, uid, domain, field, value, dispatch=True):
        error = self.check_email_validity(field, value, dispatch)
        if error:
            return error

        configurazione_obj = self.pool.get('protocollo.configurazione')
        configurazione_ids = configurazione_obj.search(cr, uid, [])
        configurazione = configurazione_obj.browse(cr, uid, configurazione_ids[0])
        if configurazione.email_pec_unique:
            if (self.search(cr, uid, domain)):
                error = 'Esiste già un contatto in rubrica con la stessa ' + field.encode() + ': ' + value.encode()
                if dispatch:
                    raise orm.except_orm('Errore!', error)
                else:
                    return error

        return ''

    def check_field_in_create(self, cr, uid, vals):
        errors = ''
        if vals.has_key('pec_mail') and vals['pec_mail']:
            pec_mail_error = self.check_email_field(cr, uid, [('pec_mail', '=', vals['pec_mail'])], 'Mail PEC', vals['pec_mail'], False)
            if pec_mail_error:
                errors = errors + '\n' + pec_mail_error
        if vals.has_key('email') and vals['email']:
            email_error = self.check_email_field(cr, uid, [('email', '=', vals['email'])], 'Mail', vals['email'], False)
            if email_error:
                errors = errors + '\n' + email_error
        self.dispatch_email_error(errors)

    def check_field_in_write(self, cr, uid, ids, vals):
        errors = ''
        if vals.has_key('pec_mail') and vals['pec_mail']:
            pec_mail_error = self.check_email_field(cr, uid, [('pec_mail', '=', vals['pec_mail'])], 'Mail PEC', vals['pec_mail'], False)
            if pec_mail_error:
                errors = errors + '\n' + pec_mail_error
        if vals.has_key('email') and vals['email']:
            email_error = self.check_email_field(cr, uid, [('email', '=', vals['email'])], 'Mail', vals['email'], False)
            if email_error:
                errors = errors + '\n' + email_error
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