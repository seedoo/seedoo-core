# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.
import base64
import logging

from openerp import SUPERUSER_ID
from openerp.osv import fields, osv
from utility.conversion import ConversionUtility
from lxml import etree
from ..segnatura.segnatura_xml_parser import SegnaturaXMLParser
_logger = logging.getLogger(__name__)


class protocollo_sender_receiver_wizard(osv.TransientModel):
    _name = 'protocollo.sender_receiver.wizard'

    def on_change_partner(self, cr, uid, ids, partner_id, context=None):
        values = {}
        if partner_id:
            partner = self.pool.get('res.partner'). \
                browse(cr, uid, partner_id, context=context)
            values = {
                'type': partner.is_company and 'individual' or 'legal',
                'name': partner.name,
                'street': partner.street,
                'city': partner.city,
                'country_id': partner.country_id and
                              partner.country_id.id or False,
                'email_from': partner.email,
                'phone': partner.phone,
                'mobile': partner.mobile,
                'fax': partner.fax,
                'zip': partner.zip,
            }
        return {'value': values}

    _columns = {
        # TODO: inserire anche AOO in type?
        'wizard_id': fields.many2one('protocollo.pec.wizard',
                                     'Crea Protocollo'),
        'type': fields.selection([
            ('individual', 'Persona Fisica'),
            ('legal', 'Persona Giuridica'),
        ],
            'Tipologia',
            size=32,
            required=True,
        ),
        'partner_id': fields.many2one('res.partner', 'Anagrafica'),
        'name': fields.char('Nome Cognome/Ragione Sociale',
                            size=512,
                            required=True),
        'street': fields.char('Via/Piazza num civico', size=128),
        'zip': fields.char('Cap', change_default=True, size=24),
        'city': fields.char('Citta\'', size=128),
        'country_id': fields.many2one('res.country', 'Paese'),
        'email': fields.char('Email', size=240),
        'pec_mail': fields.char('PEC', size=240, required=True, readonly=True),
        'phone': fields.char('Telefono', size=64),
        'fax': fields.char('Fax', size=64),
        'mobile': fields.char('Cellulare', size=64),
        'notes': fields.text('Note'),
        'send_type': fields.many2one('protocollo.typology',
                                     'Mezzo di Spedizione'
                                     ),
        'send_date': fields.date('Data Spedizione'),
    }


class ProtocolloPecWizard(osv.TransientModel):
    """
        A wizard to manage the creation of
        document protocollo from pec message
    """
    _name = 'protocollo.pec.wizard'
    _description = 'Create Protocollo From PEC'
    _rec_name = 'subject'

    DOC_PRINCIPALE_SELECTION = [('testo', 'Testo del messaggio'), ('eml', 'File Eml'), ('allegato', 'Allegato')]

    _columns = {
        'subject': fields.text('Oggetto',
                               required=True, readonly=True),
        'body': fields.html('Corpo della mail', readonly=True),
        'receiving_date': fields.datetime(
            'Data Ricezione',
            required=True,
            readonly=True),
        'message_id': fields.integer('Id',
                                     required=True, readonly=True),
        'select_doc_principale': fields.selection(DOC_PRINCIPALE_SELECTION, 'Seleziona il documento principale',
                                                  select=True,
                                                  required=True),
        'doc_principale': fields.many2one('ir.attachment', 'Allegato',
                                          domain="[('datas_fname', '=', 'original_email.eml')]"),

        'is_attach_message': fields.related('ir.attachment', 'doc_principale', type='boolean',
                                            string="Author's Avatar"),
        'doc_fname': fields.related('doc_principale', 'datas_fname', type='char', readonly=True),
        'sender_receivers': fields.one2many(
            'protocollo.sender_receiver.wizard',
            'wizard_id',
            'Mittenti/Destinatari',
            required=True,
            limit=1),
        # 'dossier_ids': fields.many2many(
        #     'protocollo.dossier',
        #     'dossier_protocollo_pec_rel',
        #     'wizard_id', 'dossier_id',
        #     'Fascicoli'),
        # TODO: insert assigne here
        # 'notes': fields.text('Note'),
    }

    # def _default_doc_principale(self, cr, uid, context):
    #     id = 0
    #     mail_message = self.pool.get('mail.message').browse(cr, uid, context['active_id'], context=context)
    #     for attach in mail_message.attachment_ids:
    #         if attach.name == 'original_email.eml':
    #             id = attach.id
    #     return id

    def _default_subject(self, cr, uid, context):
        mail_message = self.pool.get('mail.message').browse(cr, uid, context['active_id'], context=context)
        return mail_message.subject

    def _default_id(self, cr, uid, context):
        mail_message = self.pool.get('mail.message').browse(cr, uid, context['active_id'], context=context)
        return mail_message.id

    def _default_receiving_date(self, cr, uid, context):
        mail_message = self.pool.get('mail.message').browse(cr, uid, context['active_id'], context=context)
        # TODO: to verify
        return mail_message.date

    def _default_body(self, cr, uid, context):
        mail_message = self.pool.get('mail.message').browse(cr, uid, context['active_id'], context=context)
        return mail_message.body

    def _default_sender_receivers(self, cr, uid, context):
        mail_message = self.pool.get('mail.message').browse(cr, uid, context['active_id'], context=context)
        partner = mail_message.author_id
        res = []
        if partner:
            res.append({
                'partner_id': partner.id,
                'type': partner.is_company and 'legal' or 'individual',
                'name': partner.name,
                'street': partner.street,
                'zip': partner.zip,
                'city': partner.city,
                'country_id': partner.country_id.id,
                'email': partner.email,
                'phone': partner.phone,
                'fax': partner.fax,
                'mobile': partner.mobile,
                'pec_mail': mail_message.email_from
            })
        else:
            res.append({
                'name': mail_message.email_from,
                'pec_mail': mail_message.email_from,
                'type': 'individual',
            })
        return res

    _defaults = {
        'subject': _default_subject,
        'message_id': _default_id,
        'receiving_date': _default_receiving_date,
        'body': _default_body,
        'sender_receivers': _default_sender_receivers,
        'select_doc_principale': 'testo',
        # 'doc_principale': _default_doc_principale,
    }

    def action_save(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids[0], context=context)
        protocollo_obj = self.pool.get('protocollo.protocollo')
        sender_receiver_obj = self.pool.get('protocollo.sender_receiver')
        ir_attachment_obj = self.pool.get('ir.attachment')
        protocollo_typology_obj = self.pool.get('protocollo.typology')
        typology_id = protocollo_typology_obj.search(cr, uid,
                                                     [('pec', '=', True)]
                                                     )[0]
        mail_message_obj = self.pool.get('mail.message')
        mail_message = mail_message_obj.browse(cr, uid,
                                               context['active_id'],
                                               context=context)
        vals = {}
        vals['type'] = 'in'
        vals['typology'] = typology_id
        vals['receiving_date'] = wizard.receiving_date
        vals['subject'] = wizard.subject
        vals['body'] = wizard.body
        vals['mail_pec_ref'] = context['active_id']
        vals['user_id'] = uid
        sender_receiver = []

        for attach in mail_message.attachment_ids:
            if attach.name.lower() == 'segnatura.xml':
                vals_receiver = {}
                location = self.pool.get('ir.config_parameter').get_param(cr, uid, 'ir_attachment.location')
                attach_path = protocollo_obj._full_path(cr, uid, location, attach.store_fname)
                segnatura_xml = SegnaturaXMLParser(attach_path)

                srvals = {
                    'type': segnatura_xml.getTipoMittente(),
                    'pa_type': segnatura_xml.getTipoAmministrazione(),
                    'source': 'sender',
                    'partner_id': False,
                    'name': segnatura_xml.getDenominazioneCompleta(),
                    'street': segnatura_xml.getToponimo(),
                    'zip': segnatura_xml.getCAP(),
                    'city': segnatura_xml.getComune(),
                    'country_id': False,
                    'email': segnatura_xml.getIndirizzoTelematico(),
                    'pec_mail': mail_message.email_from,
                    'phone': segnatura_xml.getTelefono(),
                    'fax': segnatura_xml.getFax(),
                }

                tipo = segnatura_xml.getTipoAmministrazione()
                if tipo == 'uo':
                    srvals['ipa_code'] = segnatura_xml.getCodiceUnitaOrganizzativa()
                if tipo == 'aoo':
                    srvals['ident_code'] = segnatura_xml.getCodiceAOO()
                if tipo == 'pa':
                    srvals['amm_code'] = segnatura_xml.getCodiceAmministrazione()

                sender_receiver.append(sender_receiver_obj.create(cr, uid, srvals))
                vals['sender_receivers'] = [[6, 0, sender_receiver]]


        protocollo_id = protocollo_obj.create(cr, uid, vals)
        self.pool.get('mail.message').write(
            cr,
            SUPERUSER_ID,
            context['active_id'],
            {'pec_state': 'protocol','pec_protocol_ref': protocollo_id},
            context=context
        )

        new_context = dict(context).copy()
        new_context.update({'is_pec_to_draft': True})

        action_class = "history_icon print"
        post_vars = {'subject': "Creata Bozza Protocollo",
                     'body': "<div class='%s'><ul><li>Messaggio PEC convertito in bozza di protocollo</li></ul></div>" % action_class,
                     'model': "protocollo.protocollo",
                     'res_id': context['active_id'],
                     }

        thread_pool = self.pool.get('protocollo.protocollo')
        thread_pool.message_post(cr, uid, protocollo_id, type="notification", context=new_context, **post_vars)

        # Attachments
        file_data_list = []

        body_pdf_content = base64.b64encode(ConversionUtility.html_to_pdf(wizard.body))
        body_pdf_name = "mailbody.pdf"

        for attach in mail_message.attachment_ids:
            if attach.name == 'original_email.eml':
                if wizard.select_doc_principale == 'testo':
                    protocollo_obj.carica_documento_principale(cr,
                                                               uid,
                                                               protocollo_id,
                                                               body_pdf_content,
                                                               body_pdf_name,
                                                               "")
                else:
                    file_data_list.append({
                        'datas': body_pdf_content,
                        'datas_fname': body_pdf_name,
                        'datas_description': ''
                    })

                if wizard.select_doc_principale == 'eml':
                    protocollo_obj.carica_documento_principale(cr,
                                                               uid,
                                                               protocollo_id,
                                                               attach.datas,
                                                               attach.name,
                                                               "")
                else:
                    file_data_list.append({
                        'datas': attach.datas,
                        'datas_fname': attach.name,
                        'datas_description': ''
                    })

            else:
                if wizard.select_doc_principale == 'allegato' and attach.id == wizard.doc_principale.id:
                    if attach.datas and attach.name:
                        protocollo_obj.carica_documento_principale(cr,
                                                                   uid,
                                                                   protocollo_id,
                                                                   attach.datas,
                                                                   attach.name,
                                                                   "")
                else:
                    file_data_list.append({
                        'datas': attach.datas,
                        'datas_fname': attach.name,
                        'datas_description': ''
                    })

        if file_data_list:
            protocollo_obj.carica_documenti_secondari(cr, uid, protocollo_id, file_data_list)

        obj_model = self.pool.get('ir.model.data')
        model_data_ids = obj_model.search(
            cr,
            uid,
            [('model', '=', 'ir.ui.view'),
             ('name', '=', 'protocollo_protocollo_form')]
        )
        resource_id = obj_model.read(cr, uid,
                                     model_data_ids,
                                     fields=['res_id'])[0]['res_id']

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'protocollo.protocollo',
            'res_id': protocollo_id,
            'views': [(resource_id, 'form')],
            'type': 'ir.actions.act_window',
            'context': context,
        }
