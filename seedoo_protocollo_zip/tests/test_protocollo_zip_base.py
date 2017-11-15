# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

import base64
import tempfile
import openerp.tests.common as test_common
import openerp.modules as addons
import shutil
import os
import glob
from openerp import netsvc
import threading
from openerp.osv.orm import except_orm


class TestProtocolloZipBase(test_common.SingleTransactionCase):

    def getDocFile(self, docname):
        path = addons.get_module_resource('seedoo_protocollo_zip',
                                          'tests', 'data', docname)
        with open(path) as test_data:
            content = test_data.read()
        return base64.encodestring(content)

    def getCopyOfFile(self, filename, srcfile):
        """
        this method get a copy of file , present in data folder
        of this tests.
        filename: the name of new file
        srcfile: the file which we want have a copy
        """
        path = addons.get_module_resource('seedoo_protocollo_zip',
                                          'tests', 'data', srcfile)
        currDir = os.path.dirname(path)
        new_file = '%s/%s.pdf' % (currDir, filename)
        shutil.copyfile(path, new_file)
        with open(new_file) as test_data:
            with tempfile.TemporaryFile() as out:
                base64.encode(test_data, out)
                out.seek(0)
                return path, out.read()

    def delCopyOfFiles(self, srcfile):
        path = addons.get_module_resource('seedoo_protocollo_zip',
                                          'tests', 'data', srcfile)
        currDir = os.path.dirname(path)
        for fname in glob.glob(currDir + '/*.' + srcfile.split('.')[1]):
            if os.path.basename(fname) != srcfile:
                os.remove(fname)

    def getDemoObject(self, module, data_id):
        cr, uid = self.cr, self.uid
        if module == '':
            module = 'seedoo_protocollo'
        return self.registry('ir.model.data').get_object(
            cr, uid, module, data_id)

    def getIdDemoObj(self, module, data_id):
        return self.getDemoObject(module, data_id).id

    def setUp(self):
        super(TestProtocolloZipBase, self).setUp()

        # Usefull stuffs
        self.company = self.getDemoObject('base', 'main_company')
        self.company.write({'ident_code': 'test_proto'})
        self.uid = self.getIdDemoObj('', 'protocollo_manager')
        self.admin = 1
        self.modelAttachs = self.registry('ir.attachment')
        self.modelProtocollo = self.registry('protocollo.protocollo')
        self.modelProtRegistry = self.registry('protocollo.registry')
        self.modelProtSendRec = self.registry('protocollo.sender_receiver')
        self.modelHrDepartmentCollaborator = \
            self.registry('hr.department.collaborator')
        self.zipWizard = self.registry('protocollo.archivio.zip')

        self.wf_service = netsvc.LocalService("workflow")

        # this is needed to avoid emails being actually sent
        threading.currentThread().testing = True

    def tearDown(self):
        # Remove fake docs
        self.delCopyOfFiles('test_doc_src.pdf')
        super(TestProtocolloZipBase, self).tearDown()
