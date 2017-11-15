# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp import addons
import openerp.netsvc
import datetime
from openerp.osv import fields
from openerp.osv.orm import except_orm
# from openerp.addons.seedoo_gedoc.tests.test_gedoc_base import TestGedocBase
from test_gedoc_base import TestGedocBase


class TestGedoc(TestGedocBase):
    def test_0_document(self):
        """
        Testing creation of a document and visibility
        """
        cr, uid = self.cr, self.uid
        context = {
            'lang': 'en_US',
            'tz': False,
            'uid': uid,
        }
        doc_contract_id = self.modeldoc.create(
            cr, uid,
            {
                'name': 'test contract',
                'document_type': self.getIdDemoObj(
                    '', 'gedoc_document_type_contract'),
                'subject': 'Contract',
                'data_doc': fields.datetime.now(),
            },
            context=context
        )
        doc_contract = self.modeldoc.browse(
            cr, uid, doc_contract_id)
        self.assertEqual(doc_contract.user_id.id, uid)
        self.assertFalse(doc_contract.main_doc_id)
        user_modifier = self.getIdDemoObj(
            '', 'gedoc_user_modifier')
        user_reader = self.getIdDemoObj(
            '', 'gedoc_user_reader')
        context['uid'] = user_modifier
        searchedDocs = self.modeldoc.search(
            cr,
            user_modifier,
            [('subject', '=', 'Contract')],
            context=context
        )
        self.assertEqual(len(searchedDocs), 0)
        context['uid'] = user_reader
        searchedDocs = self.modeldoc.search(
            cr,
            user_reader,
            [('subject', '=', 'Contract')],
            context=context
        )
        self.assertEqual(len(searchedDocs), 0)
        context['uid'] = uid
        self.modeldoc.write(
            cr, uid, doc_contract_id,
            {
                'office_comp_ids': [
                    (4, self.getIdDemoObj(
                        '', 'generic_dept2'))
                ],
                'office_view_ids': [
                    (4, self.getIdDemoObj(
                        '', 'generic_dept3'))
                ],
            },
            context=context
        )
        context['uid'] = user_modifier
        searchedDocs = self.modeldoc.search(
            cr,
            user_modifier,
            [('subject', '=', 'Contract')],
            context=context
        )
        self.assertEqual(len(searchedDocs), 1)
        context['uid'] = user_reader
        searchedDocs = self.modeldoc.search(
            cr,
            user_reader,
            [('subject', '=', 'Contract')],
            context=context
        )
        self.assertEqual(len(searchedDocs), 1)
        self.uid = user_modifier
        self.doc_contract_id = doc_contract_id
        self.doc_write()
        context['active_id'] = doc_contract_id
        context['uid'] = uid
        wizard_id = self.uploaddocwizard.create(
            cr, uid,
            {
                'name': 'testcontract.pdf',
                'datas_fname': 'testcontract.pdf',
                'datas': self.getCopyOfFile(
                    'testcontract.pdf', 'contract.pdf')[1],
            },
            context=context
        )
        self.uploaddocwizard.action_save(
            cr, uid, [wizard_id], context=context
        )
        doc_contract.refresh()
        self.assertTrue(doc_contract.main_doc_id)
        self.uid = user_reader
        self.assertRaises(except_orm, self.doc_unlink)
        self.assertRaises(except_orm, self.doc_write)

    def test_1_dossier(self):
        """
        Testing creation of a dossier and visibility
        """
        cr, uid = self.cr, self.uid
        context = {
            'lang': 'en_US',
            'tz': False,
            'uid': uid,
        }
        classification_id = self.getIdDemoObj(
            '', 'protocollo_classification_8')
        res = self.modeldossier.on_change_dossier_type_classification(
            cr, uid, [],
            'fascicolo',
            classification_id,
            False
        )
        dossier_id = self.modeldossier.create(
            cr, uid,
            {
                'name': res['value']['name'],
                'description': 'test dossier',
                'classification_id': classification_id,
                'paperless': True
            },
            context=context
        )
        dossier = self.modeldossier.browse(
            cr, uid, dossier_id)
        self.assertEqual(dossier.state, 'draft')
        self.assertEqual(
            dossier.name,
            '<Fascicolo N.0 del \'7.   Sistema informativo\'>'
        )
        user_modifier = self.getIdDemoObj(
            '', 'gedoc_user_modifier')
        user_reader = self.getIdDemoObj(
            '', 'gedoc_user_reader')
        context['uid'] = user_modifier
        searchedDossiers = self.modeldossier.search(
            cr,
            user_modifier,
            [('description', '=', 'test dossier')],
            context=context
        )
        self.assertEqual(len(searchedDossiers), 0)
        context['uid'] = user_reader
        searchedDossiers = self.modeldossier.search(
            cr,
            user_reader,
            [('description', '=', 'test dossier')],
            context=context
        )
        self.assertEqual(len(searchedDossiers), 0)
        context['uid'] = uid
        self.modeldossier.write(
            cr, uid, dossier_id,
            {
                'office_comp_ids': [
                    (4, self.getIdDemoObj(
                        '', 'generic_dept2'))
                ],
                'office_view_ids': [
                    (4, self.getIdDemoObj(
                        '', 'generic_dept3'))
                ],
            },
            context=context
        )
        context['uid'] = user_modifier
        searchedDossiers = self.modeldossier.search(
            cr,
            user_modifier,
            [('description', '=', 'test dossier')],
            context=context
        )
        self.assertEqual(len(searchedDossiers), 1)
        context['uid'] = user_reader
        searchedDossiers = self.modeldossier.search(
            cr,
            user_reader,
            [('description', '=', 'test dossier')],
            context=context
        )
        self.assertEqual(len(searchedDossiers), 1)

        self.uid = user_modifier
        self.dossier_id = dossier_id
        context['active_id'] = dossier_id
        context['uid'] = user_modifier
        # adds a doc to the dossier
        doc_contract2_id = self.modeldoc.create(
            cr, uid,
            {
                'name': 'test contract 2',
                'document_type': self.getIdDemoObj(
                    '', 'gedoc_document_type_contract'),
                'subject': 'Contract',
                'data_doc': fields.datetime.now(),
            },
            context=context
        )
        self.modeldossier.write(
            cr,
            user_modifier,
            dossier_id,
            {'document_ids': [(4, doc_contract2_id)]},
            context=context
        )
        dossier.refresh()
        self.assertTrue(dossier.state, 'open')

        self.uid = user_reader
        context['uid'] = user_reader

    def test_2_search_doc(self):
        """
        Testing search document
        """
        cr, uid = self.cr, self.uid
        context = {
            'lang': 'en_US',
            'tz': False,
            'uid': uid,
        }
        # Create Doc
        doc_contract3_id = self.modeldoc.create(
            cr, uid,
            {
                'name': 'test contract 3',
                'document_type': self.getIdDemoObj(
                    '', 'gedoc_document_type_contract'),
                'subject': 'Contract 3',
                'data_doc': fields.datetime.now(),
            },
            context=context
        )
        doc_contract = self.modeldoc.browse(
            cr, uid, doc_contract3_id)
        self.assertEqual(doc_contract.user_id.id, uid)
        context['active_id'] = doc_contract3_id
        wizard_id = self.uploaddocwizard.create(
            cr, uid,
            {
                'name': 'testcontract2.pdf',
                'datas_fname': 'testcontract2.pdf',
                'datas': self.getCopyOfFile(
                    'testcontract2.pdf', 'contract.pdf')[1],
            },
            context=context
        )
        self.uploaddocwizard.action_save(
            cr, uid, [wizard_id], context=context
        )
        doc_contract.refresh()
        self.assertTrue(doc_contract.main_doc_id)
        # Create Dossier
        classification_id = self.getIdDemoObj(
            '', 'protocollo_classification_8')
        res = self.modeldossier.on_change_dossier_type_classification(
            cr, uid, [],
            'fascicolo',
            classification_id,
            False
        )
        dossier2_id = self.modeldossier.create(
            cr, uid,
            {
                'name': res['value']['name'],
                'description': 'test dossier',
                'classification_id': classification_id,
                'document_ids': [(4, doc_contract3_id)],
                'paperless': True
            },
            context=context
        )
        dossier = self.modeldossier.browse(
            cr, uid, dossier2_id)
        dossier.refresh()
        self.assertTrue(dossier.state, 'open')
        # Search Docs
        doc_search_id = self.modeldocsearch.create(
            cr,
            uid,
            {
                'name': 'gedoc.document',
                'dossier_id': dossier2_id
            },
            context=context
        )
        res = self.modeldocsearch.search_action(
            cr, uid, [doc_search_id], context=context)
        self.assertEqual(
            res['domain'],
            "[('id', 'in', (%s,))]" % doc_contract3_id
        )
        self.modeldocsearch.write(
            cr,
            uid,
            doc_search_id,
            {
                'index_content': 'new contract'
            },
            context=context
        )
        res = self.modeldocsearch.search_action(
            cr, uid, [doc_search_id], context=context)
        self.assertEqual(
            res['domain'],
            "[('id', 'in', (%s,))]" % doc_contract3_id
        )
        self.modeldocsearch.write(
            cr,
            uid,
            doc_search_id,
            {
                'dossier_id': 0,
                'index_content': 'dossier'
            },
            context=context
        )
        res = self.modeldocsearch.search_action(
            cr, uid, [doc_search_id], context=context)
        self.assertEqual(
            res['domain'],
            "[('id', 'in', (%d,))]" % 0
        )
        self.modeldocsearch.write(
            cr,
            uid,
            doc_search_id,
            {
                'subject': 'contract 3',
                'index_content': 'new contract'
            },
            context=context
        )
        res = self.modeldocsearch.search_action(
            cr, uid, [doc_search_id], context=context)
        self.assertEqual(
            res['domain'],
            "[('id', 'in', (%s,))]" % doc_contract3_id
        )
