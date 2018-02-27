# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.
import base64

from openerp import SUPERUSER_ID
from openerp.osv import fields, osv
from lxml import etree


class CreaProtocolloDaDocumentoWizard(osv.TransientModel):
    _name = 'dematerializzazione.crea.protocollo.da.documento.wizard'
    _description = 'Create Protocollo da Documento'

    _columns = {
        'typology_id': fields.many2one('protocollo.typology', 'Tipologia'),
        'doc_principale': fields.many2one('ir.attachment', 'Allegato', readonly=True),
        'doc_fname': fields.related('doc_principale', 'datas_fname', type='char', readonly=True),
        'doc_description': fields.char('Descrizione documento', size=256, readonly=False),
        'preview': fields.binary('Anteprima allegato PDF'),
    }

    def _get_attachment_id(self, cr, uid, context):
        attachments = self.pool.get('ir.attachment').search(cr, uid, [
            ('res_model', '=', 'gedoc.document'),
            ('res_id', '=', context.get('active_id', False))
        ])
        if attachments:
            return attachments[0]
        return False

    def _default_doc_principale(self, cr, uid, context):
        return self._get_attachment_id(cr, uid, context)

    def _default_preview(self, cr, uid, context):
        attachment_id = self._get_attachment_id(cr, uid, context)
        if attachment_id:
            return self.pool.get('ir.attachment').browse(cr, uid, attachment_id).datas
        return False

    _defaults = {
        'doc_principale': _default_doc_principale,
        'preview': _default_preview,
    }

    def action_save(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids[0], context=context)
        protocollo_obj = self.pool.get('protocollo.protocollo')

        vals = {}
        vals['type'] = 'in'
        vals['user_id'] = uid
        vals['typology'] = wizard.typology_id.id
        protocollo_id = protocollo_obj.create(cr, uid, vals)

        protocollo_obj.carica_documento_principale(cr, uid, protocollo_id, wizard.preview, wizard.doc_fname, wizard.doc_description)

        action_class = "history_icon print"
        post_vars = {
            'subject': "Creata Bozza Protocollo",
            'body': "<div class='%s'><ul><li>Documento convertito in bozza di protocollo</li></ul></div>" % action_class,
            'res_id': protocollo_id,
            'model': 'protocollo.protocollo',
        }
        thread_pool = self.pool.get('protocollo.protocollo')
        thread_pool.message_post(cr, uid, protocollo_id, type="notification", context=context, **post_vars)

        self.pool.get('gedoc.document').write(cr, uid, [context.get('active_id')], {'protocollo_id': protocollo_id})

        obj_model = self.pool.get('ir.model.data')
        model_data_ids = obj_model.search(cr, uid, [('model', '=', 'ir.ui.view'), ('name', '=', 'protocollo_protocollo_form')])
        resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'protocollo.protocollo',
            'res_id': protocollo_id,
            'views': [(resource_id, 'form')],
            'type': 'ir.actions.act_window',
            'context': context,
        }