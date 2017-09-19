# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

import base64
import tempfile
import openerp.tests.common as test_common
from openerp import addons
from openerp.osv import fields
import shutil
import os
import glob
from openerp import netsvc
import threading
from openerp.modules.module import get_module_resource
from openerp.osv.orm import except_orm


class TestGedocBase(test_common.SingleTransactionCase):

    def getDocFile(self, docname):
        path = get_module_resource(
            'seedoo_gedoc',
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
        path = get_module_resource('seedoo_gedoc',
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
        path = get_module_resource(
            'seedoo_gedoc',
            'tests', 'data', srcfile)
        currDir = os.path.dirname(path)
        for fname in glob.glob(currDir + '/*.' + srcfile.split('.')[1]):
            if os.path.basename(fname) != srcfile:
                os.remove(fname)

    def getDemoObject(self, module, data_id):
        cr, uid = self.cr, self.uid
        if module == '':
            module = 'seedoo_gedoc'
        return self.registry('ir.model.data').get_object(
            cr, uid, module, data_id)

    def getIdDemoObj(self, module, data_id):
        return self.getDemoObject(module, data_id).id

    def doc_unlink(self):
        self.modeldoc.unlink(self.cr, self.uid, self.doc_contract_id)

    def doc_write(self):
        self.modeldoc.write(
            self.cr,
            self.uid,
            self.doc_contract_id,
            {'subject': 'New Contract %s' % fields.datetime.now()})

    def dossier_write(self):
        self.modeldoc.write(
            self.cr,
            self.uid,
            self.dossier_id,
            {'description': 'New Contract Dossier %s' % fields.datetime.now()})

    def setUp(self):
        super(TestGedocBase, self).setUp()

        # Usefull stuffs
        self.uid = self.getIdDemoObj('', 'gedoc_user')
        self.admin = 1
        self.mod_uid = self.getIdDemoObj('', 'gedoc_user_modifier')
        self.read_uid = self.getIdDemoObj('', 'gedoc_user_reader')
        self.wf_service = netsvc.LocalService("workflow")
        self.modelattachs = self.registry('ir.attachment')
        self.modeldoc = self.registry('gedoc.document')
        self.modeldocsearch = self.registry('gedoc.document.search')
        self.uploaddocwizard = self.registry(
            'gedoc.upload.doc.wizard')
        self.modeldossier = self.registry('protocollo.dossier')
        threading.currentThread().testing = True

    def tearDown(self):
        # Remove fake docs
        self.delCopyOfFiles('contract.pdf')
        super(TestGedocBase, self).tearDown()
