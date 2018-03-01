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

            res.append((doc_obj.id, check))

        return dict(res)


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
        'ripristina_per_protocollazione_visibility': fields.function(_ripristina_per_protocollazione_visibility,
                                                                     type='boolean',
                                                                     string='Ripristina per protocollazione')
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

        vals = {}
        for document in self.browse(cr, uid, ids):
            vals = {
                    # 'sharedmail_state': 'new',
                    'protocollo_id': None,
                    'doc_protocol_state': 'new'
                    # 'recovered_message_parent': document.id
                }
            if vals:
                try:
                    doc_copy_id = self.pool.get('gedoc.document').write(cr, uid, document.id, vals, context=context)
                except Exception as e:
                    raise orm.except_orm(_("Errore"), _("Non è possibile ripristinare questo documento"))

        return True
