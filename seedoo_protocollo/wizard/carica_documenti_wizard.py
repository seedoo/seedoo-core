# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp import SUPERUSER_ID
from openerp.osv import fields, osv
import mimetypes


class protocollo_carica_documenti_step1_wizard(osv.TransientModel):
    _name = 'protocollo.carica.documenti.step1.wizard'
    _description = 'Wizard di Caricamento del Documento del Protocollo'

    _columns = {
        'datas_fname': fields.char('Nome Documento Principale', size=256, readonly=False),
        'datas': fields.binary('Documento', required=True),
        'datas_description': fields.char('Descrizione', size=256, readonly=False),
        'document_ids': fields.one2many(
            'protocollo.carica.documenti.secondari.step1.wizard',
            'wizard_id',
            'Documenti Secondari'),
        'error_description': fields.text('Errore', readonly=True),
        'documento_descrizione_required_wizard': fields.boolean('Descrizione documento obbligatorio', readonly=1)
    }

    def _default_datas_fname(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'], {'skip_check': True})
        if protocollo and protocollo.doc_id:
            return protocollo.doc_id.datas_fname
        return False

    def _default_datas(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'], {'skip_check': True})
        if protocollo and protocollo.doc_id:
            return protocollo.doc_id.datas
        return False

    def _default_datas_description(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'], {'skip_check': True})
        if protocollo and protocollo.doc_id:
            return protocollo.doc_id.datas_description
        return False

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

    def _default_documento_descrizione_wizard_required(self, cr, uid, context):
        configurazione_ids = self.pool.get('protocollo.configurazione').search(cr, uid, [])
        configurazione = self.pool.get('protocollo.configurazione').browse(cr, uid, configurazione_ids[0])
        return configurazione.documento_descrizione_required

    _defaults = {
        'datas_fname': _default_datas_fname,
        'datas': _default_datas,
        'datas_description': _default_datas_description,
        'document_ids': _default_document_ids,
        'documento_descrizione_required_wizard': _default_documento_descrizione_wizard_required
    }

    def action_save(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids[0], context)

        if wizard.datas and wizard.datas_fname:
            wizard_datas_encoded = wizard.datas.decode('base64').encode('base64')
            document_datas_encoded_list = []

            protocollo_obj = self.pool.get('protocollo.protocollo')
            file_data_list = []
            if wizard.document_ids:
                for document in wizard.document_ids:
                    document_datas_encoded = document.datas.decode('base64').encode('base64')
                    if document_datas_encoded == wizard_datas_encoded:
                        error_description = "Il contenuto dell'allegato '"+str(document.datas_fname)+"' è uguale al documento principale!"
                        wizard.write({'error_description': error_description})
                        #raise osv.except_orm('Attenzione!', "Il contenuto dell'allegato '"+str(document.datas_fname)+"' è uguale al documento principale!")
                        return {
                            'name': 'Carica Documento',
                            'view_type': 'form',
                            'view_mode': 'form,tree',
                            'res_model': 'protocollo.carica.documenti.step1.wizard',
                            'res_id': wizard.id,
                            'context': context,
                            'type': 'ir.actions.act_window',
                            'target': 'new'
                        }

                    if document_datas_encoded in document_datas_encoded_list:
                        error_description = "Il contenuto dell'allegato '"+str(document.datas_fname)+"' è già stato inserito fra gli allegati!"
                        wizard.write({'error_description': error_description})
                        #raise osv.except_orm('Attenzione!', "Il contenuto dell'allegato '"+str(document.datas_fname)+"' è già stato inserito fra gli allegati!")
                        return {
                            'name': 'Carica Documento',
                            'view_type': 'form',
                            'view_mode': 'form,tree',
                            'res_model': 'protocollo.carica.documenti.step1.wizard',
                            'res_id': wizard.id,
                            'context': context,
                            'type': 'ir.actions.act_window',
                            'target': 'new'
                        }
                    document_datas_encoded_list.append(document_datas_encoded)

                    file_data_list.append({
                        'datas': document.datas,
                        'datas_fname': document.datas_fname,
                        'datas_description': document.datas_description
                    })

            protocollo_obj.carica_documento_principale(cr, uid, context['active_id'], wizard.datas, wizard.datas_fname, wizard.datas_description)

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



class protocollo_carica_documenti_secondari_step1_wizard(osv.TransientModel):
    _name = 'protocollo.carica.documenti.secondari.step1.wizard'

    _columns = {
        'wizard_id': fields.many2one('protocollo.carica.documenti.step1.wizard'),
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

