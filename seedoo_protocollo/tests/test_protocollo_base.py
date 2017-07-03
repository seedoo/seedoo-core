# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

import base64
import tempfile
import openerp.tests.common as test_common
# from openerp import addons
import shutil
import os
import glob
from openerp import netsvc
import hashlib
import threading
from openerp.osv.orm import except_orm
import openerp.modules as addons

# from openerp.modules.module import get_module_resource


'''
ATTENZIONE:

questa prima versione di test prevede che si sia installato
signature.sh  in /opt/signature/
nel file demo viene infatti inserito questo come
percorso parametrico per itext.location

Se lo script è già attivo in un altro path è necessario
modificare il percorso del parametro itext.location
nel file demo/data.xml

'''


class TestProtocolloBase(test_common.SingleTransactionCase):
    def getPecFile(self, msgname):
        path = addons.get_module_resource('seedoo_protocollo',
                                          'tests', 'data', msgname)
        with open(path) as test_data:
            content = test_data.read()
        return content

    '''
    this method get a copy of file , present in data folder
    of this tests.
    filename: the name of new file
    srcfile: the file which we want have a copy
    '''

    def getCopyOfFile(self, filename, srcfile):
        path = addons.get_module_resource('seedoo_protocollo',
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
        path = addons.get_module_resource('seedoo_protocollo',
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

    def sha1OfFile(self, attachment_id):
        cr, uid = self.cr, self.uid
        location = self.registry(
            'ir.config_parameter').get_param(
            cr, uid, 'ir_attachment.location'
        )
        location += '/protocollazioni'
        new_attachment = self.modelattachs.browse(
            cr, uid, attachment_id)
        file_path = self.modelProtocollo._full_path(
            cr, uid, location, new_attachment.store_fname)
        with open(file_path, 'rb') as f:
            return hashlib.sha1(f.read()).hexdigest()

    def setUp(self):
        super(TestProtocolloBase, self).setUp()
        # Set ir.config_parameter for env Test
        self.config_parameter = self.registry('ir.config_parameter')

        config_parameter_id = self.config_parameter.search(
            self.cr, self.uid, [('key', '=', 'itext.location')])

        self.config_parameter.write(self.cr, self.uid, config_parameter_id,
                                    {'value': '/opt/signature'})
        
        

        # Usefull stuffs
        self.company = self.getDemoObject('base', 'main_company')
        self.company.write(
            {'ammi_code': 'test_ammi_code_proto', 'ident_code': 'test_proto'})
        self.uid = self.getIdDemoObj('', 'protocollo_manager')
        self.admin = 1
        self.modelattachs = self.registry('ir.attachment')
        self.modelProtocollo = self.registry('protocollo.protocollo')
        self.modelProtRegistry = self.registry('protocollo.registry')
        self.modelProtSendRec = self.registry('protocollo.sender_receiver')
        self.modeldossier = self.registry('protocollo.dossier')
        self.modeldocsearch = self.registry('gedoc.document.search')
        self.modelHrDepartmentCollaborator = \
            self.registry('hr.department.collaborator')
        self.thread_model = self.registry('mail.thread')
        self.message_model = self.registry('mail.message')
        self.mail_model = self.registry('mail.mail')
        self.fetchmail_model = self.registry('fetchmail.server')
        self.compose_msg_model = self.registry('mail.compose.message')
        self.pecWizard = self.registry('protocollo.pec.wizard')
        self.cancelWizard = self.registry('protocollo.cancel.wizard')
        self.modifyWizard = self.registry('protocollo.modify.wizard')
        self.pecModifyWizard = self.registry('protocollo.modify.pec.wizard')
        self.pecModifyReceiverWizard = self.registry(
            'protocollo.sender_receiver.pec.wizard'
        )

        self.wf_service = netsvc.LocalService("workflow")

        # this is needed to avoid emails being actually sent
        threading.currentThread().testing = True

    def tearDown(self):
        # Remove fake docs
        self.delCopyOfFiles('test_doc_src.pdf')
        super(TestProtocolloBase, self).tearDown()
