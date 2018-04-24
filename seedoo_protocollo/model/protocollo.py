# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.
import base64
import datetime
import logging
import mimetypes
import os
import re
import shutil
import string
import subprocess
import threading
import time

import magic
import pytz
from lxml import etree

import openerp.exceptions
from openerp import SUPERUSER_ID, api
from openerp import netsvc
from openerp.api import Environment
from openerp.osv import orm, fields, osv
from openerp.report import render_report
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DSDF
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DSDT, random
from openerp.tools.translate import _
from util.selection import *
from ..segnatura.annullamento_xml import AnnullamentoXML
from ..segnatura.conferma_xml import ConfermaXML
from ..segnatura.segnatura_xml import SegnaturaXML

_logger = logging.getLogger(__name__)
mimetypes.init()


class protocollo_typology(orm.Model):
    _name = 'protocollo.typology'

    _order = 'display_order, name'

    _columns = {
        'name': fields.char('Nome', size=256, required=True),
        'sharedmail': fields.boolean('Shared Mail'),
        'pec': fields.boolean('PEC'),
        'aoo_id': fields.many2one('protocollo.aoo', 'AOO', required=True),
        'display_order': fields.integer('Ordine visualizzazione')
    }

    _defaults = {
        'display_order': 100
    }


class protocollo_registry(orm.Model):
    _name = 'protocollo.registry'

    def _get_first_aoo_id(self, cr, uid, ids, field, arg, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        res = dict.fromkeys(ids, False)
        for registry in self.browse(cr, uid, ids):
            for aoo in registry.aoo_ids:
                res[registry.id] = aoo.id
                break
        return res

    _columns = {
        'name': fields.char('Nome Registro', char=256, required=True),
        'code': fields.char('Codice Registro', char=16, required=True),
        'description': fields.text('Descrizione Registro'),
        'sequence': fields.many2one('ir.sequence', 'Sequenza', required=True, readonly=True),
        'office_ids': fields.many2many('hr.department', 'protocollo_registry_office_rel', 'registry_id', 'office_id',
                                       'Uffici Abilitati'),
        # TODO check for company in registry and emergency registry
        'company_id': fields.many2one('res.company', 'Ente', required=True, readonly=True),
        'priority': fields.integer('Priorità Registro'),
        # 'allowed_users': fields.many2many(
        #    'res.users', 'registry_res_users_rel',
        #    'user_id', 'registryt_id', 'Allowed Users',
        #    required=True),
        'allowed_employee_ids': fields.many2many('hr.employee', 'protocollo_registry_hr_employee_rel',
                                                 'registry_id', 'employee_id', 'Dipendenti Abilitati'),
        'aoo_ids': fields.one2many('protocollo.aoo', 'registry_id', 'AOO'),
        'first_aoo_id': fields.function(_get_first_aoo_id, type='many2one', relation='protocollo.aoo', string='AOO'),
    }

    def get_registry_for_user(self, cr, uid):
        ids = self.search(cr, uid, [('allowed_users', 'in', [uid])])
        if ids:
            return ids[0]
        else:
            return []

    def assign_employee_to_registry(self, cr, uid, aoo_id, employee_id):
        aoo = self.pool.get('protocollo.aoo').browse(cr, uid, aoo_id)

        # if aoo and aoo.registry_id and aoo.registry_id.allowed_employee_ids:
        self.write(cr, uid, [aoo.registry_id.id], {'allowed_employee_ids':
                                                       [(6, 0, [employee_id[0]])],
                                                   })
        # self.write(cr, uid, [aoo.id], {'ident_code': '1'
        # })
        # for employee in aoo.registry_id.allowed_employee_ids:
        #     if employee.user_id and employee.user_id.id == user.id and self._office_check(cr, uid, user, aoo):
        #         return True
        return True

    def unlink(self, cr, uid, ids, context=None):
        reg = self.browse(cr, uid, ids, context=context)
        sequence_obj = self.pool.get('ir.sequence')
        sequence_type_obj = self.pool.get('ir.sequence.type')
        seq_id = reg.sequence.id
        seq_code = reg.sequence.code
        res = super(protocollo_registry, self).unlink(cr, uid, ids, context=context)
        if res:
            seq_type = sequence_type_obj.search(cr, uid, [('code', '=', seq_code)])
            sequence_type_obj.unlink(cr, SUPERUSER_ID, seq_type)
            sequence_obj.unlink(cr, SUPERUSER_ID, seq_id)
        return True


class protocollo_protocollo(orm.Model):
    _name = 'protocollo.protocollo'

    _inherit = 'mail.thread'
    _order = 'creation_date desc,name desc'

    STATE_SELECTION = [
        ('draft', 'Bozza'),
        ('registered', 'Registrato'),
        ('notified', 'Notificato'),
        ('waiting', 'Pec Inviata'),
        ('error', 'Errore Pec'),
        ('sent', 'Inviato'),
        ('canceled', 'Annullato'),
    ]

    def view_init(self, cr, uid, fields_list, context=None):
        user_ids = self.pool.get('res.users').browse(cr, SUPERUSER_ID, uid)

        if len(user_ids.employee_ids.ids) == 0:
            raise osv.except_osv(_('Warning!'), _(
                "L'utente %s non e' abilitato alla protocollazione: deve essere associato ad un dipendente") % user_ids.name)

        if len(user_ids.employee_ids.ids) > 1:
            raise osv.except_osv(_('Warning!'), _(
                "L'utente %s non e' configurato correttamente: deve essere associato ad un unico dipendente") % user_ids.name)

        if len(user_ids.employee_ids.department_id.ids) == 0:
            raise osv.except_osv(_('Warning!'), _(
                "Il dipendente %s non e' abilitato alla protocollazione: deve essere associato ad un Ufficio") % user_ids.name)

        employee_ids = self.pool.get('hr.employee').browse(cr, SUPERUSER_ID, user_ids.employee_ids.id)
        department_ids = self.pool.get('hr.department').browse(cr, uid, user_ids.employee_ids.department_id.id)
        if len(department_ids.aoo_id.ids) == 0:
            raise osv.except_osv(_('Warning!'), _(
                "Il dipendente %s non e' abilitato alla protocollazione: l'Ufficio '%s' deve essere associato ad una AOO") % (
                                     employee_ids.name, department_ids.name))
        aoo = department_ids.aoo_id.ids[0]
        aoo_ids = self.pool.get('protocollo.aoo').browse(cr, uid, aoo)
        if len(aoo_ids.registry_id.ids) == 0:
            raise osv.except_osv(_('Warning!'), _(
                'Errore di configurazione: nessun Registro associato alla AOO'))
        registry = self.pool.get('protocollo.registry').browse(cr, uid, aoo_ids.registry_id.ids[0])

        if employee_ids.id not in registry.allowed_employee_ids.ids:
            raise osv.except_osv(_('Warning!'), _(
                "Il dipendente %s non e' abilitato alla protocollazione: deve essere associato al Registro della AOO '%s'") % (
                                     employee_ids.name, aoo_ids.name))

    pass

    def on_change_emergency_receiving_date(self, cr, uid, ids, emergency_receiving_date, context=None):
        values = {}
        if emergency_receiving_date:
            values = {
                'receiving_date': emergency_receiving_date
            }
        return {'value': values}

    def on_change_datas(self, cr, uid, ids, datas, context=None):
        values = {}
        if datas:
            ct = magic.from_buffer(base64.b64decode(datas), mime=True)
            values = {
                'preview': datas,
                'preview_image': datas,
                'mimetype': ct
            }
        return {'value': values}

    def on_change_typology(self, cr, uid, ids, typology_id, context=None):
        values = {'pec': False, 'sharedmail': False, 'inserisci_testo_mailpec_visibility': False}
        if typology_id:
            typology_obj = self.pool.get('protocollo.typology')
            typology = typology_obj.browse(cr, uid, typology_id)
            configurazione_ids = self.pool.get('protocollo.configurazione').search(cr, uid, [])
            configurazione = self.pool.get('protocollo.configurazione').browse(cr, uid, configurazione_ids[0])
            body = configurazione.inserisci_testo_mailpec
            values['inserisci_testo_mailpec_visibility'] = body
            if typology.pec:
                values['pec'] = True
                values['sharedmail'] = False
            if typology.sharedmail:
                values['pec'] = False
                values['sharedmail'] = True
        return {'value': values}

    def on_change_reserved(self, cr, uid, ids, reserved, context=None):
        values = {}
        if reserved:
            values = {
                'assegnazione_ids': False,
            }
        return {'value': values}

    def calculate_complete_name(self, prot_date, prot_number):
        year = prot_date[:4]
        return year + prot_number

    def name_get(self, cr, uid, ids, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        reads = self.read(cr, uid, ids,
                          ['name', 'registration_date', 'state'],
                          context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['state'] != 'draft':
                name = self.calculate_complete_name(record['registration_date'], name)
                # year = record['registration_date'][:4]
                # name = year + name
            res.append((record['id'], name))
        return res

    def _get_complete_name(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)

    def _get_complete_name_search(self, cursor, user, obj, name, args, domain=None, context=None):
        res = []
        return [('id', 'in', res)]

    def _get_pec_notifications_sum(self, cr, uid, ids, field, arg, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        res = dict.fromkeys(ids, False)
        for prot in self.browse(cr, uid, ids):
            if prot.sender_receivers:
                check_notifications = 0
                for sender_receiver_id in prot.sender_receivers.ids:
                    sender_receiver_obj = self.pool.get('protocollo.sender_receiver').browse(cr, uid,
                                                                                             sender_receiver_id,
                                                                                             context=context)
                    # if sender_receiver_obj.pec_accettazione_status and sender_receiver_obj.pec_consegna_status:
                    #     check_notifications += 1
                if check_notifications == len(prot.sender_receivers.ids):
                    res[prot.id] = True
        return res

    def _get_assegnatari_competenza(self, cr, uid, protocollo):
        employees = []
        for assegnazione_competenza in protocollo.assegnazione_competenza_ids:
            if assegnazione_competenza.tipologia_assegnatario=='department':
                for assegnazione_competenza_child in assegnazione_competenza.child_ids:
                    employees.append(assegnazione_competenza_child.assegnatario_employee_id)
            else:
                employees.append(assegnazione_competenza.assegnatario_employee_id)
        employees = list(set(employees))
        return employees

    def _get_assegnatari_conoscenza(self, cr, uid, protocollo):
        employees = []
        for assegnazione_conoscenza in protocollo.assegnazione_conoscenza_ids:
            if assegnazione_conoscenza.tipologia_assegnatario=='department':
                for assegnazione_conoscenza_child in assegnazione_conoscenza.child_ids:
                    employees.append(assegnazione_conoscenza_child.assegnatario_employee_id)
            else:
                employees.append(assegnazione_conoscenza.assegnatario_employee_id)
        employees = list(set(employees))
        return employees

    def _get_assigne_emails(self, cr, uid, ids, field, arg, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        res = dict.fromkeys(ids, False)
        emails = ''
        for prot in self.browse(cr, uid, ids):
            assegnatari_competenza = self._get_assegnatari_competenza(cr, uid, prot)
            assegnatari_conoscenza = self._get_assegnatari_conoscenza(cr, uid, prot)
            assegnatari = list(set(assegnatari_competenza + assegnatari_conoscenza))
            assegnatari_emails = []
            for assegnatario in assegnatari:
                if assegnatario.user_id and assegnatario.user_id.email:
                    assegnatari_emails.append(assegnatario.user_id.email)
            emails = ','.join(assegnatari_emails)
            res[prot.id] = emails
        return res

    def _get_preview_datas(self, cr, uid, ids, field, arg, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        res = dict.fromkeys(ids, False)
        for prot in self.browse(cr, uid, ids):
            res[prot.id] = prot.doc_id.datas
        return res

    def _get_preview_image_datas(self, cr, uid, ids, field, arg, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        res = dict.fromkeys(ids, False)
        for prot in self.browse(cr, uid, ids):
            if prot.mimetype in ['image/png', 'image/jpeg', 'image/gif']:
                res[prot.id] = prot.doc_id.datas
            else:
                res[prot.id] = False
        return res

    def _get_assigne_emails_search(self, cursor, user, obj, name,
                                   args, domain=None, context=None):
        res = []
        return [('id', 'in', res)]

    def _get_sender_receivers_summary(self, cr, uid, ids,
                                      name, args, context=None):
        res = dict.fromkeys(ids, False)
        for protocol in self.browse(cr, uid, ids):
            res[protocol.id] = u"\n".join(
                [line.name for line
                 in protocol.sender_receivers
                 ]
            )
        return res

    def action_apri_stampa_etichetta(self, cr, uid, ids, context=None):
        context = dict(context or {})
        if not ids:
            return {}
        # for session in self.browse(cr, uid, ids, context=context):
        #     if session.user_id.id != uid:
        #         raise osv.except_osv(
        #             _('Error!'),
        #             _(
        #                 "You cannot use the session of another users. This session is owned by %s. Please first close this one to use this point of sale." % session.user_id.name))
        context.update({'active_id': ids[0]})
        action_class = "history_icon print"
        post_vars = {'subject': "Stampa Etichetta",
                     'body': "<div class='%s'><ul><li>Generata l'etichetta</li></ul></div>" % action_class,
                     'model': "protocollo.protocollo",
                     'res_id': context['active_id'],
                     }

        thread_pool = self.pool.get('protocollo.protocollo')
        thread_pool.message_post(cr, uid, context['active_id'], type="notification", context=context, **post_vars)

        return {
            'type': 'ir.actions.act_url',
            'url': '/seedoo/etichetta/%d' % ids[0],
        }

    _columns = {
        'complete_name': fields.function(
            _get_complete_name, type='char', size=256,
            string='N. Protocollo'),
        'name': fields.char('Numero Protocollo',
                            size=256,
                            required=True,
                            readonly=True),
        'registration_date': fields.datetime('Data Registrazione',
                                             readonly=True),
        'registration_date_from': fields.function(
            lambda *a, **k: {}, method=True,
            type='date', string="Inizio Data Ricerca"),
        'registration_date_to': fields.function(lambda *a, **k: {},
                                                method=True,
                                                type='date',
                                                string="Fine  Data Ricerca"),
        'user_id': fields.many2one('res.users', 'Protocollatore', readonly=True),
        'registration_employee_id': fields.many2one('hr.employee', 'Protocollatore', readonly=True),
        'registration_type': fields.selection(
            [
                ('normal', 'Normale'),
                ('emergency', 'Emergenza'),
            ], 'Tipologia Registrazione', size=32, required=True,
            readonly=True,
            states={'draft': [('readonly', False)]}, ),
        'type': fields.selection(
            [
                ('out', 'Uscita'),
                ('in', 'Ingresso'),
                ('internal', 'Interno')
            ], 'Tipo', size=32, required=True, readonly=True),
        'typology': fields.many2one(
            'protocollo.typology', 'Mezzo Trasmissione', readonly=True, required=False,
            states={'draft': [('readonly', False)]},
            help="Tipologia invio/ricevimento: \
                        Raccomandata, Fax, PEC, etc. \
                        si possono inserire nuove tipologie \
                        dal menu Tipologie."),
        'reserved': fields.boolean('Riservato',
                                   readonly=True,
                                   states={'draft': [('readonly', False)]},
                                   help="Se il protocollo e' riservato \
                                   il documento risulta visibile solo \
                                   all'ufficio di competenza"),
        'pec': fields.related('typology',
                              'pec',
                              type='boolean',
                              string='PEC',
                              readonly=False,
                              store=False),
        'sharedmail': fields.related('typology',
                                     'sharedmail',
                                     type='boolean',
                                     string='Sharedmail',
                                     readonly=False,
                                     store=False),
        'body': fields.html('Corpo della mail', readonly=True),
        'mail_pec_ref': fields.many2one('mail.message',
                                        'Riferimento PEC',
                                        readonly=True),
        'mail_sharedmail_ref': fields.many2one('mail.message',
                                               'Riferimento Mail',
                                               readonly=True),
        'mail_out_ref': fields.many2one('mail.mail',
                                        'Riferimento mail in uscita',
                                        readonly=True),
        'pec_notifications_ids': fields.related('mail_pec_ref',
                                                'pec_notifications_ids',
                                                type='one2many',
                                                relation='mail.message',
                                                string='Notification Messages',
                                                readonly=True),
        'pec_notifications_sum': fields.function(_get_pec_notifications_sum,
                                                 type="char",
                                                 string="PEC Status",
                                                 store=False),
        'creation_date': fields.date('Data Creazione',
                                     required=True,
                                     readonly=True,
                                     ),
        'receiving_date': fields.datetime('Data Ricezione',
                                          required=False,
                                          readonly=True,
                                          states={
                                              'draft': [('readonly', False)]
                                          }),
        'receiving_date_from': fields.function(
            lambda *a, **k: {}, method=True,
            type='date', string="Inizio Data ricezione Ricerca"),
        'receiving_date_to': fields.function(lambda *a, **k: {},
                                                method=True,
                                                type='date',
                                                string="Fine  Data ricezione Ricerca"),
        'subject': fields.text('Oggetto',
                               required=False,
                               readonly=True,
                               states={'draft': [('readonly', False)]}),
        'datas_fname': fields.char(
            'Nome Documento', size=256, readonly=False),
        'datas': fields.binary('File Documento',
                               required=False),
        'preview': fields.function(_get_preview_datas,
                                   type='binary',
                                   string='Preview'),
        'preview_image': fields.function(_get_preview_image_datas,
                                   type='binary',
                                   string='Preview Image'),
        'mimetype': fields.char('Mime Type', size=64),
        'doc_id': fields.many2one(
            'ir.attachment', 'Documento Principale', readonly=True,
            domain="[('res_model', '=', 'protocollo.protocollo')]"),
        'doc_content': fields.related('doc_id', 'datas', type='binary', string='Documento', readonly=True),
        'doc_description': fields.related('doc_id', 'datas_description', type='char', string='Descrizione',
                                          readonly=True),
        'doc_fname': fields.related('doc_id', 'datas_fname', type="char", readonly=True),
        'fingerprint': fields.char(string="Impronta Documento", size=256),
        'classification': fields.many2one('protocollo.classification',
                                          'Titolario di Classificazione',
                                          required=False,
                                          readonly=True,
                                          states={
                                              'draft': [('readonly', False)]
                                          }),
        'classification_code': fields.related('classification',
                                              'code',
                                              type="char",
                                              string="Codice e Nome Titolario",
                                              readonly=True),
        'emergency_protocol': fields.char(
            'Protocollo Emergenza', size=64, required=False,
            readonly=True,
            states={'draft': [('readonly', False)]}),
        'emergency_receiving_date': fields.datetime(
            'Data Ricevimento in Emergenza', required=False,
            readonly=True,
            states={'draft': [('readonly', False)]}),
        'emergency_active': fields.boolean('Registro Emergenza Attivo'),
        'sender_protocol': fields.char('Protocollo Mittente',
                                       size=64,
                                       required=False,
                                       readonly=True,
                                       states={'draft': [('readonly', False)]
                                               }),
        'sender_register': fields.char('Registro Mittente',
                                       size=64,
                                       required=False,
                                       readonly=True),
        'sender_registration_date': fields.date('Data Registrazione Mittente',
                                                size=64,
                                                required=False,
                                                ),
        'sender_receivers': fields.one2many('protocollo.sender_receiver', 'protocollo_id', 'Mittenti/Destinatari'),
        'senders': fields.one2many('protocollo.sender_receiver', 'protocollo_id', 'Mittente',
                                   domain=[('source', '=', 'sender')]),
        'receivers': fields.one2many('protocollo.sender_receiver', 'protocollo_id', 'Destinatari',
                                     domain=[('source', '=', 'receiver')]),

        'sender_receivers_summary': fields.function(
            _get_sender_receivers_summary,
            type="char",
            string="Mittenti/Destinatari",
            store=False),
        'assigne_emails': fields.function(_get_assigne_emails, type='char', string='Email Destinatari'),
        'assigne_cc': fields.boolean('Inserisci gli Assegnatari in CC'),
        'dossier_ids': fields.many2many('protocollo.dossier', 'dossier_protocollo_rel', 'protocollo_id', 'dossier_id',
                                        'Fascicoli'),

        'assegnazione_ids': fields.one2many('protocollo.assegnazione', 'protocollo_id', 'Assegnatari', readonly=True),
        'assegnazione_first_level_ids': fields.one2many('protocollo.assegnazione', 'protocollo_id', 'Assegnatari',
                                                        domain=[('parent_id', '=', False)], readonly=True),
        'assegnazione_competenza_ids': fields.one2many('protocollo.assegnazione', 'protocollo_id', 'Assegnatari',
                                       domain=[('parent_id', '=', False),('tipologia_assegnazione', '=', 'competenza')],
                                       readonly=True),
        'assegnazione_conoscenza_ids': fields.one2many('protocollo.assegnazione', 'protocollo_id', 'Assegnatari',
                                       domain=[('parent_id', '=', False), ('tipologia_assegnazione', '=', 'conoscenza')],
                                       readonly=True),

        'notes': fields.text('Note'),
        'state': fields.selection(
            STATE_SELECTION, 'Stato', readonly=True,
            help="Lo stato del protocollo.", select=True),
        'year': fields.integer('Anno', required=True),
        'attachment_ids': fields.one2many('ir.attachment', 'res_id', 'Allegati', readonly=True,
                                          domain=[('res_model', '=', 'protocollo.protocollo')]),
        'xml_signature': fields.text('Segnatura xml'),
        'aoo_id': fields.many2one('protocollo.aoo', 'AOO', required=True),
        'registry': fields.related('aoo_id', 'registry_id', type='many2one', relation='protocollo.registry',
                                   string='Registro', store=True, readonly=True),
        'protocol_request': fields.boolean('Richiesta Protocollo', readonly=True),
        'server_sharedmail_id': fields.many2one('fetchmail.server', 'Account Email',
                                                domain="[('sharedmail', '=', True),('user_sharedmail_ids', 'in', uid)]"),
        'server_pec_id': fields.many2one('fetchmail.server', 'Account PEC',
                                         domain="[('pec', '=', True),('user_ids', 'in', uid)]"),

    }

    def _get_default_name(self, cr, uid, context=None):
        if context is None:
            context = {}
        dest_tz = pytz.timezone("Europe/Rome")
        now = datetime.datetime.now(dest_tz).strftime(DSDF)
        # now = datetime.datetime.now().strftime(
        #     DSDF)
        return 'Nuovo Protocollo del ' + now

    def _get_default_year(self, cr, uid, context=None):
        if context is None:
            context = {}
        now = datetime.datetime.now()
        return now.year

    def _get_default_is_emergency_active(self, cr, uid, context=None):
        emergency_registry_obj = self.pool.get('protocollo.emergency.registry')
        aoo_id = self._get_default_aoo_id(cr, uid)
        if aoo_id:
            reg_ids = emergency_registry_obj.search(cr, uid, [
                ('aoo_id', '=', aoo_id),
                ('state', '=', 'draft')
            ])
            if len(reg_ids) > 0:
                return True
        return False

    def _get_default_aoo_id(self, cr, uid, context=None):
        aoo_ids = self.pool.get('protocollo.aoo').search(cr, uid, [], context=context)
        for aoo_id in aoo_ids:
            check = self.pool.get('protocollo.aoo').is_visible_to_protocol_action(cr, uid, aoo_id)
            if check:
                return aoo_id
        return False

    def _get_def_sharedmail_server(self, cr, uid, context=None):
        res = self.pool.get('fetchmail.server').search(cr, uid,
                                                       [('user_sharedmail_ids', 'in', uid), ('sharedmail', '=', True)],
                                                       context=context)
        return res and res[0] or False

    def _get_def_pec_server(self, cr, uid, context=None):
        res = self.pool.get('fetchmail.server').search(cr, uid, [('user_ids', 'in', uid), ('pec', '=', True)],
                                                       context=context)
        return res and res[0] or False

    _defaults = {
        'registration_type': 'normal',
        'emergency_active': _get_default_is_emergency_active,
        'name': _get_default_name,
        'creation_date': fields.date.context_today,
        # 'receiving_date': lambda *a: time.strftime(
        #     DSDF),
        'state': 'draft',
        'year': _get_default_year,
        'user_id': lambda obj, cr, uid, context: uid,
        'datas': None,
        'datas_fname': None,
        'aoo_id': _get_default_aoo_id,
        'server_sharedmail_id': _get_def_sharedmail_server,
        'server_pec_id': _get_def_pec_server,
    }

    _sql_constraints = [
        ('protocol_number_unique', 'unique(name,year,aoo_id)',
         'Elemento già presente nel DB!'),
        ('protocol_mail_pec_ref_unique', 'unique(mail_pec_ref)',
         'Messaggio protocollato in precedenza!')
    ]

    def _get_next_number_normal(self, cr, uid, prot):

        sequence_obj = self.pool.get('ir.sequence')

        _logger.info("Acquiring lock")
        LockerSingleton.lock.acquire()

        new_cr = self.pool.cursor()
        new_cr.execute("BEGIN TRANSACTION ISOLATION LEVEL SERIALIZABLE READ WRITE;")

        last_id = self.search(new_cr, uid,
                              [('state', 'in', ('registered', 'notified', 'sent', 'waiting', 'error', 'canceled'))],
                              limit=1, order='registration_date desc')
        if last_id:
            now = datetime.datetime.now()
            last = self.browse(new_cr, uid, last_id[0])
            if last.registration_date[0:4] < str(now.year):
                seq_id = sequence_obj.search(new_cr, uid, [('code', '=', prot.registry.sequence.code)])
                sequence_obj.write(new_cr, SUPERUSER_ID, seq_id, {'number_next': 1})

        next_num = False

        _logger.info("Getting sequence")
        try:
            next_num = sequence_obj.get_serialized_sequence_code(new_cr, uid, prot.registry.sequence.code) or None
        except Exception as e:
            _logger.error(e.message)

        new_cr.execute("COMMIT TRANSACTION;")
        new_cr.close()

        LockerSingleton.lock.release()
        _logger.info("Lock released")

        if not next_num:
            raise orm.except_orm(_('Errore'),
                                 _('Il sistema ha riscontrato un errore nel reperimento del numero protocollo'))
        return next_num

    def _get_next_number_emergency(self, cr, uid, prot):
        emergency_registry_obj = self.pool.get('protocollo.emergency.registry')
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
                    self.pool.get('protocollo.emergency.registry.line'). \
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

    def _get_next_number(self, cr, uid, prot):
        if prot.registration_type == 'emergency':
            return self._get_next_number_emergency(cr, uid, prot)
        # FIXME what if the emergency is the 31 december
        # and we protocol the 1 january
        return self._get_next_number_normal(cr, uid, prot)

    def _full_path(self, cr, uid, location, path):
        assert location.startswith('file:'), \
            "Unhandled filestore location %s" % location
        location = location[5:]

        # sanitize location name and path
        location = re.sub('[.]', '', location)
        location = location.strip('/\\')

        path = re.sub('[.]', '', path)
        path = path.strip('/\\')
        return os.path.join('/', location, cr.dbname, path)

    def _convert_pdfa(self, cr, uid, doc_path):
        cmd = ['unoconv', '-f', 'pdf', '-eSelectPdfVersion=1', '-o',
               doc_path + '.pdf', doc_path]
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
            stdoutdata, stderrdata = proc.communicate()
            if proc.wait() != 0:
                _logger.warning(stdoutdata)
                raise Exception(stderrdata)
            return True
        finally:
            shutil.move(doc_path + '.pdf', doc_path)

    def _create_attachment_encryped_file(self, cr, uid, prot, path):
        pdf_file = open(path, 'r')
        data_encoded = base64.encodestring(pdf_file.read())
        attach_vals = {
            'name': prot.datas_fname + '.signed',
            'datas': data_encoded,
            'datas_fname': prot.datas_fname + '.signed',
            'res_model': 'protocollo.protocollo',
            'is_protocol': True,
            'res_id': prot.id,
        }
        attachment_obj = self.pool.get('ir.attachment')
        attachment_obj.create(cr, uid, attach_vals)
        pdf_file.close()
        os.remove(path)
        return True

    def _sign_doc(self, cr, uid, prot, prot_number, prot_date):
        def sha1OfFile(filepath):
            import hashlib
            with open(filepath, 'rb') as f:
                return hashlib.sha1(f.read()).hexdigest()

        pd = prot_date.split(' ')[0]
        prot_date = datetime.datetime.strptime(pd, DSDT)

        if prot.type == "in":
            prot_dir = "INGRESSO"
        elif prot.type == "out":
            prot_dir = "USCITA"
        elif prot.type == "internal":
            prot_dir = "INTERNO"
        else:
            prot_dir = ""

        ammi_code = prot.registry.company_id.ammi_code if prot.registry.company_id.ammi_code else ""
        prot_def = "%s %s - %s - %s - Prot. n. %s del %s" % (
            ammi_code,
            prot.aoo_id.ident_code,
            prot.registry.code,
            prot_dir,
            prot_number,
            prot_date.strftime(DSDT)
        )

        location = self.pool.get('ir.config_parameter').get_param(cr,
                                                                  uid,
                                                                  'ir_attachment.location') + '/protocollazioni'

        file_path = self._full_path(cr, uid, location, prot.doc_id.store_fname)
        maintain_orig = False
        strong_encryption = False

        signature_jar = "signature.jar"
        signature_cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)), "util", signature_jar)
        cmd = ["java", "-jar", signature_cmd, file_path, prot_def]

        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
            stdoutdata, stderrdata = proc.communicate()
            if proc.wait() != 0:
                _logger.warning(stdoutdata)
                raise Exception(stderrdata)
            if os.path.isfile(file_path + '.dec.pdf'):
                maintain_orig = True
            if os.path.isfile(file_path + '.enc'):
                strong_encryption = True
                os.remove(file_path + '.enc')
            if os.path.isfile(file_path + '.fail'):
                os.remove(file_path + '.fail')
                raise orm.except_osv(_("Errore"), _("Qualcosa è andato storto nella aggiunta della segnatura!"))
        except Exception as e:
            raise Exception(e)

        if maintain_orig:
            self._create_attachment_encryped_file(cr, uid, prot, file_path + '.dec.pdf')
        elif strong_encryption:
            pass
        else:
            shutil.move(file_path + '.pdf', file_path)

        # TODO convert in pdfa here

        return sha1OfFile(file_path)

    def _create_protocol_attachment(self, cr, uid, prot,
                                    prot_number, prot_date):
        def sha1OfFile(filepath):
            import hashlib
            with open(filepath, 'rb') as f:
                return hashlib.sha1(f.read()).hexdigest()

        parent_id = 0
        ruid = 0
        # if prot.reserved:
        #    parent_id, ruid = self._create_protocol_security_folder(cr, SUPERUSER_ID, prot, prot_number)
        attachment_obj = self.pool.get('ir.attachment')
        configurazione_ids = self.pool.get('protocollo.configurazione').search(cr, uid, [])
        configurazione = self.pool.get('protocollo.configurazione').browse(cr, uid, configurazione_ids[0])
        old_attachment_id = prot.doc_id.id
        attachment = attachment_obj.browse(cr, uid, old_attachment_id)
        file_name = attachment.datas_fname

        if file_name and configurazione.rinomina_documento_allegati:
            file_name = self._get_name_documento_allegato(cr, uid, file_name, prot_number, 'Prot', True)

        attach_vals = {
            'name': file_name,
            'datas': attachment.datas,
            'datas_fname': file_name,
            'datas_description': attachment.datas_description,
            'res_model': 'protocollo.protocollo',
            'is_protocol': True,
            'reserved': prot.reserved,
            'res_id': prot.id,
        }
        if parent_id:
            attach_vals['parent_id'] = parent_id

        user_id = ruid or uid
        attachment_id = attachment_obj.create(cr, user_id, attach_vals)
        self.write(cr, uid, prot.id, {'doc_id': attachment_id, 'datas': 0})
        attachment_obj.unlink(cr, SUPERUSER_ID, old_attachment_id)
        location = self.pool.get('ir.config_parameter').get_param(cr, uid,
                                                                  'ir_attachment.location') + '/protocollazioni'
        new_attachment = attachment_obj.browse(cr, user_id, attachment_id)
        file_path = self._full_path(
            cr, uid, location, new_attachment.store_fname)
        return sha1OfFile(file_path)

    def _create_protocol_security_folder(self, cr, uid, prot, prot_number):
        group_reserved_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'seedoo_protocollo',
                                                                                'group_protocollazione_riservata')[1]
        directory_obj = self.pool.get('document.directory')
        directory_root_id = \
            self.pool.get('ir.model.data').get_object_reference(cr, uid, 'seedoo_protocollo', 'dir_protocol')[1]
        ruid = None
        if prot.aoo_id.reserved_employee_id and prot.aoo_id.reserved_employee_id.user_id:
            ruid = prot.aoo_id.reserved_employee_id.user_id.id
        if not ruid:
            raise orm.except_orm(_('Attenzione!'), _('Manca il responsabile dei dati sensibili!'))
        directory_id = directory_obj.create(
            cr, uid, {
                'name': 'Protocollo %s %s' % (str(prot_number), str(prot.year)),
                'parent_id': directory_root_id,
                'user_id': ruid,
                'group_ids': [[6, 0, [group_reserved_id]]]
            })
        return directory_id, ruid

    def action_create_attachment(self, cr, uid, ids, *args):
        try:
            for prot in self.browse(cr, uid, ids):
                if prot.datas and prot.datas_fname:
                    attach_vals = {
                        'name': prot.datas_fname,
                        'datas': prot.datas,
                        'datas_fname': prot.datas_fname,
                        'res_model': 'protocollo.protocollo',
                        'is_protocol': True,
                        'res_id': prot.id,
                    }
                    protocollo_obj = self.pool.get('protocollo.protocollo')
                    attachment_obj = self.pool.get('ir.attachment')
                    attachment_id = attachment_obj.create(cr, uid, attach_vals)
                    protocollo_obj.write(
                        cr, uid, prot.id,
                        {'doc_id': attachment_id, 'datas': 0})
        except Exception as e:
            raise Exception(e)

        return True

    def get_partner_values(self, cr, uid, send_rec):
        values = {
            'name': send_rec.name,
            'street': send_rec.street,
            'city': send_rec.city,
            'country_id': send_rec.country_id and send_rec.country_id.id or False,
            'email': send_rec.email,
            'pec_mail': send_rec.pec_mail,
            'phone': send_rec.phone,
            'mobile': send_rec.mobile,
            'fax': send_rec.fax,
            'zip': send_rec.zip,
            'legal_type': send_rec.type,
            'pa_type': send_rec.pa_type,
            'ident_code': send_rec.ident_code,
            'ammi_code': send_rec.ammi_code,
            'ipa_code': send_rec.ipa_code
        }
        return values

    def action_create_partners(self, cr, uid, ids, *args):
        send_rec_obj = self.pool.get('protocollo.sender_receiver')
        for prot in self.browse(cr, uid, ids):
            for send_rec in prot.sender_receivers:
                if send_rec.save_partner and not send_rec.partner_id:
                    # if send_rec.partner_id:
                    #    raise orm.except_orm('Attenzione!', 'Si sta tentando di salvare un\' anagrafica già presente nel sistema')
                    partner_obj = self.pool.get('res.partner')
                    values = self.get_partner_values(cr, uid, send_rec)
                    partner_id = partner_obj.create(cr, uid, values)
                    send_rec_obj.write(cr, uid, [send_rec.id], {'partner_id': partner_id})
        return True

    def action_register_process(self, cr, uid, ids, context=None, *args):
        res = []
        res_registrazione = None
        res_conferma = None
        check = self.check_journal(cr, uid, ids)
        if check:
            check = self.action_create_attachment(cr, uid, ids)
        if check:
            check = self.action_create_partners(cr, uid, ids)
        if check:
            res_registrazione = self.action_register(cr, uid, ids)
            check = True if res_registrazione is not None and len(res_registrazione) > 0 and 'Registrazione' in \
                            res_registrazione[0] and 'Res' in res_registrazione[0]['Registrazione'] and \
                            res_registrazione[0]['Registrazione']['Res'] else False

        if check:
            wf_service = netsvc.LocalService('workflow')
            wf_service.trg_validate(uid, 'protocollo.protocollo', ids[0], 'register', cr)
            res_conferma = self.action_send_conferma(cr, uid, ids)

        if res_registrazione is not None:
            for item_res_registrazione in res_registrazione:
                res.append(item_res_registrazione)

        if check and res_conferma is not None:
            res.append(res_conferma)

        return res

    def action_register(self, cr, uid, ids, context=None, *args):
        # self.lock.acquire()
        configurazione_ids = self.pool.get('protocollo.configurazione').search(cr, uid, [])
        configurazione = self.pool.get('protocollo.configurazione').browse(cr, uid, configurazione_ids[0])
        res = []
        res_registrazione = []
        res_segnatura = []
        err_segnatura = False

        for prot in self.browse(cr, uid, ids):

            self.pool.get('protocollo.configurazione').verifica_campi_obbligatori(cr, uid, prot)
            prot_reserved_errors = ''
            if prot.reserved and prot.assegnazione_competenza_ids and \
                    prot.assegnazione_competenza_ids[0].tipologia_assegnatario=='department':
                prot_reserved_errors = prot_reserved_errors + '\n- I protocollo riservati non possono avere uffici come assegnatari per competenza'
            if prot.reserved and prot.assegnazione_conoscenza_ids:
                prot_reserved_errors = prot_reserved_errors + '\n- I protocollo riservati non possono avere assegnatari per conoscenza'
            if prot_reserved_errors:
                raise openerp.exceptions.Warning('Prima di procedere con la registrazione è necessario correggere i seguenti punti: ' + prot_reserved_errors)


            if prot.state == 'draft':
                try:
                    vals = {}
                    prot_number = self._get_next_number(cr, uid, prot)
                    prot_date = fields.datetime.now()
                    vals['name'] = prot_number
                    vals['registration_date'] = prot_date
                    employee_ids = self.pool.get('hr.employee').search(cr, uid, [('user_id', '=', uid)])
                    attachment_obj = self.pool.get('ir.attachment')

                    if employee_ids:
                        vals['registration_employee_id'] = employee_ids[0]

                    # prot_complete_name = self.calculate_complete_name(prot_date, prot_number)

                    if prot.doc_id:
                        try:
                            if prot.mimetype == 'application/pdf':
                                self._sign_doc(cr, uid, prot, prot_number, prot_date)
                            res_segnatura = {"Segnatura": {"Res": True, "Msg": "Segnatura generata correttamente"}}
                        except Exception as e:
                            _logger.error(e)
                            err_segnatura = True
                            res_segnatura = {
                                "Segnatura": {"Res": False, "Msg": "Non è stato possibile generare la segnatura PDF"}}

                        fingerprint = self._create_protocol_attachment(cr, uid, prot, prot_number, prot_date)
                        vals['fingerprint'] = fingerprint
                        vals['datas'] = 0

                    now = datetime.datetime.now()
                    vals['year'] = now.year
                    self.write(cr, uid, [prot.id], vals)

                    try:
                        if configurazione.rinomina_documento_allegati:
                            attachment_ids = attachment_obj.search(cr, uid,
                                                                   [('res_model', '=', 'protocollo.protocollo'),
                                                                    ('res_id', '=', prot.id),
                                                                    ('is_protocol', '=', True)])
                            if attachment_ids:
                                attachments = attachment_obj.browse(cr, uid, attachment_ids)
                                for attachment in attachments:
                                    if attachment.is_main is False:
                                        filename = self._get_name_documento_allegato(cr, uid, attachment.datas_fname,
                                                                                     prot_number, 'Prot', False)
                                        attachment_obj.write(cr, uid, [attachment.id],
                                                             {'name': filename, 'datas_fname': filename})
                    except Exception as e:
                        _logger.error(e)
                        raise openerp.exceptions.Warning(_('Errore nella ridenominazione degli allegati'))

                    thread_pool = self.pool.get('protocollo.protocollo')
                    action_class = "history_icon registration"
                    post_vars = {
                        'subject': "Registrazione protocollo",
                        'body': "<div class='%s'><ul><li>Creato protocollo %s</li></ul></div>" % (
                            action_class, prot_number),
                        'model': "protocollo.protocollo",
                        'res_id': prot.id,
                    }
                    thread_pool.message_post(cr, uid, prot.id, type="notification", context=context, **post_vars)

                    if err_segnatura:
                        action_class = "history_icon warning"
                        post_vars_segnatura = {
                            'subject': "Errore Generazione Segnatura",
                            'body': "<div class='%s'><ul><li>Impossibile generare la segnatura PDF</li></ul></div>" % action_class,
                            'model': "protocollo.protocollo",
                            'res_id': prot.id,
                        }
                        thread_pool.message_post(cr, uid, prot.id, type="notification", context=context,
                                                 **post_vars_segnatura)

                    res_registrazione = {"Registrazione": {"Res": True,
                                                           "Msg": "Protocollo Nr. %s del %s registrato correttamente" % (
                                                               prot_number, prot.registration_date)}}
                except Exception as e:
                    _logger.error(e)
                    # res_registrazione = {"Registrazione":{"Res": False, "Msg": "Errore nella registrazione del protocollo"}}
                    raise openerp.exceptions.Warning(_('Errore nella registrazione del protocollo'))
                res.append(res_registrazione)
                if len(res_segnatura) > 0:
                    res.append(res_segnatura)
            else:
                raise openerp.exceptions.Warning(_('"Non è più possibile eseguire l\'operazione richiesta! Il protocollo è già stato preso in carico da un altro utente!'))
        # self.lock.release()
        return res

    def action_send_conferma(self, cr, uid, ids, context=None, *args):
        res_conferma = {"Invio Conferma": {"Res": False, "Msg": None}}
        configurazione_ids = self.pool.get('protocollo.configurazione').search(cr, uid, [])
        configurazione = self.pool.get('protocollo.configurazione').browse(cr, uid, configurazione_ids[0])

        try:
            for prot in self.browse(cr, uid, ids):
                if prot.type == 'in' and prot.pec and len(
                        prot.mail_pec_ref.ids) > 0 and configurazione.conferma_xml_invia:
                    res = self.action_send_receipt(cr, uid, ids, 'conferma', context=context)
                    if res == 'sent':
                        res_conferma = {"Invio Conferma": {"Res": True, "Msg": "Conferma inviata correttamente"}}
                    elif res == 'exception':
                        res_conferma = {"Invio Conferma": {"Res": False,
                                                           "Msg": "Non è stato possibile inviare la Conferma di Protocollazione al Mittente"}}
        except Exception as e:
            _logger.error(e)
            res_conferma = {"Invio Conferma": {"Res": False,
                                               "Msg": "Non è stato possibile inviare la Conferma di Protocollazione al Mittente"}}

        return res_conferma

    def action_notify(self, cr, uid, ids, *args):
        email_template_obj = self.pool.get('email.template')
        for prot in self.browse(cr, uid, ids):
            if prot.type == 'in' and not prot.assegnazione_competenza_ids:
                raise openerp.exceptions.Warning(_('Errore nella notifica del protocollo, mancano gli assegnatari'))
            if prot.reserved:
                template_reserved_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'seedoo_protocollo',
                                                                                           'notify_reserved_protocol')[
                    1]
                email_template_obj.send_mail(cr, uid, template_reserved_id, prot.id, force_send=True)
            if prot.assigne_emails:
                template_id = \
                    self.pool.get('ir.model.data').get_object_reference(cr, uid, 'seedoo_protocollo',
                                                                        'notify_protocol')[1]
                email_template_obj.send_mail(cr, uid, template_id, prot.id, force_send=True)
        return True

    def action_notify_cancel(self, cr, uid, ids, *args):
        return True

    def action_send_receipt(self, cr, uid, ids, receipt_type, context=None, *args):
        if context is None:
            context = {}

        res = None
        for prot in self.browse(cr, uid, ids):
            receipt_xml = None
            messaggio_pec_obj = self.pool.get('protocollo.messaggio.pec')
            if receipt_type == 'conferma':
                receipt_xml = ConfermaXML(prot, cr, uid)
            if receipt_type == 'annullamento':
                receipt_xml = AnnullamentoXML(cr, uid, prot, context['receipt_cancel_reason'],
                                              context['receipt_cancel_author'], context['receipt_cancel_date'])

            xml = receipt_xml.generate_receipt_root()
            etree_tostring = etree.tostring(xml, pretty_print=True)

            if etree_tostring:
                mail_mail = self.pool.get('mail.mail')
                new_context = dict(context).copy()
                new_context.update({'pec_messages': True})
                mail_server = self.get_mail_server(cr, uid, new_context)

                sender_receivers_pec_mails = []
                sender_receivers_pec_ids = []

                if prot.sender_receivers:
                    for sender_receiver_id in prot.sender_receivers.ids:
                        sender_receiver_obj = self.pool.get('protocollo.sender_receiver').browse(cr, uid,
                                                                                                 sender_receiver_id,
                                                                                                 context=context)
                        sender_receivers_pec_mails.append(sender_receiver_obj.pec_mail)
                        sender_receivers_pec_ids.append(sender_receiver_obj.id)

                if receipt_type == 'conferma':
                    attachment = self.pool.get('ir.attachment').create(cr, uid, {'name': 'conferma.xml',
                                                                                 'datas_fname': 'conferma.xml',
                                                                                 'datas': etree_tostring.encode(
                                                                                     'base64')})
                elif receipt_type == 'annullamento':
                    attachment = self.pool.get('ir.attachment').create(cr, uid, {'name': 'annullamento.xml',
                                                                                 'datas_fname': 'annullamento.xml',
                                                                                 'datas': etree_tostring.encode(
                                                                                     'base64')})

                # vals = {'pec_conferma_ref': mail.mail_message_id.id}
                # self.write(cr, uid, [prot.id], vals)
                new_context = dict(context).copy()
                new_context.update({'receipt_email_from': mail_server.smtp_user})
                new_context.update({'receipt_email_to': ','.join([sr for sr in sender_receivers_pec_mails])})
                new_context.update({'pec_messages': True})

                email_template_obj = self.pool.get('email.template')

                if receipt_type == 'conferma':
                    template_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'seedoo_protocollo',
                                                                                      'confirm_protocol')[1]
                if receipt_type == 'annullamento':
                    template_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'seedoo_protocollo',
                                                                                      'cancel_protocol')[1]

                template = email_template_obj.browse(cr, uid, template_id, new_context)
                template.attachment_ids = [(6, 0, [attachment])]
                template.write({
                    'mail_server_id': mail_server.id
                })
                mail_receipt_id = template.send_mail(prot.id, force_send=True)

                for sender_receiver_id in sender_receivers_pec_ids:
                    vals = {}
                    sender_receiver_obj = self.pool.get('protocollo.sender_receiver').browse(cr, uid,
                                                                                             sender_receiver_id,
                                                                                             context=context)
                    message_obj = self.pool.get('mail.message')
                    mail_receipt = self.pool.get('mail.mail').browse(cr, uid, mail_receipt_id[0], context=context)
                    message_receipt = mail_mail.browse(cr, uid, mail_receipt.mail_message_id.id, context=context)
                    valsreceipt = {}
                    valsreceipt['pec_protocol_ref'] = prot.id
                    valsreceipt['pec_state'] = 'protocol'
                    valsreceipt['pec_type'] = 'posta-certificata'
                    valsreceipt['direction'] = 'out'
                    message_obj.write(cr, uid, mail_receipt.mail_message_id.id, valsreceipt)
                    messaggio_pec_id = messaggio_pec_obj.create(cr, uid, {'type': receipt_type,
                                                                          'messaggio_ref': message_receipt.id})
                    vals['pec_messaggio_ids'] = [(4, [messaggio_pec_id])]
                    sender_receiver_obj.write(vals)

                res_mail_receipt = self.pool.get('mail.mail').browse(cr, uid, mail_receipt_id, context=context)
                thread_pool = self.pool.get('protocollo.protocollo')
                if res_mail_receipt.state == "sent":
                    action_class = "history_icon mail"
                    post_vars = {
                        'subject': "Ricevuta di %s inviata" % receipt_type,
                        'body': "<div class='%s'><ul><li>Conferma.xml inviata correttamente</li></ul></div>" % (
                            action_class),
                        'model': "protocollo.protocollo",
                        'res_id': prot.id,
                    }
                elif res_mail_receipt.state == "exception":
                    action_class = "history_icon warning"
                    post_vars = {
                        'subject': "Ricevuta di %s non inviata" % receipt_type,
                        'body': "<div class='%s'><ul><li>Non è stato possibile inviare la Conferma di Protocollazione al Mittente</li></ul></div>" % (
                            action_class),
                        'model': "protocollo.protocollo",
                        'res_id': prot.id,
                    }

                if res_mail_receipt.state in ['sent', 'exception']:
                    thread_pool.message_post(cr, uid, prot.id, type="notification", context=context, **post_vars)
                    res = res_mail_receipt.state
        return res

    def _get_assigne_cc_emails(self, cr, uid, ids, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        emails = ''
        users = []
        for prot in self.browse(cr, uid, ids):
            assegnatari_competenza = self._get_assegnatari_competenza(cr, uid, prot)
            assegnatari_conoscenza = self._get_assegnatari_conoscenza(cr, uid, prot)
            assegnatari = list(set(assegnatari_competenza + assegnatari_conoscenza))
            assegnatari_emails = []
            for assegnatario in assegnatari:
                if assegnatario.user_id and assegnatario.user_id.email:
                    assegnatari_emails.append(assegnatario.user_id.email)
            emails = ','.join(assegnatari_emails)
        return emails

    def _create_outgoing_pec(self, cr, uid, prot_id, context=None):
        if context is None:
            context = {}
        prot = self.browse(cr, uid, prot_id)
        if prot.type == 'out' and prot.pec:
            configurazione_ids = self.pool.get('protocollo.configurazione').search(cr, uid, [])
            configurazione = self.pool.get('protocollo.configurazione').browse(cr, uid, configurazione_ids[0])
            mail_mail = self.pool.get('mail.mail')
            ir_attachment = self.pool.get('ir.attachment')
            messaggio_pec_obj = self.pool.get('protocollo.messaggio.pec')
            sender_receivers_pec_mails = []
            sender_receivers_pec_ids = []
            fetchmail_server_id = prot.server_pec_id.id
            mail_server_obj = self.pool.get('ir.mail_server')
            mail_server_ids = mail_server_obj.search(cr, uid, [('in_server_id', '=', fetchmail_server_id)])
            mail_server = mail_server_obj.browse(cr, uid, mail_server_ids)
            # mail_server = self.get_mail_server(cr, uid, context)

            if configurazione.segnatura_xml_invia:
                vals = {}
                try:
                    segnatura_xml = SegnaturaXML(prot, prot.name, prot.registration_date, cr, uid)
                    xml = segnatura_xml.generate_segnatura_root()
                    etree_tostring = etree.tostring(xml, pretty_print=True)
                    vals['xml_signature'] = etree_tostring
                    self.write(cr, uid, [prot.id], vals)
                    self.allega_segnatura_xml(cr, uid, prot.id, prot.xml_signature)
                except Exception as e:
                    _logger.error(e)

            if prot.sender_receivers:
                for sender_receiver_id in prot.sender_receivers.ids:
                    sender_receiver_obj = self.pool.get('protocollo.sender_receiver').browse(cr, uid,
                                                                                             sender_receiver_id,
                                                                                             context=context)
                    # if not sender_receiver_obj.pec_invio_status:
                    if (
                            sender_receiver_obj.pec_errore_consegna_status and sender_receiver_obj.to_resend) or not sender_receiver_obj.pec_invio_status:
                        sender_receivers_pec_mails.append(sender_receiver_obj.pec_mail)
                        sender_receivers_pec_ids.append(sender_receiver_obj.id)

            subject = self._get_oggetto_mail_pec(cr, uid, prot.subject, prot.name,
                                                 prot.registration_date) if configurazione.rinomina_oggetto_mail_pec else prot.subject
            if configurazione.lunghezza_massima_oggetto_pec > 0:
                subject = subject[:configurazione.lunghezza_massima_oggetto_pec]

            values = {}
            values['subject'] = subject
            values['body_html'] = prot.body
            values['body'] = prot.body
            values['email_from'] = mail_server.smtp_user
            values['reply_to'] = mail_server.in_server_id.user
            values['mail_server_id'] = mail_server.id
            values['email_to'] = ','.join([sr for sr in
                                           sender_receivers_pec_mails]
                                          )
            values['pec_to'] = values['email_to']
            values['pec_protocol_ref'] = prot.id
            values['pec_state'] = 'protocol'
            values['pec_type'] = 'posta-certificata'
            values['server_id'] = fetchmail_server_id

            if prot.assigne_cc:
                values['email_cc'] = self._get_assigne_cc_emails(
                    cr, uid, prot_id, context)
            msg_id = mail_mail.create(cr, uid, values, context=context)
            mail = mail_mail.browse(cr, uid, msg_id, context=context)
            # manage attachments
            attachment_ids = ir_attachment.search(cr, uid,
                                                  [('res_model',
                                                    '=',
                                                    'protocollo.protocollo'),
                                                   ('res_id',
                                                    '=',
                                                    prot.id)]
                                                  )
            if attachment_ids:
                values['attachment_ids'] = [(6, 0, attachment_ids)]
                mail_mail.write(
                    cr, uid, msg_id,
                    {'attachment_ids': [(6, 0, attachment_ids)]}
                )
            vals = {'mail_out_ref': mail.id,
                    'mail_pec_ref': mail.mail_message_id.id}
            self.write(cr, uid, [prot.id], vals)
            mail_mail.send(cr, uid, [msg_id], context=context)
            res = mail_mail.read(
                cr, uid, [msg_id], ['state'], context=context
            )

            action_class = "history_icon mail"
            post_vars = {'subject': "Invio PEC",
                         'body': "<div class='%s'><ul><li>PEC protocollo inviato a: %s</li></ul></div>" % (
                             action_class, values['email_to']),
                         'model': "protocollo.protocollo",
                         'res_id': prot_id,
                         }

            thread_pool = self.pool.get('protocollo.protocollo')
            thread_pool.message_post(cr, uid, prot_id, type="notification", context=context, **post_vars)

            if res[0]['state'] != 'sent':
                raise openerp.exceptions.Warning(_('Errore nella \
                    notifica del protocollo, mail pec non spedita'))
            else:
                mail_message_obj = self.pool.get('mail.message')
                mail_message_obj.write(cr, uid, mail.mail_message_id.id, {'direction': 'out'})
                for sender_receiver_id in sender_receivers_pec_ids:
                    msgvals = {}
                    sender_receiver_obj = self.pool.get('protocollo.sender_receiver').browse(cr, uid,
                                                                                             sender_receiver_id,
                                                                                             context=context)
                    messaggio_pec_id = messaggio_pec_obj.create(cr, uid, {'type': 'messaggio',
                                                                          'messaggio_ref': mail.mail_message_id.id})
                    msgvals['pec_messaggio_ids'] = [(4, [messaggio_pec_id])]
                    msgvals['to_resend'] = False
                    sender_receiver_obj.write(msgvals)
        else:
            raise openerp.exceptions.Warning(_('Errore nel \
                    protocollo, si sta cercando di inviare una pec \
                    su un tipo di protocollo non pec.'))
        return True

    def _process_new_pec(self, cr, uid, ids, protocollo_obj, context=None):
        # check if waiting then resend pec mail
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]

        for prot in self.browse(cr, uid, ids):
            if prot.state in ('waiting', 'sent', 'error'):
                wf_service = netsvc.LocalService('workflow')
                wf_service.trg_validate(uid, 'protocollo.protocollo', prot.id, 'resend', cr)
        return True

    def _create_outgoing_sharedmail(self, cr, uid, prot_id, context=None):
        if context is None:
            context = {}
        prot = self.browse(cr, uid, prot_id)
        if prot.type == 'out' and prot.typology.name == 'Email':
            configurazione_ids = self.pool.get('protocollo.configurazione').search(cr, uid, [])
            configurazione = self.pool.get('protocollo.configurazione').browse(cr, uid, configurazione_ids[0])
            mail_mail = self.pool.get('mail.mail')
            ir_attachment = self.pool.get('ir.attachment')
            sender_receivers_mails = []
            sender_receivers_ids = []
            fetchmail_server_id = prot.server_sharedmail_id.id
            mail_server_obj = self.pool.get('ir.mail_server')
            mail_server_ids = mail_server_obj.search(cr, uid, [('in_server_sharedmail_id', '=', fetchmail_server_id)])
            mail_server = mail_server_obj.browse(cr, uid, mail_server_ids)

            if prot.sender_receivers:
                for sender_receiver_id in prot.sender_receivers.ids:
                    sender_receiver_obj = self.pool.get('protocollo.sender_receiver').browse(cr, uid,
                                                                                             sender_receiver_id,
                                                                                             context=context)
                    if (sender_receiver_obj.sharedmail_numero_invii == 0) or (
                            sender_receiver_obj.sharedmail_numero_invii > 0 and sender_receiver_obj.to_resend):
                        sender_receivers_mails.append(sender_receiver_obj.email)
                        sender_receivers_ids.append(sender_receiver_obj.id)

            subject = self._get_oggetto_mail_pec(cr, uid, prot.subject, prot.name,
                                                 prot.registration_date) if configurazione.rinomina_oggetto_mail_pec else prot.subject
            if configurazione.lunghezza_massima_oggetto_mail > 0:
                subject = subject[:configurazione.lunghezza_massima_oggetto_mail]

            values = {}
            values['subject'] = subject
            values['body_html'] = prot.body
            values['body'] = prot.body
            values['email_from'] = mail_server.smtp_user
            values['reply_to'] = mail_server.in_server_id.user
            values['mail_server_id'] = mail_server.id
            values['email_to'] = ','.join([sr for sr in
                                           sender_receivers_mails]
                                          )
            values['sharedmail_to'] = values['email_to']
            values['sharedmail_protocol_ref'] = prot.id
            values['sharedmail_state'] = 'protocol'
            values['sharedmail_type'] = 'sharedmail'
            values['server_sharedmail_id'] = fetchmail_server_id

            if prot.assigne_cc:
                values['email_cc'] = self._get_assigne_cc_emails(
                    cr, uid, prot_id, context)
            msg_id = mail_mail.create(cr, uid, values, context=context)
            mail = mail_mail.browse(cr, uid, msg_id, context=context)
            # manage attachments
            attachment_ids = ir_attachment.search(cr, uid,
                                                  [('res_model',
                                                    '=',
                                                    'protocollo.protocollo'),
                                                   ('res_id',
                                                    '=',
                                                    prot.id)]
                                                  )
            if attachment_ids:
                values['attachment_ids'] = [(6, 0, attachment_ids)]
                mail_mail.write(
                    cr, uid, msg_id,
                    {'attachment_ids': [(6, 0, attachment_ids)]}
                )
            vals = {'mail_out_ref': mail.id,
                    'mail_sharedmail_ref': mail.mail_message_id.id}
            self.write(cr, uid, [prot.id], vals)
            mail_mail.send(cr, uid, [msg_id], context=context)
            res = mail_mail.read(
                cr, uid, [msg_id], ['state'], context=context
            )

            action_class = "history_icon mail"
            post_vars = {'subject': "Invio E-mail",
                         'body': "<div class='%s'><ul><li>E-mail protocollo inviata a: %s</li></ul></div>" % (
                             action_class, values['email_to']),
                         'model': "protocollo.protocollo",
                         'res_id': prot_id,
                         }

            thread_pool = self.pool.get('protocollo.protocollo')
            thread_pool.message_post(cr, uid, prot_id, type="notification", context=context, **post_vars)

            if res[0]['state'] != 'sent':
                raise openerp.exceptions.Warning(_('Errore nella \
                    notifica del protocollo, mail non spedita'))
            else:
                mail_message_obj = self.pool.get('mail.message')
                mail_message_obj.write(cr, uid, mail.mail_message_id.id, {'direction_sharedmail': 'out'})
                for sender_receiver_id in sender_receivers_ids:
                    msgvals = {}
                    sender_receiver_obj = self.pool.get('protocollo.sender_receiver').browse(cr, uid,
                                                                                             sender_receiver_id,
                                                                                             context=context)
                    msgvals['to_resend'] = False
                    msgvals['sharedmail_numero_invii'] = int(sender_receiver_obj.sharedmail_numero_invii) + 1
                    sender_receiver_obj.write(msgvals)

        else:
            raise openerp.exceptions.Warning(_('Errore nel \
                    protocollo, si sta cercando di inviare una pec \
                    su un tipo di protocollo non pec.'))
        return True

    def get_mail_server(self, cr, uid, context=None):
        mail_server_obj = self.pool.get('ir.mail_server')
        fetch_server_obj = self.pool.get('fetchmail.server')
        if 'sharedmail_messages' in context:
            fetch_server_ids = fetch_server_obj.get_fetch_server_sharedmail(cr, uid, context)
        if 'pec_messages' in context:
            fetch_server_ids = fetch_server_obj.get_fetch_server_pec(cr, uid, context)
        if not fetch_server_ids:
            raise openerp.exceptions.Warning(_('Errore nella \
                notifica del protocollo, nessun server pec associato all\'utente'))
        if 'sharedmail_messages' in context:
            mail_server_ids = mail_server_obj.get_mail_server_sharedmail(cr, uid, fetch_server_ids[0], context)
        if 'pec_messages' in context:
            mail_server_ids = mail_server_obj.get_mail_server_pec(cr, uid, fetch_server_ids[0], context)
        if not mail_server_ids:
            raise openerp.exceptions.Warning(_('Errore nella \
                notifica del protocollo, manca il server di posta in uscita'))
        mail_server = mail_server_obj.browse(cr, uid, mail_server_ids[0])
        return mail_server

    def action_mail_pec_send(self, cr, uid, ids, *args):

        for prot_id in ids:
            prot = self.pool.get('protocollo.protocollo').browse(cr, uid, prot_id)
            # if prot.state == 'sent': SOLUZIONE NON APPLICABILE. CREA PROBLEMI NEL REINVIO
            #     raise openerp.exceptions.Warning(_('Il messaggio è già stato inviato in precedenza: ricaricare la pagina'))
            if prot.pec:
                context = {'pec_messages': True}
                self._create_outgoing_pec(cr, uid, prot_id, context=context)
            else:
                context = {'sharedmail_messages': True}
                self._create_outgoing_sharedmail(cr, uid, prot_id, context=context)
        return True

    def action_resend(self, cr, uid, ids, context=None):
        protocollo_obj = self.pool.get('protocollo.protocollo')
        protocollo_obj._process_new_pec(cr, uid, ids, protocollo_obj, context)

    def mail_message_id_get(self, cr, uid, ids, *args):
        res = {}
        if not ids:
            return []
        protocol_obj = self.pool.get('protocollo.protocollo')
        for prot in protocol_obj.browse(cr, uid, ids):
            if prot.pec:
                res[prot.id] = [prot.mail_pec_ref.id]
            else:
                res[prot.id] = [prot.mail_sharedmail_ref.id]
        _logger.info('mail_message_id_get')
        return res[ids[0]]

    def test_mail_message(self, cr, uid, ids, *args):
        _logger.info('test_mail_message')
        res = self.mail_message_id_get(cr, SUPERUSER_ID, ids)
        if not res:
            return False
        mail_message_obj = self.pool.get('mail.message')
        mail_message = mail_message_obj.browse(cr, SUPERUSER_ID, res[0])
        ok = mail_message.message_ok and not \
            mail_message.error
        return ok

    def check_all_mail_messages(self, cr, uid, ids, *args):
        _logger.info('check_all_mail_messages')
        res = self.mail_message_id_get(cr, SUPERUSER_ID, ids)
        if not res:
            return False
        mail_message_obj = self.pool.get('mail.message')
        mail_message = mail_message_obj.browse(cr, SUPERUSER_ID, res[0])
        protocollo_obj = self.pool.get('protocollo.protocollo')
        protocollo = protocollo_obj.browse(cr, SUPERUSER_ID, mail_message.pec_protocol_ref.id)
        for sr in protocollo.sender_receivers.ids:
            sender_receiver_obj = self.pool.get('protocollo.sender_receiver').browse(cr, SUPERUSER_ID, sr)
            if not sender_receiver_obj.pec_consegna_status:
                return False
        return True

    def test_error_mail_message(self, cr, uid, ids, *args):
        _logger.info('test_error_mail_message')
        res = self.mail_message_id_get(cr, SUPERUSER_ID, ids)
        if not res:
            return False
        mail_message_obj = self.pool.get('mail.message')
        mail_message = mail_message_obj.browse(cr, SUPERUSER_ID, res[0])
        return mail_message.error

    def check_journal(self, cr, uid, ids, *args):
        journal_obj = self.pool.get('protocollo.journal')
        journal_id = journal_obj.search(cr, uid, [('state', '=', 'closed'), ('date', '=', time.strftime(DSDT))])
        if journal_id:
            raise orm.except_orm(
                _('Attenzione!'),
                _('Registro Giornaliero di protocollo chiuso! Non e\' possibile inserire nuovi protocolli')
            )
        return True

    # def has_offices(self, cr, uid, ids, *args):
    #     for protocol in self.browse(cr, uid, ids):
    #         if (
    #                 protocol.assegnatari_competenza_uffici_ids or protocol.assegnatari_competenza_dipendenti_ids) and protocol.type == 'in':
    #             return True
    #     return False

    def prendi_in_carico(self, cr, uid, ids, context=None):
        rec = self.pool.get('res.users').browse(cr, uid, uid)

        try:
            check_permission = self.browse(cr, uid, ids).prendi_in_carico_visibility
            if check_permission == True:
                action_class = "history_icon taken"
                post_vars = {'subject': "Presa in carico",
                             'body': "<div class='%s'><ul><li>Protocollo preso in carico da <span style='color:#009900;'>%s</span></li></ul></div>" % (
                                 action_class, rec.name),
                             'model': "protocollo.protocollo",
                             'res_id': ids[0],
                             }

                thread_pool = self.pool.get('protocollo.protocollo')
                thread_pool.message_post(cr, uid, ids[0], type="notification", context=context, **post_vars)

                # l'invio della notifica avviene prima della modifica dello stato, perchè se fatta dopo, in alcuni casi,
                # potrebbe non avere più i permessi di scrittura sul protocollo
                # self.pool.get('protocollo.stato.dipendente').modifica_stato_dipendente(cr, uid, ids, 'preso')
                self.pool.get('protocollo.assegnazione').modifica_stato_assegnazione(cr, uid, ids, 'preso')
            else:
                raise orm.except_orm(_('Azione Non Valida!'), _('Non sei più assegnatario di questo protocollo'))
        except Exception as e:
            raise orm.except_orm(_('Azione Non Valida!'), _('Non sei più assegnatario di questo protocollo'))
        return True

    def rifiuta_presa_in_carico(self, cr, uid, ids, motivazione, context=None):
        rec = self.pool.get('res.users').browse(cr, uid, uid)
        try:
            check_permission = self.browse(cr, uid, ids).rifiuta_visibility
            if check_permission == True:
                action_class = "history_icon refused"
                post_vars = {
                    'subject': "Rifiuto assegnazione: %s" % motivazione,
                    'body': "<div class='%s'><ul><li>Assegnazione rifiutata da <span style='color:#990000;'>%s</span></li></ul></div>" % (action_class, rec.name),
                    'model': "protocollo.protocollo",
                    'res_id': ids[0]
                }

                thread_pool = self.pool.get('protocollo.protocollo')
                thread_pool.message_post(cr, uid, ids[0], type="notification", context=context, **post_vars)

                # l'invio della notifica avviene prima della modifica dello stato, perchè se fatta dopo, in alcuni casi,
                # potrebbe non avere più i permessi di scrittura sul protocollo
                #self.pool.get('protocollo.stato.dipendente').modifica_stato_dipendente(cr, uid, ids, 'rifiutato')
                self.pool.get('protocollo.assegnazione').modifica_stato_assegnazione(cr, uid, ids, 'rifiutato')
            else:
                raise orm.except_orm(_('Attenzione!'), _('Non sei uno degli assegnatari del protocollo!'))
        except Exception as e:
            raise orm.except_orm(_('Attenzione!'), _('Non sei uno degli assegnatari del protocollo!'))
        return True

    def _verifica_dati_sender_receiver(self, cr, uid, vals, context):
        if vals and vals.has_key('senders'):
            for mittente in vals['senders']:
                if mittente[0] == 0:
                    mittente_data = mittente[2]
                    mittente_data['source'] = 'sender'
        if vals and vals.has_key('receivers'):
            for destinatario in vals['receivers']:
                if destinatario[0] == 0:
                    destinatario_data = destinatario[2]
                    destinatario_data['source'] = 'receiver'
        return vals

    def create(self, cr, uid, vals, context=None):
        vals = self._verifica_dati_sender_receiver(cr, uid, vals, context)
        protocollo_id = super(protocollo_protocollo, self).create(cr, uid, vals, context=context)
        return protocollo_id

    def write(self, cr, uid, ids, vals, context=None):
        vals = self._verifica_dati_sender_receiver(cr, uid, vals, context)
        protocollo_id = super(protocollo_protocollo, self).write(cr, uid, ids, vals, context=context)
        return protocollo_id

    def unlink(self, cr, uid, ids, context=None):
        stat = self.read(cr, uid, ids, ['state'], context=context)
        unlink_ids = []
        for t in stat:
            if t['state'] in ('draft'):
                unlink_ids.append(t['id'])
            else:
                raise orm.except_orm(_('Azione Non Valida!'),
                                     _('Solo i protocolli in stato \
                                     compilazione possono essere eliminati.')
                                     )
        return super(protocollo_protocollo, self).unlink(
            cr, uid, unlink_ids, context=context)

    def copy(self, cr, uid, pid, default=None, context=None):
        raise orm.except_orm(_('Azione Non Valida!'),
                             _('Impossibile duplicare un protocollo')
                             )
        return True

    def carica_documento_principale(self, cr, uid, protocollo_id, datas, datas_fname, datas_description, context=None):

        configurazione_ids = self.pool.get('protocollo.configurazione').search(cr, uid, [])
        configurazione = self.pool.get('protocollo.configurazione').browse(cr, uid, configurazione_ids[0])
        mimetype = magic.from_buffer(base64.b64decode(datas), mime=True)

        protocollo_obj = self.pool.get('protocollo.protocollo')
        attachment_obj = self.pool.get('ir.attachment')

        attachment_ids = attachment_obj.search(cr, uid, [
            ('res_model', '=', 'protocollo.protocollo'),
            ('res_id', '=', protocollo_id),
            ('is_protocol', '=', True)
        ])

        if attachment_ids:
            attachments = attachment_obj.browse(cr, uid, attachment_ids)
            for attachment in attachments:
                if attachment.is_main:
                    attachment_obj.unlink(cr, SUPERUSER_ID, attachment.id)

        attachment_id = attachment_obj.create(
            cr, uid,
            {
                'name': datas_fname,
                'datas': datas,
                'datas_fname': datas_fname,
                'datas_description': datas_description,
                'res_model': 'protocollo.protocollo',
                'is_protocol': True,
                'res_id': protocollo_id,
            }
        )
        protocollo_obj.write(cr, uid, protocollo_id, {'doc_id': attachment_id, 'mimetype': mimetype})

        for prot in self.browse(cr, uid, protocollo_id):
            if prot.state == 'registered':
                try:
                    vals = {}
                    prot_number = prot.name
                    # prot_number = self.name_get(cr, uid, protocollo_id, context=None)
                    prot_complete_name = prot.name
                    prot_date = fields.datetime.now()
                    if prot.doc_id:
                        if prot.mimetype == 'application/pdf' and configurazione.genera_segnatura:
                            self._sign_doc(
                                cr, uid, prot,
                                prot_complete_name, prot_date
                            )
                        fingerprint = self._create_protocol_attachment(
                            cr,
                            uid,
                            prot,
                            prot_number,
                            prot_date
                        )
                        vals['fingerprint'] = fingerprint
                        vals['datas'] = 0
                    vals['name'] = prot_number
                    vals['registration_date'] = prot_date
                    now = datetime.datetime.now()
                    vals['year'] = now.year
                    esito = self.write(cr, uid, [prot.id], vals)

                    # Generazione della segnatura spostata al momento dell'invio della PEC
                    # if configurazione.genera_xml_segnatura:
                    #     segnatura_xml = SegnaturaXML(prot, prot_number, prot_date, cr, uid)
                    #     xml = segnatura_xml.generate_segnatura_root()
                    #     etree_tostring = etree.tostring(xml, pretty_print=True)
                    #     vals['xml_signature'] = etree_tostring

                    action_class = "history_icon upload"
                    post_vars = {'subject': "Upload Documento",
                                 'body': "<div class='%s'><ul><li>Aggiunto documento principale: %s</li></ul></div>" % (
                                     action_class, datas_fname),
                                 'model': "protocollo.protocollo",
                                 'res_id': prot.id,
                                 }

                    thread_pool = self.pool.get('protocollo.protocollo')
                    thread_pool.message_post(cr, uid, prot.id, type="notification", context=context, **post_vars)

                    self.write(cr, uid, [prot.id], vals)
                except Exception as e:
                    _logger.error(e)
                    raise openerp.exceptions.Warning(_('Errore nella \
                                   registrazione del protocollo'))
                continue

            return True

    def allega_segnatura_xml(self, cr, uid, protocollo_id, xml_segnatura, context=None):
        xml_segnatura_datas = base64.b64encode(xml_segnatura)
        attachment_obj = self.pool.get('ir.attachment')
        attachment_obj.create(
            cr, uid,
            {
                'name': 'Segnatura.xml',
                'datas': xml_segnatura_datas,
                'datas_fname': 'Segnatura.xml',
                'datas_description': 'Segnatura.xml',
                'res_model': 'protocollo.protocollo',
                'is_protocol': True,
                'res_id': protocollo_id,
            }
        )

    def carica_documenti_secondari(self, cr, uid, protocollo_id, file_data_list, context=None):
        attachment_obj = self.pool.get('ir.attachment')

        attachment_ids = attachment_obj.search(cr, uid, [
            ('res_model', '=', 'protocollo.protocollo'),
            ('res_id', '=', protocollo_id),
            ('is_protocol', '=', True)
        ])
        if attachment_ids:
            attachments = attachment_obj.browse(cr, uid, attachment_ids)
            for attachment in attachments:
                if not attachment.is_main:
                    attachment_obj.unlink(cr, SUPERUSER_ID, attachment.id)

        nomi_allegati = ''
        counter = 0
        for file_data in file_data_list:
            attachment_obj.create(
                cr, uid,
                {
                    'name': file_data['datas_fname'],
                    'datas': file_data['datas'],
                    'datas_fname': file_data['datas_fname'],
                    'datas_description': file_data['datas_description'],
                    'res_model': 'protocollo.protocollo',
                    'is_protocol': True,
                    'res_id': protocollo_id,
                }
            )
            nomi_allegati += file_data['datas_fname']
            if counter < len(file_data_list) - 1:
                nomi_allegati += ', '
            counter += 1

        text = 'o' if counter == 1 else 'i'

        if counter > 0:
            action_class = "history_icon upload"
            post_vars = {'subject': "Upload Documento",
                         'body': "<div class='%s'><ul><li>Aggiunt%s %d allegat%s: <i>%s</i></li></ul></div>" % (
                             action_class, text, len(file_data_list), text, nomi_allegati),
                         'model': "protocollo.protocollo",
                         'res_id': protocollo_id,
                         }

            thread_pool = self.pool.get('protocollo.protocollo')
            thread_pool.message_post(cr, uid, protocollo_id, type="notification", context=context, **post_vars)

    def _get_oggetto_mail_pec(self, cr, uid, subject, prot_name, prot_registration_date):
        prefix = "Prot. n. " + prot_name + " del " + prot_registration_date + " - "
        subject_text = prefix + subject
        return subject_text

    def _get_name_documento_allegato(self, cr, uid, attachment_name, prot_number, prefix, is_main):

        reg_date = fields.datetime.now()[0:10]
        doc_type = 'Documento' if is_main else 'Allegato'
        att_name = attachment_name.split('.')[0]
        gext = '.' + attachment_name.split('.')[-1]
        att_ext = gext in mimetypes.types_map and gext or ''
        complete_prefix = prefix + '_' + prot_number + '_' + reg_date + '_' + doc_type
        if attachment_name.find(complete_prefix) == -1:
            file_name = complete_prefix + "_" + att_name + att_ext
        else:
            return attachment_name
        return file_name

    # @api.cr_uid_ids_context
    # Gestione dello Storico attraverso Mail Thread
    def message_post(self, cr, uid, thread_id, body='', subject=None, type='notification',
                     subtype=None, parent_id=False, attachments=None, context=None,
                     content_subtype='html', **kwargs):
        if not context:
            context = {}
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, thread_id)
        if protocollo.state == 'draft' and str(subject).find('Registrazione') != 0 and str(subject).find(
                'Errore Generazione') != 0 and context.has_key('is_mailpec_to_draft') == False:
            pass
        else:
            return super(protocollo_protocollo, self).message_post(
                cr, uid, thread_id, body=body,
                subject=subject, type=type,
                subtype=subtype, parent_id=parent_id,
                attachments=attachments, context=context,
                content_subtype=content_subtype, **kwargs)


class protocollo_journal(orm.Model):
    _name = 'protocollo.journal'
    _description = 'Registro Giornaliero'

    _order = 'name desc'

    STATE_SELECTION = [
        ('draft', 'Bozza'),
        ('closed', 'Chiuso'),
    ]

    _columns = {
        'name': fields.datetime('Data Evento', required=True, readonly=True),
        'date': fields.date('Data Registro', required=True, readonly=True),
        'user_id': fields.many2one('res.users', 'Responsabile', readonly=True),
        'protocol_ids': fields.many2many(
            'protocollo.protocollo',
            'protocollo_journal_rel',
            'journal_id',
            'protocollo_id',
            'Protocollazioni della Giornata',
            required=False,
            readonly=True),
        'state': fields.selection(
            STATE_SELECTION,
            'Status',
            readonly=True,
            help="Lo stato del protocollo.",
            select=True,
        ),
        'aoo_id': fields.many2one('protocollo.aoo', 'AOO', ondelete="cascade", required=True),
    }

    _defaults = {
        'name': time.strftime(DSDF),
        'date': fields.date.context_today,
        'user_id': lambda obj, cr, uid, context: uid,
        'state': 'draft',
    }

    def _create_journal(self, cr, uid, ids=False, context=None):
        aoo_ids = self.pool.get('protocollo.aoo').search(cr, uid, [])

        if aoo_ids and len(aoo_ids) > 0:
            for aoo_id in aoo_ids:
                journal_obj = self.pool.get('protocollo.journal')
                journal_ids = []
                last_journal_id = journal_obj.search(
                    cr, uid,
                    [
                        ('aoo_id', '=', aoo_id),
                        ('state', '=', 'closed'),
                        ('date', '<', time.strftime(DSDT))
                    ], order='date desc', limit=1)

                protocollo_obj = self.pool.get('protocollo.protocollo')
                if last_journal_id:
                    today = datetime.datetime.now()
                    last_journal = journal_obj.browse(cr, uid, last_journal_id[0])
                    last_journal_date = datetime.datetime.strptime(
                        last_journal.date,
                        DSDT
                    )
                    num_days = (today - last_journal_date).days
                    if num_days in (0, 1):
                        continue
                    for day in range(1, num_days):
                        last_date = (last_journal_date + datetime.timedelta(days=day))
                        protocol_ids = protocollo_obj.search(cr, uid, [
                            ('aoo_id', '=', aoo_id),
                            ('state', 'in', ['registered', 'notified', 'sent', 'waiting', 'error', 'canceled']),
                            ('registration_date', '>', last_date.strftime(DSDT) + ' 00:00:00'),
                            ('registration_date', '<', last_date.strftime(DSDT) + ' 23:59:59'),
                        ])
                        try:
                            journal_id = journal_obj.create(
                                cr, uid,
                                {
                                    'name': last_date.strftime(DSDF),
                                    'aoo_id': aoo_id,
                                    'user_id': uid,
                                    'protocol_ids': [[6, 0, protocol_ids]],
                                    'date': last_date.strftime(DSDT),
                                    'state': 'closed',
                                }
                            )
                            journal_ids.append(journal_id)
                        except Exception as e:
                            _logger.exception("Unable to create Protocol Journal %s" % last_date.strftime(DSDT))
                            _logger.info(e)
                            return False
                else:
                    today = datetime.datetime.now()
                    yesterday = today + datetime.timedelta(days=-1)
                    protocol_ids = protocollo_obj.search(cr, uid, [
                        ('aoo_id', '=', aoo_id),
                        ('state', 'in', ['registered', 'notified', 'sent', 'waiting', 'error', 'canceled']),
                        ('registration_date', '>', yesterday.strftime(DSDT) + ' 00:00:00'),
                        ('registration_date', '<', yesterday.strftime(DSDT) + ' 23:59:59'),
                    ])
                    try:
                        journal_id = journal_obj.create(
                            cr, uid,
                            {
                                'name': yesterday.strftime(DSDF),
                                'aoo_id': aoo_id,
                                'user_id': uid,
                                'protocol_ids': [[6, 0, protocol_ids]],
                                'date': yesterday.strftime(DSDT),
                                'state': 'closed',
                            }
                        )
                        journal_ids.append(journal_id)
                    except Exception as e:
                        _logger.exception("Unable to create Protocol Journal %s" % time.strftime(DSDT))
                        _logger.info(e)
                        return False
                if len(journal_ids) > 0:
                    for journal_id in journal_ids:
                        report_data, format = render_report(cr, uid, [journal_id], 'seedoo_protocollo.journal_qweb', {},
                                                            context=context)
                        # attach_vals = {
                        #     'name': 'Registro Giornaliero',
                        #     'datas_fname': 'Registro Giornaliero.pdf',
                        #     'res_model': 'protocollo.journal',
                        #     'res_id': journal_id,
                        #     'datas': base64.encodestring(report_data),
                        #     'file_type': format
                        # }
                        # self.pool.get('ir.attachment').create(cr, uid, attach_vals)
        return True


class protocollo_emergency_registry_line(orm.Model):
    _name = 'protocollo.emergency.registry.line'
    _columns = {
        'name': fields.char('Numero Riservato', size=256, required=True, readonly=True),
        'protocol_id': fields.many2one('protocollo.protocollo', 'Protocollo Registrato', readonly=True),
        'emergency_number': fields.related('protocol_id', 'emergency_protocol', type='char',
                                           string='Protocollo Emergenza', readonly=True),
        'emergency_id': fields.many2one('protocollo.emergency.registry', 'Registro Emergenza'),
    }


class protocollo_emergency_registry(orm.Model):
    _name = 'protocollo.emergency.registry'

    STATE_SELECTION = [
        ('draft', 'Bozza'),
        ('closed', 'Chiuso'),
    ]

    _columns = {
        'name': fields.char('Causa Emergenza', size=256, required=True, readonly=True),
        'user_id': fields.many2one('res.users', 'Responsabile', readonly=True),
        'date_start': fields.datetime('Data Inizio Emergenza', required=True, readonly=True),
        'date_end': fields.datetime('Data Fine Emergenza', required=True, readonly=True),
        'aoo_id': fields.many2one('protocollo.aoo', 'AOO', required=True),
        'registry': fields.related('aoo_id', 'registry_id', type='many2one', relation='protocollo.registry',
                                   string='Registro', store=True, readonly=True),
        'emergency_ids': fields.one2many('protocollo.emergency.registry.line', 'emergency_id',
                                         'Numeri Riservati e Protocollazioni', required=False, readonly=True, ),
        'state': fields.selection(STATE_SELECTION, 'Status', readonly=True, help="Lo stato del protocollo.",
                                  select=True),
    }

    _defaults = {
        'user_id': lambda obj, cr, uid, context: uid,
        'state': 'draft',
    }

class Wizard(object):

    def __init__(self):
        self.count_rifiutati = 100
        self.count_presi_in_carico = 100
        self.count_registrati = 100
        self.count_bozza = 100


class LockerSingleton():
    lock = threading.RLock()