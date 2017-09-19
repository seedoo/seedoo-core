# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp import netsvc
import datetime
from openerp.osv.orm import except_orm
from seedoo_protocollo_zip.tests.test_protocollo_zip_base import \
    TestProtocolloZipBase


class TestProtocolloZip(TestProtocolloZipBase):

    def test_0_prot_zip(self):
        """
        Testing receive pdf File and protocol it
        with signature as typology_rac and attachments
        """        # create protocol with attachments
        cr, uid = self.cr, self.uid
        partner_id = self.getIdDemoObj('base', 'main_partner')
        racc_id = self.getIdDemoObj('', 'protocollo_typology_rac')
        # todo protocollo_classification_6 non esistente
        com_varie_id = self.getIdDemoObj('', 'protocollo_classification_6')
        send_rec_id = self.modelProtSendRec.create(
            cr, uid,
            {
                'name': 'test_partner',
                'type': 'individual',
                'partner_id': partner_id
            }
        )
        prot_id = self.modelProtocollo.create(
            cr, uid,
            {
                'type': 'in',
                'subject': 'test',
                'typology': racc_id,
                'sender_receivers': [(4, send_rec_id)],
                'classification': com_varie_id,
                'datas_fname': 'test0',
                'datas': self.getCopyOfFile('test0', 'test_doc_src.pdf')[1],
                'mimetype': 'application/pdf'
            }
        )
        attach1_vals = {
            'name': 'demo1.odt',
            'datas': self.getDocFile('demo1.odt'),
            'datas_fname': 'demo1.odt',
            'res_model': 'protocollo.protocollo',
            'is_protocol': True,
            'reserved': False,
            'res_id': prot_id,
            }

        attach2_vals = {
            'name': 'demo2.ods',
            'datas': self.getDocFile('demo2.ods'),
            'datas_fname': 'demo2.ods',
            'res_model': 'protocollo.protocollo',
            'is_protocol': True,
            'reserved': False,
            'res_id': prot_id,
            }
        self.modelAttachs.create(cr, uid, attach1_vals)
        self.modelAttachs.create(cr, uid, attach2_vals)
        prot_obj = self.modelProtocollo.browse(cr, uid, prot_id)
        self.wf_service.trg_validate(
            uid, 'protocollo.protocollo', prot_id, 'register', cr)
        prot_obj.refresh()
        self.assertEqual(prot_obj.state, 'registered')
        prot_name = 'Protocollo_0000001_%d' % prot_obj.year
        self.assertEqual(prot_obj.doc_id.name, prot_name)
        context = {'active_id': prot_id}
        wizard_id = self.zipWizard.create(
            cr, uid, {}, context=context
        )
        wizard_zip = self.zipWizard.browse(
            cr, uid, wizard_id, context=context
        )
        self.assertEquals(wizard_zip.view_fields, False)
        self.zipWizard.create_archive(
            cr, uid, [wizard_id], context=context
        )
        wizard_zip.refresh()
        self.assertEquals(wizard_zip.view_fields, True)
        prot_now = datetime.datetime.now()
        prot_year = prot_now.year
        self.assertEquals(wizard_zip.datas_fname, '0000001_%d.zip' % prot_year)
        # TODO: create a temp zip file and
        # verify the exact number of files in the archive
        self.assertTrue(wizard_zip.datas)
