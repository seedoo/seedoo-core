# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import orm
from openerp import netsvc
from openerp import SUPERUSER_ID
import logging

from openerp.osv import *

_logger = logging.getLogger(__name__)


class ResPartner(orm.Model):
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

    _columns = {
        'legal_type': fields.selection([('individual', 'Persona Fisica'), ('legal', 'Azienda privata'), ('government', 'Amministrazione pubblica')],
                                       'Tipologia', size=32, required=False),
        'pa_type': fields.selection([('pa', 'Amministrazione Principale'), ('aoo', 'Area Organizzativa Omogenea'), ('uo', 'Unità Organizzativa')],
                                    'Tipologia amministrazione', size=5, required=False),
        'super_type': fields.char('super_type', size=5, required=False),
        'ident_code': fields.char('Codice Identificativo Area (AOO)', size=256, required=False),
        'ammi_code': fields.char('Codice Amministrazione', size=256, required=False),
        'ipa_code': fields.char('Codice Unità Organizzativa', size=256, required=False),
        'parent_pa_id': fields.many2one('res.partner', 'Organizzazione di Appartenenza', required=False),
        'parent_pa_type': fields.related('parent_pa_id', 'pa_type', type='char', readonly=True, string='Tipologia amministrazione padre'),
        'child_pa_ids': fields.one2many('res.partner', 'parent_pa_id', 'Strutture Afferenti', required=False)
    }

    def message_post(
            self, cr, uid, thread_id, body='', subject=None, type='notification',
            subtype=None, parent_id=False, attachments=None, context=None,
            content_subtype='html', **kwargs):
        if context is None:
            context = {}
        msg_id = super(ResPartner, self).message_post(
            cr, uid, thread_id, body=body, subject=subject, type=type,
            subtype=subtype, parent_id=parent_id, attachments=attachments,
            context=context, content_subtype=content_subtype, **kwargs)
        if (
                    context.get('main_message_id') and
                    (
                                context.get('pec_type') or
                                context.get('send_error')
                    )
        ):
            wf_service = netsvc.LocalService("workflow")
            _logger.info('workflow: mail message trigger')
            wf_service.trg_trigger(uid, 'mail.message',
                                   context['main_message_id'], cr)
        return msg_id