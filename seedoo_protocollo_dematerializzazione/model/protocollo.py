# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.
import sys

from openerp.osv import fields, osv
from lxml import etree


class protocollo_protocollo(osv.Model):
    _inherit = 'protocollo.protocollo'

    _columns = {
        'importer_id': fields.many2one('dematerializzazione.storico.importazione.importer', 'Importer', readonly=True),
        'doc_imported_ref': fields.many2one('gedoc.document', 'Riferimento documento importato', readonly=True),
    }

    _sql_constraints = [
        ('protocol_doc_imported_ref_unique', 'unique(doc_imported_ref)',
         'Documento protocollato in precedenza!')
    ]

    def associa_importer_protocollo(self, cr, uid, prot_id, storico_importer_id):

        protocollo_obj = self.pool.get('protocollo.protocollo')

        prot_date = fields.datetime.now()

        vals = {}

        if storico_importer_id:
            vals['importer_id'] = storico_importer_id

        # SPOSTATO A LIVELLO DI CONFIGURAZIONE DEL PROTOCOLLO
        # if genera_segnatura:
        #     protocollo = self.browse(cr, uid, prot_id)
        #     # TODO: Resolve problems for ugly imports
        #     sys.path.append("../../seedoo_protocollo")
        #     from seedoo_protocollo import segnatura
        #     segnatura_xml = segnatura.segnatura_xml.SegnaturaXML(protocollo, prot_number, prot_date, cr, uid)
        #     xml = segnatura_xml.generate_segnatura_root()
        #     etree_tostring = etree.tostring(xml, pretty_print=True)
        #     vals['xml_signature'] = etree_tostring

        protocollo_obj.write(cr, uid, prot_id, vals)


class protocollo_aoo(osv.Model):
    _inherit = 'protocollo.aoo'
    _columns = {
        'importer_ids': fields.one2many('dematerializzazione.importer', 'aoo_id', 'Importer'),
    }
