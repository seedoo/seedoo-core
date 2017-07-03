# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp import exceptions
import openerp.modules as addons
from openerp import netsvc
from openerp.osv.orm import except_orm
from test_protocollo_base import TestProtocolloBase
from lxml import etree
import os
from openerp import tools


class TestProtocolloOut(TestProtocolloBase):
    """
        SMTP Server MockObj
    """

    def _mock_smtp_gateway(self, *args, **kwargs):
        return args[2]['Message-Id']

    def wkf_register_prot(self):
        self.wf_service.trg_validate(
            self.uid, 'protocollo.protocollo',
            self._prot_id, 'register', self.cr
        )

    def wkf_send_prot(self):
        self.wf_service.trg_validate(
            self.uid, 'protocollo.protocollo',
            self._prot_id, 'sent', self.cr
        )

    def receiveAcceptancePec(self):
        cr = self.cr
        msg = self.getPecFile('acceptance1')
        context = {
            'lang': 'en_US',
            'tz': False,
            'uid': 1,
            'fetchmail_cron_running': True,
            'server_type': u'imap',
            'fetchmail_server_id': 1,
        }
        self.thread_model.message_process(
            cr, 1, None, msg, save_original=False, strip_attachments=False,
            context=context)

    def receiveDeliveryPec(self):
        cr = self.cr
        msg = self.getPecFile('delivery1')
        context = {
            'lang': 'en_US',
            'tz': False,
            'uid': 1,
            'fetchmail_cron_running': True,
            'server_type': u'imap',
            'fetchmail_server_id': 1,
        }
        self.thread_model.message_process(
            cr, 1, None, msg, save_original=False, strip_attachments=False,
            context=context)

    def setUp(self):
        super(TestProtocolloOut, self).setUp()

        # Install mock SMTP gateway
        self._send_email = self.registry('ir.mail_server').send_email
        self.registry('ir.mail_server').send_email = self._mock_smtp_gateway

    def test_0_prot_pdf_out(self):
        """
        Testing send pdf File and protocol it
        with signature as typology_rac
        """
        cr, uid = self.cr, self.uid
        partner_id = self.getIdDemoObj('base', 'main_partner')
        racc_id = self.getIdDemoObj('', 'protocollo_typology_rac')
        com_varie_id = self.getIdDemoObj('seedoo_gedoc',
                                         'protocollo_classification_6')
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
                'type': 'out',
                'subject': 'test out',
                'typology': racc_id,
                'sender_receivers': [(4, send_rec_id)],
                'classification': com_varie_id,
                'datas_fname': 'test0',
                'datas': self.getCopyOfFile('test0', 'test_doc_src.pdf')[1],
                'mimetype': 'application/pdf'
            }
        )
        self.assertTrue(bool(prot_id))
        prot_obj = self.modelProtocollo.browse(cr, uid, prot_id)
        self.assertEqual(prot_obj.state, 'draft')
        self.assertEqual(prot_obj.fingerprint, False)
        self.wf_service.trg_validate(
            uid, 'protocollo.protocollo', prot_id, 'register', cr)
        prot_obj.refresh()
        self.assertEqual(prot_obj.state, 'registered')
        prot_name = 'Protocollo_0000001_%d' % prot_obj.year
        self.assertEqual(prot_obj.doc_id.name, prot_name)
        sha1 = self.sha1OfFile(prot_obj.doc_id.id)
        self.assertEqual(prot_obj.fingerprint, sha1)
        self.assertTrue(prot_obj.xml_signature)
        path = addons.get_module_resource('seedoo_protocollo',
                                          'data', "segnatura.dtd")
        dtdPath = os.path.dirname(path) + "/segnatura.dtd"
        dtdfile = open(dtdPath, 'r')
        dtd = etree.DTD(dtdfile)
        signature_xml = etree.XML(prot_obj.xml_signature)
        self.assertTrue(dtd.validate(signature_xml))

    def test_1_prot_assigne_out(self):
        """Testing assignee for sent protocol"""
        cr, uid = self.cr, self.uid
        generic_dept_id = self.getIdDemoObj('', 'generic_dept')
        prot_id = self.modelProtocollo.search(
            cr, uid, [('name', '=', '0000001')]
        )[0]
        self.modelProtocollo.write(
            cr, uid, prot_id,
            {
                'assigne': [(6, 0, [generic_dept_id])],
            }
        )
        prot_obj = self.modelProtocollo.browse(cr, uid, prot_id)
        self.assertEqual(prot_obj.assigne_emails,
                         'protocollo_user@example.com')

    def test_2_prot_visibility_out(self):
        cr, uid = self.cr, self.uid
        # user without visibility
        prot_ids = self.modelProtocollo.search(
            cr, uid, [('name', '=', '0000001'),
                      ('is_visible', '=', True)]
        )
        self.assertEqual(prot_ids, [])
        # send protocol
        prot_id = self.modelProtocollo.search(
            cr, uid, [('name', '=', '0000001')]
        )[0]
        prot_obj = self.modelProtocollo.browse(cr, uid, prot_id)
        self.wf_service.trg_validate(
            uid, 'protocollo.protocollo', prot_id, 'sent', cr)
        prot_obj.refresh()
        self.assertEqual(prot_obj.state, 'sent')
        # user with visibility
        user_id = self.getIdDemoObj('', 'protocollo_user')
        prot_ids = self.modelProtocollo.search(
            cr, user_id, [('is_visible', '=', True)]
        )
        self.assertEqual(len(prot_ids), 1)

    def test_3_delete_prot_pdf_out(self):
        cr, uid = self.cr, self.uid
        racc_id = self.getIdDemoObj('', 'protocollo_typology_rac')
        com_varie_id = self.getIdDemoObj('seedoo_gedoc',
                                         'protocollo_classification_6')
        send_rec_id = self.modelProtSendRec.search(
            cr, uid, [('name', '=', 'test_partner')])[0]
        prot_id = self.modelProtocollo.create(
            cr, uid,
            {
                'type': 'out',
                'subject': 'test 4',
                'typology': racc_id,
                'sender_receivers': [(4, send_rec_id)],
                'classification': com_varie_id,
                'datas_fname': 'test4',
                'datas': self.getCopyOfFile('test4', 'test_doc_src.pdf')[1],
                'mimetype': 'application/pdf'
            }
        )
        prot_obj = self.modelProtocollo.browse(cr, uid, prot_id)
        self.assertEqual(prot_obj.state, 'draft')
        # as uid is protocollo_manager
        self.assertRaises(except_orm, prot_obj.unlink)
        # as admin can delete
        self.modelProtocollo.unlink(cr, self.admin, [prot_id])

    def test_4_prot_pec_out(self):
        """
        Testing send pec mail with protocol
        """
        cr, uid = self.cr, self.uid
        partner_id = self.getIdDemoObj('base', 'main_partner')
        pec_id = self.getIdDemoObj('', 'protocollo_typology_pec')
        com_varie_id = self.getIdDemoObj('seedoo_gedoc',
                                         'protocollo_classification_6')
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
                'type': 'out',
                'subject': 'test pec out',
                'body': 'Best regards',
                'typology': pec_id,
                'sender_receivers': [(4, send_rec_id)],
                'classification': com_varie_id,
                'datas_fname': 'test0',
                'datas': self.getCopyOfFile('test0', 'test_doc_src.pdf')[1],
                'mimetype': 'application/pdf'
            }
        )
        self.assertTrue(bool(prot_id))
        self._prot_id = prot_id
        prot_obj = self.modelProtocollo.browse(cr, uid, prot_id)
        self.assertEqual(prot_obj.state, 'draft')
        self.assertEqual(prot_obj.fingerprint, False)
        # Testa la presenza della mail pec del destinatario
        with self.assertRaises(exceptions.Warning):
            self.modelProtocollo.action_register(cr, uid, [prot_id])
        prot_obj.refresh()
        self.assertEqual(prot_obj.state, 'draft')

    def test_5_prot_pec_out(self):
        """
            Testing registration with receiver with pec mail set
            and sets protocol to waiting state (pec sent)
        """
        cr, uid = self.cr, self.uid
        prot_id = self.modelProtocollo.search(
            cr, uid, [('type', '=', 'out'),
                      ('subject', '=', 'test pec out')]
        )[0]
        prot_obj = self.modelProtocollo.browse(cr, uid, prot_id)
        self.modelProtSendRec.write(
            cr, uid, prot_obj.sender_receivers[0].id,
            {
                'pec_mail': 'test@pec.it',
            })
        prot_obj.refresh()
        self.wf_service.trg_validate(
            uid, 'protocollo.protocollo',
            prot_id, 'register', cr
        )
        prot_obj.refresh()
        self.assertEqual(prot_obj.state, 'registered')
        prot_name = 'Protocollo_0000002_%d' % prot_obj.year
        self.assertEqual(prot_obj.doc_id.name, prot_name)
        sha1 = self.sha1OfFile(prot_obj.doc_id.id)
        self.assertEqual(prot_obj.fingerprint, sha1)
        self.assertFalse(prot_obj.mail_out_ref.id)
        self.wf_service.trg_validate(
            uid, 'protocollo.protocollo',
            prot_id, 'sent_pec', cr
        )
        prot_obj.refresh()
        self.assertEqual(prot_obj.state, 'waiting')
        self.assertTrue(prot_obj.mail_out_ref.id)

    def test_6_prot_resend_pec_out(self):
        """
            Testing pec mail resend
        """
        cr, uid = self.cr, self.uid
        prot_id = self.modelProtocollo.search(
            cr, uid, [('type', '=', 'out'),
                      ('subject', '=', 'test pec out')]
        )[0]
        prot_obj = self.modelProtocollo.browse(cr, uid, prot_id)
        self.assertEqual(len(prot_obj.history_ids), 0)
        old_pec_id = prot_obj.mail_out_ref.id
        context = {'active_id': prot_id}
        wizard_id = self.pecModifyWizard.create(
            cr, uid, {}, context=context
        )
        self.pecModifyWizard.action_resend(
            cr, uid, [wizard_id], context=context
        )
        prot_obj.refresh()
        self.assertNotEqual(prot_obj.mail_out_ref.id, old_pec_id)
        self.assertEqual(prot_obj.state, 'waiting')
        self.assertEqual(prot_obj.mail_out_ref.email_to, 'test@pec.it')
        old_pec_id = prot_obj.mail_out_ref.id
        wizard_id = self.pecModifyWizard.create(
            cr, uid, {}, context=context
        )
        wizard_obj = self.pecModifyWizard.browse(cr, uid,
                                                 wizard_id,
                                                 context=context
                                                 )
        self.pecModifyReceiverWizard.write(
            cr, uid,
            wizard_obj.sender_receivers[0].id,
            {'pec_mail': 'innoviu.test1@legalmail.it'},
            context=context
        )
        self.pecModifyWizard.write(
            cr, uid, wizard_id,
            {
                'cause': 'The mail of the receiver was wrong!'
            },
            context=context
        )
        self.pecModifyWizard.action_save(
            cr, uid, [wizard_id], context=context
        )
        prot_obj.refresh()
        self.assertNotEqual(prot_obj.mail_out_ref.id, old_pec_id)
        self.assertEqual(prot_obj.state, 'waiting')
        self.assertEqual(prot_obj.mail_out_ref.email_to,
                         'innoviu.test1@legalmail.it')
        self.assertEqual(len(prot_obj.history_ids), 1)
        self.assertEqual(prot_obj.history_ids[0].type,
                         'modify')
        self.assertEqual(prot_obj.history_ids[0].description,
                         'The mail of the receiver was wrong!')
        self.assertNotEqual(prot_obj.history_ids[0].before,
                            prot_obj.history_ids[0].after)

    def test_7_prot_trigger_pec_out(self):
        """
            Test protocol wf with pec notifications
        """
        cr, uid = self.cr, self.uid

        # Set ir.config_parameter for env Test
        res_user = self.registry('res.users')
        res_user_obj = res_user.browse(cr, uid, uid)
        alias_id = res_user_obj.alias_id.id

        mail_alias = self.registry('mail.alias')
        mail_alias.write(self.cr, self.uid, alias_id,
                         {'alias_name': 'info'})

        prot_id = self.modelProtocollo.search(
            cr, uid, [('type', '=', 'out'),
                      ('subject', '=', 'test pec out')]
        )[0]
        prot_obj = self.modelProtocollo.browse(cr, uid, prot_id)
        self.assertEqual(prot_obj.state, 'waiting')
        # update message_id to link notifications
        mail_message_id = prot_obj.mail_pec_ref.id
        self.message_model.write(
            cr, uid, mail_message_id,
            {
                'message_id':
                    '<1432134489.558327913284302.165667473553067-openerp-private@roberto-ubuntu12>'
            }
        )
        self.receiveAcceptancePec()
        prot_obj.refresh()
        self.assertEqual(len(prot_obj.pec_notifications_ids), 1)
        self.assertEqual(prot_obj.state, 'waiting')
        self.receiveDeliveryPec()
        prot_obj.refresh()
        self.assertEqual(len(prot_obj.pec_notifications_ids), 2)
        # todo vedere meglio la configurazione delle mail 
        # todo verificare prot_obj.state, 'sent'

    def tearDown(self):
        # Remove mocks
        self.registry('ir.mail_server').send_email = self._send_email
        super(TestProtocolloOut, self).tearDown()
