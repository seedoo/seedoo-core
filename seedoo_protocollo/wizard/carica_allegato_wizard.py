# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

import logging
from openerp.osv import fields, osv
import magic
import base64

_logger = logging.getLogger(__name__)


class protocollo_carica_allegato_wizard(osv.TransientModel):
    _name = 'protocollo.carica.allegato.wizard'
    _description = 'Allegato Protocollo'

    def _get_preview_datas(self, cr, uid, ids, field, arg, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        res = dict.fromkeys(ids, False)
        for wizard in self.browse(cr, uid, ids):
            res[wizard.id] = wizard.datas
        return res

    _columns = {
        'read_only_mode': fields.boolean('Modalità Read Only', readonly=1),
        'datas_fname': fields.char('Nome Allegato', size=256, readonly=False),
        'datas': fields.binary('Allegato', required=True),
        'datas_description': fields.char('Descrizione', size=256, readonly=False),
        'error_description': fields.text('Errore', readonly=True),
        'attachment_description_required': fields.boolean('Descrizione allegato obbligatoria', readonly=1),
        #'preview': fields.binary('Anteprima Allegato', readonly=True),
        'preview': fields.function(_get_preview_datas, type='binary', string='Anteprima Allegato', readonly=True)
    }

    def _default_read_only_mode(self, cr, uid, context):
        if context and 'read_only_mode' in context and context['read_only_mode']:
            return True
        return False

    def _default_datas_fname(self, cr, uid, context):
        if context and 'active_model' in context and context['active_model']=='ir.attachment':
            attachment = self.pool.get('ir.attachment').browse(cr, uid, context['active_id'])
            if attachment:
                return attachment.datas_fname
        return False

    def _default_datas(self, cr, uid, context):
        if context and 'active_model' in context and context['active_model'] == 'ir.attachment':
            attachment = self.pool.get('ir.attachment').browse(cr, uid, context['active_id'])
            if attachment:
                return attachment.datas
        return False

    def _default_datas_description(self, cr, uid, context):
        if context and 'active_model' in context and context['active_model'] == 'ir.attachment':
            attachment = self.pool.get('ir.attachment').browse(cr, uid, context['active_id'])
            if attachment:
                return attachment.datas_description
        return False

    def _default_attachment_description_required(self, cr, uid, context):
        configurazione_ids = self.pool.get('protocollo.configurazione').search(cr, uid, [])
        configurazione = self.pool.get('protocollo.configurazione').browse(cr, uid, configurazione_ids[0])
        return configurazione.allegati_descrizione_required

    # def _default_preview(self, cr, uid, context):
    #     if context and 'active_model' in context and context['active_model'] == 'ir.attachment':
    #         attachment = self.pool.get('ir.attachment').browse(cr, uid, context['active_id'])
    #         if attachment and attachment.file_type=='application/pdf':
    #             return attachment.datas
    #     return False

    _defaults = {
        'read_only_mode': _default_read_only_mode,
        'datas_fname': _default_datas_fname,
        'datas': _default_datas,
        'datas_description': _default_datas_description,
        'attachment_description_required': _default_attachment_description_required,
        #'preview': _default_preview
    }

    def on_change_datas(self, cr, uid, ids, datas, context=None):
        values = {'preview': False}
        if datas:
            mimetype = magic.from_buffer(base64.b64decode(datas), mime=True)
            if mimetype == 'application/pdf':
                values = {'preview': datas}
        return {'value': values}

    def action_save(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids[0], context)

        protocollo_obj = self.pool.get('protocollo.protocollo')
        file_data = {
            'datas': wizard.datas,
            'datas_fname': wizard.datas_fname,
            'datas_description': wizard.datas_description
        }
        if context and 'active_model' in context and context['active_model'] == 'ir.attachment':
            file_data['attachment_id'] = context['active_id']
            attachment = self.pool.get('ir.attachment').browse(cr, uid, context['active_id'])
            protocollo_id = attachment.res_id
        else:
            protocollo_id = context['active_id']

        context_caricamento = {}
        file_data_list = [file_data]
        protocollo = protocollo_obj.browse(cr, uid, protocollo_id, {'skip_check': True})

        if protocollo.registration_date:
            context_caricamento['append'] = True
        protocollo_obj.carica_documenti_secondari(cr, uid, protocollo_id, file_data_list, context_caricamento)

        if protocollo.registration_date:
            protocollo_obj.aggiorna_segnatura_xml(cr, uid, [protocollo.id], force=True, log=False, commit=False, context=context)

        return {
                'name': 'Protocollo',
                'view_type': 'form',
                'view_mode': 'form,tree',
                'res_model': 'protocollo.protocollo',
                'res_id': protocollo_id,
                'context': context,
                'type': 'ir.actions.act_window',
                'flags': {'initial_mode': 'edit'}
        }