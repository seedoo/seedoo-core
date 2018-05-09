# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp import SUPERUSER_ID
from openerp.osv import fields, osv
import mimetypes


class protocollo_carica_allegati_step1_wizard(osv.TransientModel):
    _name = 'protocollo.carica.allegati.step1.wizard'
    _description = 'Wizard di Caricamento degli Allegati al Protocollo'

    _columns = {
        # 'datas_fname': fields.char('Nome Documento Principale', size=256, readonly=False),
        # 'datas': fields.binary('Documento', required=True),
        # 'datas_description': fields.char('Descrizione', size=256, readonly=False),
        'document_ids': fields.one2many(
            'protocollo.carica.documenti.allegati.step1.wizard',
            'wizard_id',
            'Documenti Secondari'),
    }

    # def _default_datas_fname(self, cr, uid, context):
    #     protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'])
    #     if protocollo and protocollo.doc_id:
    #         return protocollo.doc_id.datas_fname
    #     return False
    #
    # def _default_datas(self, cr, uid, context):
    #     protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'])
    #     if protocollo and protocollo.doc_id:
    #         return protocollo.doc_id.datas
    #     return False
    #
    # def _default_datas_description(self, cr, uid, context):
    #     protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'])
    #     if protocollo and protocollo.doc_id:
    #         return protocollo.doc_id.datas_description
    #     return False

    def _default_document_ids(self, cr, uid, context):
        attachment_obj = self.pool.get('ir.attachment')
        attachment_ids = attachment_obj.search(cr, uid, [
            ('res_model', '=', 'protocollo.protocollo'),
            ('res_id', '=', context['active_id']),
            ('is_protocol', '=', True)
        ])
        attachments = attachment_obj.browse(cr, uid, attachment_ids)
        res = []
        for attachment in attachments:
            if not attachment.is_main:
                res.append({
                    'datas_fname': attachment.datas_fname,
                    'datas': attachment.datas,
                    'datas_description': attachment.datas_description
                })
        return res

    _defaults = {
        # 'datas_fname': _default_datas_fname,
        # 'datas': _default_datas,
        # 'datas_description': _default_datas_description,
        'document_ids': _default_document_ids
    }


    def action_save(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids[0], context)

        # if wizard.datas and wizard.datas_fname and wizard.datas_description:
        configurazione_ids = self.pool.get('protocollo.configurazione').search(cr, uid, [])
        configurazione = self.pool.get('protocollo.configurazione').browse(cr, uid, configurazione_ids[0])
        protocollo_obj = self.pool.get('protocollo.protocollo')
        protocollo = protocollo_obj.browse(cr, uid, context['active_id'])

        # protocollo_obj.carica_documento_principale(cr, uid, context['active_id'], wizard.datas, wizard.datas_fname, wizard.datas_description)

        file_data_list = []
        if wizard.document_ids:
            for document in wizard.document_ids:
                filename = document.datas_fname
                if protocollo.state not in ['draft'] and configurazione.rinomina_documento_allegati:
                    filename = protocollo_obj._get_name_documento_allegato(cr, uid, document.datas_fname, protocollo.name, 'Prot', False)

                file_data_list.append({
                    'datas': document.datas,
                    'datas_fname': filename,
                    'datas_description': document.datas_description
                })
        protocollo_obj.carica_documenti_secondari(cr, uid, context['active_id'], file_data_list)

        return {
                'name': 'Protocollo',
                'view_type': 'form',
                'view_mode': 'form,tree',
                'res_model': 'protocollo.protocollo',
                'res_id': context['active_id'],
                'context': context,
                'type': 'ir.actions.act_window'
        }


class protocollo_carica_documenti_allegati_step1_wizard(osv.TransientModel):
    _name = 'protocollo.carica.documenti.allegati.step1.wizard'

    _columns = {
        'wizard_id': fields.many2one('protocollo.carica.allegati.step1.wizard'),
        'datas_fname': fields.char('Nome Documento', size=256, readonly=False),
        'datas': fields.binary('File Documento', required=True),
        'datas_description': fields.char('Descrizione Documento', size=256),
        'allegati_descrizione_required_wizard': fields.boolean('Descrizione allegato obbligatorio', readonly=1)
    }

    def _default_allegati_descrizione_wizard_required(self, cr, uid, context):
        configurazione_ids = self.pool.get('protocollo.configurazione').search(cr, uid, [])
        configurazione = self.pool.get('protocollo.configurazione').browse(cr, uid, configurazione_ids[0])
        return configurazione.allegati_descrizione_required

    _defaults = {
        'allegati_descrizione_required_wizard': _default_allegati_descrizione_wizard_required
    }