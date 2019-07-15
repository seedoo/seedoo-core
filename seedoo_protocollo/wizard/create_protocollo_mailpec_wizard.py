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
import re
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
        'wizard_id': fields.many2one('protocollo.mailpec.wizard',
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
        'pec_mail': fields.char('PEC', size=240),
        'phone': fields.char('Telefono', size=64),
        'fax': fields.char('Fax', size=64),
        'mobile': fields.char('Cellulare', size=64),
        'notes': fields.text('Note'),
        'send_type': fields.many2one('protocollo.typology', 'Mezzo di Spedizione'),
        'send_date': fields.date('Data Spedizione'),
    }


class ProtocolloMailPecWizard(osv.TransientModel):
    """
        A wizard to manage the creation of
        document protocollo from mail or pec message
    """
    _name = 'protocollo.mailpec.wizard'
    _description = 'Create Protocollo From Mail or PEC'
    _rec_name = 'subject'

    def _get_doc_principale_option(self, cr, uid, context=None):
        options = []
        attach_lower_limit = 0
        configurazione_ids = self.pool.get('protocollo.configurazione').search(cr, uid, [])
        configurazione = self.pool.get('protocollo.configurazione').browse(cr, uid, configurazione_ids[0])
        message = None
        if context and context.has_key('active_id') and context['active_id']:
            message = self.pool.get('mail.message').browse(cr, uid, context['active_id'])

        if configurazione.select_body:
            options.append(('testo', 'Corpo del messaggio'))

        if message and message.eml and configurazione.select_eml:
            options.append(('eml', 'Intero messaggio (file EML)'))
            attach_lower_limit = 1 #al momento le PEC si includono anche l'attachment EML quindi il controllo parte da 1

        if 'attachment_ids' in context and len(context['attachment_ids'][0][2])>attach_lower_limit and configurazione.select_attachments:
            options.insert(0, ('allegato', 'Allegato'))

        return options

    def on_change_attachment(self, cr, uid, ids, attachment_id, context=None):
        values = {'preview': False}
        if attachment_id:
            ir_attachment = self.pool.get('ir.attachment').browse(cr, uid, attachment_id)
            for attach in ir_attachment:
                if attach.file_type == 'application/pdf':
                    values = {
                        'preview': attach.datas,
                    }
                return {'value': values}
        else:
            return None

    _columns = {
        'registration_employee_department_id': fields.many2one('hr.department', 'Il mio ufficio'),
        'registration_employee_department_id_invisible': fields.boolean('Campo registration_employee_department_id invisible', readonly=True),
        'subject': fields.text('Oggetto', readonly=True),
        'body': fields.html('Corpo della mail', readonly=True),
        'receiving_date': fields.datetime(
            'Data Ricezione',
            required=False,
            readonly=True),
        'message_id': fields.integer('Id',
                                     required=True, readonly=True),
        'select_doc_principale': fields.selection(_get_doc_principale_option, 'Seleziona il documento da protocollare',
                                                  select=True,
                                                  required=True),
        'doc_principale': fields.many2one('ir.attachment', 'Allegato',
                                          domain="[('datas_fname', '=', 'original_email.eml')]"),

        'is_attach_message': fields.related('ir.attachment', 'doc_principale', type='boolean',
                                            string="Author's Avatar"),
        'doc_fname': fields.related('doc_principale', 'datas_fname', type='char', readonly=True),
        'doc_description': fields.char('Descrizione documento', size=256, readonly=False),
        'preview': fields.binary('Anteprima allegato PDF'),
        'sender_receivers': fields.one2many(
            'protocollo.sender_receiver.wizard',
            'wizard_id',
            'Mittenti/Destinatari',
            required=True,
            limit=1),
        'documento_descrizione_required_wizard': fields.boolean('Descrizione documento obbligatorio', readonly=1)
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

    def _default_registration_employee_department_id(self, cr, uid, context):
        department_ids = self.pool.get('hr.department').search(cr, uid, [('can_used_to_protocol', '=', True)])
        if department_ids:
            return department_ids[0]
        return False

    def _default_registration_employee_department_id_invisible(self, cr, uid, context):
        department_ids = self.pool.get('hr.department').search(cr, uid, [('can_used_to_protocol', '=', True)])
        if len(department_ids) == 1:
            return True
        return False

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
        sr_substring = re.findall('<[^>]+>', mail_message.email_from)
        if len(sr_substring):
            sr_email = sr_substring[0].strip('<>')
            sr_name = mail_message.email_from.replace(sr_substring[0], '')
        else:
            sr_name = ''
            sr_email = mail_message.email_from

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
                'pec_mail': partner.pec_mail
            })
        elif 'message_type' in context and context['message_type'] == 'mail':
            res.append({
                'name': sr_name,
                'email': sr_email,
                'type': 'individual',
            })
        elif 'message_type' in context and context['message_type'] == 'pec':
            res.append({
                'name': sr_name,
                'pec_mail': sr_email,
                'type': 'individual',
            })
        return res

    def _default_documento_descrizione_wizard_required(self, cr, uid, context):
        configurazione_ids = self.pool.get('protocollo.configurazione').search(cr, uid, [])
        configurazione = self.pool.get('protocollo.configurazione').browse(cr, uid, configurazione_ids[0])
        return configurazione.documento_descrizione_required

    _defaults = {
        'registration_employee_department_id': _default_registration_employee_department_id,
        'registration_employee_department_id_invisible': _default_registration_employee_department_id_invisible,
        'subject': _default_subject,
        'message_id': _default_id,
        'receiving_date': _default_receiving_date,
        'body': _default_body,
        'sender_receivers': _default_sender_receivers,
        'documento_descrizione_required_wizard': _default_documento_descrizione_wizard_required
        # 'doc_principale': _default_doc_principale,
    }

    def action_save(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids[0], context=context)
        protocollo_obj = self.pool.get('protocollo.protocollo')
        sender_receiver_obj = self.pool.get('protocollo.sender_receiver')
        protocollo_typology_obj = self.pool.get('protocollo.typology')
        mail_message_obj = self.pool.get('mail.message')
        mail_message = mail_message_obj.browse(cr, uid, context['active_id'], context=context)
        employee = self.pool.get('hr.employee').get_department_employee(cr, uid, wizard.registration_employee_department_id.id)

        vals = {}
        vals['type'] = 'in'
        vals['receiving_date'] = wizard.receiving_date
        vals['subject'] = wizard.subject if wizard.select_doc_principale=='eml' else ''
        vals['body'] = wizard.body
        vals['mail_pec_ref'] = context['active_id']
        vals['user_id'] = uid
        vals['registration_employee_department_id'] = wizard.registration_employee_department_id.id
        vals['registration_employee_department_name'] = wizard.registration_employee_department_id.complete_name
        vals['registration_employee_id'] = employee.id
        vals['registration_employee_name'] = employee.name_related
        sender_receiver = []

        is_pec = False
        is_segnatura = False

        # Estrae i dati del mittente dalla segnatura
        configurazione_ids = self.pool.get('protocollo.configurazione').search(cr, uid, [])
        configurazione = self.pool.get('protocollo.configurazione').browse(cr, uid, configurazione_ids[0])

        if 'message_type' in context and context['message_type'] == 'pec':
            is_pec = True

        if is_pec:
            srvals = {}
            typology_id = protocollo_typology_obj.search(cr, uid, [('pec', '=', True)])[0]
            messaggio_pec_obj = self.pool.get('protocollo.messaggio.pec')
            messaggio_pec_id = messaggio_pec_obj.create(cr, uid, {'type': 'messaggio', 'messaggio_ref': mail_message.id})

            if configurazione.segnatura_xml_parse:
                srvals = self.elaboraSegnatura(cr, uid, protocollo_obj, mail_message)
            if len(srvals) > 0 and len(srvals['mittente']) > 0:
                is_segnatura = True

        sender_segnatura_xml_parse = configurazione.sender_segnatura_xml_parse

        if is_pec and is_segnatura:
            srvals['mittente']['pec_messaggio_ids'] = [[6, 0, [messaggio_pec_id]]]
            if sender_segnatura_xml_parse:
                sender_receiver.append(sender_receiver_obj.create(cr, uid, srvals['mittente']))

        if (is_pec and (is_segnatura is False or (is_segnatura and not sender_segnatura_xml_parse))) or is_pec is False:
            for send_rec in wizard.sender_receivers:
                srvals = {
                    'type': send_rec.type,
                    'source': 'sender',
                    'partner_id': send_rec.partner_id and send_rec.partner_id.id or False,
                    'name': send_rec.name,
                    'street': send_rec.street,
                    'zip': send_rec.zip,
                    'city': send_rec.city,
                    'country_id': send_rec.country_id and send_rec.country_id.id or False,
                    'phone': send_rec.phone,
                    'fax': send_rec.fax,
                    'mobile': send_rec.mobile,
                }

                if is_pec:
                    srvals['pec_mail'] = send_rec.pec_mail
                    srvals['pec_messaggio_ids'] = [[6, 0, [messaggio_pec_id]]]
                else:
                    srvals['pec_mail'] = ''
                    srvals['email'] = send_rec.email
                    srvals['sharedmail_messaggio_ids'] = [(4, context['active_id'])]

                sender_receiver.append(sender_receiver_obj.create(cr, uid, srvals))

        vals['sender_receivers'] = [[6, 0, sender_receiver]]
        if 'protocollo' in srvals:
            vals['sender_protocol'] = srvals['protocollo']['sender_protocol']
            vals['sender_register'] = srvals['protocollo']['sender_register']
            vals['sender_registration_date'] = srvals['protocollo']['sender_registration_date']

        if is_pec is False:
            typology_id = protocollo_typology_obj.search(cr, uid,[('sharedmail', '=', True)])[0]

        vals['typology'] = typology_id
        protocollo_id = protocollo_obj.create(cr, uid, vals)

        if is_pec:
            self.pool.get('mail.message').write(cr, SUPERUSER_ID, context['active_id'], {'pec_state': 'protocol', 'pec_protocol_ref': protocollo_id}, context=context)
        else:
            self.pool.get('mail.message').write(cr, SUPERUSER_ID, context['active_id'], {'sharedmail_state': 'protocol', 'sharedmail_protocol_ref': protocollo_id}, context=context)

        action_class = "history_icon print"
        post_vars = {'subject': "Creata Bozza Protocollo",
                     'body': "<div class='%s'><ul><li>Messaggio convertito in bozza di protocollo</li></ul></div>" % action_class,
                     'model': "protocollo.protocollo",
                     'res_id': context['active_id'],
                     }

        thread_pool = self.pool.get('protocollo.protocollo')
        thread_pool.message_post(cr, uid, protocollo_id, type="notification", context=context, **post_vars)

        # Attachments
        file_data_list = []

        body_pdf_content = base64.b64encode(ConversionUtility.html_to_pdf(wizard.body))
        body_pdf_name = "mailbody.pdf"

        if wizard.select_doc_principale == 'testo':
            protocollo_obj.carica_documento_principale(cr,
                                                       uid,
                                                       protocollo_id,
                                                       body_pdf_content,
                                                       body_pdf_name,
                                                       wizard.doc_description,
                                                       {'skip_check': True})
        else:
            file_data_list.append({
                'datas': body_pdf_content,
                'datas_fname': body_pdf_name,
                'datas_description': ''
            })

        for attach in mail_message.attachment_ids:
            if attach.name == 'original_email.eml':
                if wizard.select_doc_principale == 'eml':
                    protocollo_obj.carica_documento_principale(cr,
                                                               uid,
                                                               protocollo_id,
                                                               attach.datas,
                                                               attach.name,
                                                               wizard.doc_description,
                                                               {'skip_check': True})
            else:
                if wizard.select_doc_principale == 'allegato' and attach.id == wizard.doc_principale.id:
                    if attach.datas and attach.name:
                        protocollo_obj.carica_documento_principale(cr,
                                                                   uid,
                                                                   protocollo_id,
                                                                   attach.datas,
                                                                   attach.name,
                                                                   wizard.doc_description,
                                                                   {'skip_check': True})
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
        resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'protocollo.protocollo',
            'res_id': protocollo_id,
            'views': [(resource_id, 'form')],
            'type': 'ir.actions.act_window',
            'context': context,
            'flags': {'initial_mode': 'edit'}
        }

    def elaboraSegnatura(self, cr, uid, protocollo_obj, mail_message):
        srvals = {}
        srvals_mittente = {}
        srvals_protocollo = {}

        for attach in mail_message.attachment_ids:
            if attach.name.lower() == 'segnatura.xml':
                attach_path = self.pool.get('ir.attachment')._full_path(cr, uid, attach.store_fname)
                xml = open(attach_path, "rb").read()
                content_encode = xml.decode("latin").encode("utf8")
                tree = etree.fromstring(content_encode)
                segnatura_xml = SegnaturaXMLParser(tree)

                srvals_mittente = self.getDatiSegnaturaMittente(segnatura_xml)
                srvals_protocollo = self.getDatiSegnaturaProtocollo(segnatura_xml)

                srvals_mittente['pec_mail'] = mail_message.email_from.encode('utf8')

        srvals['mittente'] = srvals_mittente
        srvals['protocollo'] = srvals_protocollo
        return srvals

    def getDatiSegnaturaMittente(self, segnatura_xml):
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
            'phone': segnatura_xml.getTelefono(),
            'fax': segnatura_xml.getFax(),
            'ipa_code': segnatura_xml.getCodiceUnitaOrganizzativa(),
            'ident_code': segnatura_xml.getCodiceAOO(),
            'amm_code': segnatura_xml.getCodiceAmministrazione()
        }

        return srvals

    def getDatiSegnaturaProtocollo(self, segnatura_xml):
        srvals = {
            'sender_protocol': segnatura_xml.getNumeroRegistrazione(),
            'sender_register': segnatura_xml.getCodiceRegistro(),
            'sender_registration_date': segnatura_xml.getDataRegistrazione()
        }

        return srvals