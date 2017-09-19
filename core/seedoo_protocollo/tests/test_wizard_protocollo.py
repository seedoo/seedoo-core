# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp import addons, exceptions
from openerp import netsvc
from openerp.osv.orm import except_orm
# from openerp.addons.seedoo_protocollo.tests.test_protocollo_base import TestProtocolloBase
from test_protocollo_base import TestProtocolloBase


class TestWizardProtocolloOut(TestProtocolloBase):
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
        super(TestWizardProtocolloOut, self).setUp()

        # Install mock SMTP gateway
        self._send_email = self.registry('ir.mail_server').send_email
        self.registry('ir.mail_server').send_email = self._mock_smtp_gateway

    def test_0_prot_mod_subject(self):
        """
        Testing modification of a simple protocol
        """
        cr, uid = self.cr, self.uid
        partner_id = self.getIdDemoObj('base', 'main_partner')
        racc_id = self.getIdDemoObj('', 'protocollo_typology_rac')
        com_varie_id = self.getIdDemoObj(
            'seedoo_gedoc', 'protocollo_classification_6')
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
                'datas_fname': 'test2',
                'datas': self.getCopyOfFile('test2', 'test_doc_src.pdf')[1],
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
        # Testing modification starts here
        context = {'active_id': prot_id}
        vals = {
            'cause': 'Errore del Protocollatore',
            'subject': 'test out with mod'
        }
        wizard_id = self.modifyWizard.create(
            cr, uid, vals, context=context
        )
        self.modifyWizard.action_save(
            cr, uid, [wizard_id], context=context
        )
        prot_obj.refresh()
        self.assertEqual(prot_obj.state, 'registered')
        self.assertEqual(len(prot_obj.history_ids), 1)
        self.assertEqual(prot_obj.history_ids[0].type,
                         'modify')
        self.assertEqual(prot_obj.subject,
                         'test out with mod')
        self.assertEqual(prot_obj.history_ids[0].description,
                         'Errore del Protocollatore')
        self.assertNotEqual(prot_obj.history_ids[0].before,
                            prot_obj.history_ids[0].after)

    def test_1_prot_mod_typology(self):
        """
        Testing modification of the typology of a protocol
        """
        cr, uid = self.cr, self.uid
        email_id = self.getIdDemoObj('', 'protocollo_typology_email')
        pec_id = self.getIdDemoObj('', 'protocollo_typology_pec')
        prot_id = self.modelProtocollo.search(
            cr, uid, [('name', '=', '0000001')]
        )[0]
        prot_obj = self.modelProtocollo.browse(cr, uid, prot_id)
        context = {'active_id': prot_id}
        vals = {
            'cause': 'Errore del Protocollatore 2',
            'typology': email_id,
        }
        wizard_id = self.modifyWizard.create(
            cr, uid, vals, context=context
        )
        self.modifyWizard.action_save(
            cr, uid, [wizard_id], context=context
        )
        prot_obj.refresh()
        self.assertEqual(prot_obj.state, 'registered')
        self.assertEqual(prot_obj.typology.id, email_id)
        self.assertEqual(len(prot_obj.history_ids), 2)
        self.assertEqual(prot_obj.history_ids[1].type,
                         'modify')
        self.assertEqual(prot_obj.history_ids[1].description,
                         'Errore del Protocollatore 2')
        self.assertNotEqual(prot_obj.history_ids[1].before,
                            prot_obj.history_ids[1].after)
        # Test Pec Failure
        vals = {
            'cause': 'Errore del Protocollatore 3',
            'typology': pec_id,
        }
        wizard_id = self.modifyWizard.create(
            cr, uid, vals, context=context
        )

        try:
            self.modifyWizard.action_save(cr, uid, [wizard_id],
                                          context=context)
            self.assertTrue(False,
                            "Il metodo di spedizione PEC non puo essere inserito in questa fase.")
        except except_orm as e:
            self.assertEqual(e.value,
                             "Il metodo di spedizione PEC non puo' essere inserito in questa fase.",
                             e)

    def test_2_prot_cancel(self):
        """
        Testing cancel action for a protocol
        """
        cr, uid = self.cr, self.uid
        prot_id = self.modelProtocollo.search(
            cr, uid, [('name', '=', '0000001')]
        )[0]
        prot_obj = self.modelProtocollo.browse(cr, uid, prot_id)
        context = {'active_id': prot_id}
        vals = {
            'name': 'Errore del Protocollatore 3',
        }
        wizard_id = self.cancelWizard.create(
            cr, uid, vals, context=context
        )
        self.cancelWizard.action_cancel(
            cr, uid, [wizard_id], context=context
        )
        prot_obj.refresh()
        self.assertEqual(prot_obj.state, 'canceled')
        self.assertEqual(len(prot_obj.history_ids), 3)
        self.assertEqual(prot_obj.history_ids[2].type,
                         'cancel')
        self.assertEqual(prot_obj.history_ids[2].description,
                         'Errore del Protocollatore 3 - Autorizzato da: Protocollo manager')
