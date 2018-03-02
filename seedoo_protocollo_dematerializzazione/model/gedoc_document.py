# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.
import sys

from openerp.osv import fields, osv, orm
from openerp import SUPERUSER_ID
from openerp.tools.translate import _


class gedoc_document(osv.Model):
    _inherit = 'gedoc.document'

    def _ripristina_per_protocollazione_visibility(self, cr, uid, ids, prop, unknow_none, context=None):
        protocollo_obj = self.pool.get('protocollo.protocollo')
        doc_obj = self.pool.get('gedoc.document').browse(cr, uid, ids)
        res = []
        for protocollo in protocollo_obj.browse(cr, uid, doc_obj.protocollo_id.id):
            check = False
            if protocollo.type == 'in' and protocollo.state in ['canceled'] and protocollo.importer_id:
                check = True

            if check:
                check_gruppi = self.user_has_groups(cr, uid, 'seedoo_protocollo.group_ripristina_per_protocollazione')
                check = check and check_gruppi

            if check:
                document_recovered_parents = self.pool.get('gedoc.document').search(cr, SUPERUSER_ID, [('recovered_document_parent', 'in', ids)])
                check = check and len(document_recovered_parents) == 0

            res.append((doc_obj.id, check))

        return dict(res)


    def _get_preview_datas(self, cr, uid, ids, field, arg, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        res = dict.fromkeys(ids, False)
        for doc in self.browse(cr, uid, ids):
            res[doc.id] = doc.main_doc_id.datas
        return res

    def _get_index_content(self, cr, uid, ids, field, arg, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        res = dict.fromkeys(ids, False)
        for doc in self.browse(cr, uid, ids):
            res[doc.id] = doc.main_doc_id.index_content
        return res


    _columns = {
        'importer_id': fields.many2one('dematerializzazione.storico.importazione.importer', 'Importer', readonly=True),
        'imported': fields.boolean('Importato', readonly=True),
        'protocollo_id': fields.many2one('protocollo.protocollo', 'Protocollo', readonly=True),
        'typology_id': fields.many2one('protocollo.typology', 'Tipologia', readonly=True),
        'doc_protocol_state': fields.selection([
                        ('new', 'Da protocollare'),
                        ('protocol', 'Protocollato'),
                        ('not_protocol', 'Non protocollato')
                    ], 'Stato in Protocollo', readonly=True),
        'preview': fields.function(_get_preview_datas, type='binary', string='Anteprima'),
        'index_content': fields.function(_get_index_content, type='text', string='Contenuto indicizzato'),
        'recovered_document_parent': fields.many2one('mail.message',
                                                    'Documento originale ripristino per protocollazione',
                                                    readonly=True),
        'ripristina_per_protocollazione_visibility': fields.function(_ripristina_per_protocollazione_visibility,
                                                                     type='boolean',
                                                                     string='Ripristina per protocollazione'),

    }

    _defaults = {
        'imported': False,
        'doc_protocol_state': 'new'
    }

    def action_not_protocol(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        self.write(cr, SUPERUSER_ID, ids[0], {'doc_protocol_state': 'not_protocol'})
        return True

    def recovery_document_to_protocol_action(self, cr, uid, ids, context=None):

        attachment_obj = self.pool.get('ir.attachment')
        doc_obj = self.pool.get('gedoc.document')
        for document in self.browse(cr, uid, ids):
            try:
                vals_attach = {
                    'res_id': False,
                }
                attach_copy_id = attachment_obj.copy(cr, uid, document.main_doc_id.id, vals_attach, context=context)
            except Exception as e:
                raise orm.except_orm(_("Errore"), _("Non è stato possibile creare il file"))

            try:
                vals_doc = {
                    'protocollo_id': None,
                    'doc_protocol_state': 'new',
                    'main_doc_id': attach_copy_id,
                    'recovered_document_parent': document.id
                }
                doc_copy_id = doc_obj.copy(cr, uid, document.id, vals_doc, context=context)
                if doc_copy_id:
                    attachment_obj.write(cr, uid, attach_copy_id, {'res_id': doc_copy_id})
            except Exception as e:
                raise orm.except_orm(_("Errore"), _("Non è stato possibile ripristinare questo documento"))

        return True
