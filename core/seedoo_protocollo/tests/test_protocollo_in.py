# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp import SUPERUSER_ID
import openerp.modules as addons

from openerp import netsvc
from openerp.osv import fields
from openerp.osv.orm import except_orm
from test_protocollo_base import TestProtocolloBase
from openerp.tools.translate import _

from openerp.osv import orm
import datetime
from lxml import etree
import os
from openerp import tools


class TestProtocolloIn(TestProtocolloBase):
    def receivePec(self):
        cr = self.cr
        msg = self.getPecFile('message1')
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

    def run_pecIN_wizard(self, classification, context):
        cr, uid = self.cr, self.uid
        wizard_id = self.pecWizard.create(
            cr, uid,
            {
                'classification': classification
            }, context=context
        )
        return self.pecWizard.action_save(
            cr, uid, [wizard_id], context=context)

    def get_next_number_normal(self, cr, uid, prot):
        pooler = prot.pool
        protocolloObj = pooler.get("protocollo.protocollo")
        sequence_obj = pooler.get('ir.sequence')
        last_id = protocolloObj.search(cr, uid,
                                       [('state', 'in',
                                         ('registered', 'notified', 'sent',
                                          'waiting', 'error', 'canceled'))
                                        ],
                                       limit=1,
                                       order='registration_date desc'
                                       )
        if last_id:
            now = datetime.datetime.now()
            last = protocolloObj.browse(cr, uid, last_id[0])
            if last.registration_date[0:4] < str(now.year):
                seq_id = sequence_obj.search(
                    cr, uid,
                    [
                        ('code', '=', prot.registry.sequence.code)
                    ])
                sequence_obj.write(cr,
                                   SUPERUSER_ID,
                                   seq_id,
                                   {'number_next': 1}
                                   )
        next_num = sequence_obj.get(cr,
                                    uid,
                                    prot.registry.sequence.code) or None
        if not next_num:
            raise orm.except_orm(_('Errore'),
                                 _('Il sistema ha riscontrato un errore \
                                 nel reperimento del numero protocollo'))
        return next_num

    def get_next_number_emergency(self, cr, uid, prot):
        pooler = prot.pool
        emergency_registry_obj = pooler.get('protocollo.emergency.registry')
        reg_ids = emergency_registry_obj.search(cr,
                                                uid,
                                                [('state', '=', 'draft')]
                                                )
        if len(reg_ids) > 0:
            er = emergency_registry_obj.browse(cr, uid, reg_ids[0])
            num = 0
            for enum in er.emergency_ids:
                if not enum.protocol_id:
                    num = enum.name
                    pooler.get('protocollo.emergency.registry.line'). \
                        write(cr, uid, [enum.id], {'protocol_id': prot.id})
                    break
            reg_available = [e.id for e in er.emergency_ids
                             if not e.protocol_id]
            if len(reg_available) < 2:
                emergency_registry_obj.write(cr,
                                             uid,
                                             [er.id],
                                             {'state': 'closed'}
                                             )
            return num
        else:
            raise orm.except_orm(_('Errore'),
                                 _('Il sistema ha riscontrato un errore \
                                 nel reperimento del numero protocollo'))

    def get_next_number(self, cr, uid, prot):
        if prot.registration_type == 'emergency':
            return self.get_next_number_emergency(cr, uid, prot)
        # FIXME what if the emergency is the 31 december
        # and we protocol the 1 january
        return self.get_next_number_normal(cr, uid, prot)

    def test_0_prot_pdf_in(self):
        """
        Testing receive pdf File and protocol it
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
        self.assertTrue(bool(prot_id))
        prot_obj = self.modelProtocollo.browse(cr, uid, prot_id)
        self.assertEqual(prot_obj.state, 'draft')
        self.assertEqual(prot_obj.fingerprint, False)
        self.wf_service.trg_validate(
            uid, 'protocollo.protocollo', prot_id, 'register', cr)
        prot_obj.refresh()
        self.assertEqual(prot_obj.state, 'registered')

        nextProtNumber = self.get_next_number(cr, uid, prot_obj)
        nextProtNumber = int(nextProtNumber) - 1
        # prot_name = 'Protocollo_0000001_%d' % prot_obj.year
        prot_name = 'Protocollo_%07d_%d' % (nextProtNumber, prot_obj.year)
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

    def test_1_prot_pec_in(self):
        """Testing received a pec mail and registred """
        cr, uid = self.cr, self.uid
        self.receivePec()
        com_varie_id = self.getIdDemoObj(
            'seedoo_gedoc', 'protocollo_classification_6')
        context = {'pec_messages': True}
        pec_todo = self.message_model.search(
            cr, uid,
            [
                ('server_id.pec', '=', True),
                ('pec_type', '=', 'posta-certificata'),
                ('server_id.user_ids', 'in', uid),
                ('pec_state', '=', 'new')

            ], context=context
        )
        pec_id = pec_todo[0]
        context['active_id'] = pec_id
        res = self.run_pecIN_wizard(com_varie_id, context)
        prot_id = res['res_id']
        prot_obj = self.modelProtocollo.browse(cr, uid, prot_id)
        self.assertEqual(prot_obj.state, 'draft')
        self.assertEqual(prot_obj.fingerprint, False)
        self.wf_service.trg_validate(
            uid, 'protocollo.protocollo', prot_id, 'register', cr)
        prot_obj = self.modelProtocollo.browse(cr, uid, prot_id)
        self.assertEqual(prot_obj.state, 'registered')

        nextProtNumber = self.get_next_number(cr, uid, prot_obj)
        nextProtNumber = int(nextProtNumber) - 1
        prot_name = 'Protocollo_%07d_%d.eml' % (nextProtNumber, prot_obj.year)
        self.assertEqual(prot_obj.doc_id.name, prot_name)

    def test_2_prot_assigne_in(self):
        """Testing change state notification"""
        cr, uid = self.cr, self.uid
        generic_dept_id = self.getIdDemoObj('', 'generic_dept')
        prot_id = self.modelProtocollo.search(
            cr, uid, [('name', '=', '0000001')]
        )[0]
        # Here we test the workflow trigger for the assigne;
        # when a registered protocol is updated with an assigne
        # (at least an office or a user) then the protocol state
        # is set to notified
        self.modelProtocollo.write(
            cr, SUPERUSER_ID, prot_id,
            {
                'assigne': [(6, 0, [generic_dept_id])],
            }
        )
        prot_obj = self.modelProtocollo.browse(cr, uid, prot_id)
        self.assertEqual(prot_obj.state, 'notified')
        self.assertEqual(prot_obj.assigne_emails,
                         'protocollo_user@example.com')

    def test_3_prot_visibility_in(self):
        cr, uid = self.cr, self.uid
        # user without visibility
        prot_ids = self.modelProtocollo.search(
            cr, uid, [('name', '=', '0000001'),
                      ('is_visible', '=', True)]
        )
        self.assertEqual(prot_ids, [])
        # user with visibility
        user_id = self.getIdDemoObj('', 'protocollo_user')
        prot_ids = self.modelProtocollo.search(
            cr, user_id, [('is_visible', '=', True)]
        )
        self.assertEqual(len(prot_ids), 1)

    def test_4_delete_prot_pdf_in(self):
        cr, uid = self.cr, self.uid
        racc_id = self.getIdDemoObj('', 'protocollo_typology_rac')
        com_varie_id = self.getIdDemoObj('seedoo_gedoc',
                                         'protocollo_classification_6')
        send_rec_id = self.modelProtSendRec.search(
            cr, uid, [('name', '=', 'test_partner')])[0]
        prot_id = self.modelProtocollo.create(
            cr, uid,
            {
                'type': 'in',
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
        # as admin can delete only in draft state!
        self.modelProtocollo.unlink(cr, self.admin, [prot_id])

    def test_5_prot_partner_duplication(self):
        """
            Test duplicazione partner
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
                'partner_id': partner_id,
                'save_partner': True
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
                'datas_fname': 'test5',
                'datas': self.getCopyOfFile('test5', 'test_doc_src.pdf')[1],
                'mimetype': 'application/pdf'
            }
        )
        self.assertTrue(bool(prot_id))
        prot_obj = self.modelProtocollo.browse(cr, uid, prot_id)
        self.assertEqual(prot_obj.state, 'draft')
        self.assertEqual(prot_obj.fingerprint, False)
        # Il sistema deve sollevare una eccezione perchè si sta
        # provando a creare un partner da riga mittente del protocollo
        # ma il partner è già presente in anagrafica e viene richiamato
        # nel campo partner_id
        with self.assertRaises(except_orm):
            self.wf_service.trg_validate(
                uid, 'protocollo.protocollo',
                prot_id, 'register', cr
            )
            # questo test diretto dell'azione register del protocollo non
            # compromette i test successivi in quanto e' l'ultimo del modulo

    def test_6_document_search(self):
        """
            Test Gedoc Extension
        """
        cr, uid = self.cr, self.uid
        context = {
            'lang': 'en_US',
            'tz': False,
            'uid': uid,
        }
        classification_id = self.getIdDemoObj(
            'seedoo_gedoc', 'protocollo_classification_8')
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
                'user_id': uid,
                'paperless': True
            },
            context=context
        )
        dossier = self.modeldossier.browse(
            cr, uid, dossier_id)
        dossier.refresh()
        self.assertTrue(dossier.state, 'draft')
        prot_id = self.modelProtocollo.search(
            cr, uid, [('name', '=', '0000001')]
        )[0]
        # is set to notified
        self.modelProtocollo.write(
            cr, uid, prot_id,
            {
                'dossier_ids': [(6, 0, [dossier_id])],
            }
        )
        self.assertTrue(dossier.state, 'open')
        # Search Docs
        doc_search_id = self.modeldocsearch.create(
            cr,
            uid,
            {
                'name': 'protocollo.protocollo',
                'dossier_id': dossier_id
            },
            context=context
        )
        res = self.modeldocsearch.search_action(
            cr, uid, [doc_search_id], context=context)
        self.assertEqual(
            res['domain'],
            "[('id', 'in', (%s,))]" % prot_id
        )
        self.modeldocsearch.write(
            cr,
            uid,
            doc_search_id,
            {
                'classification_id': classification_id
            },
            context=context
        )
        res = self.modeldocsearch.search_action(
            cr, uid, [doc_search_id], context=context)
        self.assertNotEqual(
            res['domain'],
            "[('id', 'in', (%s,))]" % prot_id
        )
        classification2_id = self.getIdDemoObj(
            'seedoo_gedoc', 'protocollo_classification_6')
        self.modeldocsearch.write(
            cr,
            uid,
            doc_search_id,
            {
                'classification_id': classification2_id
            },
            context=context
        )
        res = self.modeldocsearch.search_action(
            cr, uid, [doc_search_id], context=context)
        self.assertEqual(
            res['domain'],
            "[('id', 'in', (%s,))]" % prot_id
        )
