# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from lxml import etree

from openerp import SUPERUSER_ID, api
from openerp.osv import orm, fields, osv
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DSDT
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DSDF
from util.selection import *
import openerp.exceptions
from openerp import netsvc
from openerp.report import render_report
import re
import os
import subprocess
import shutil
import mimetypes
import base64
import magic
import pytz
import datetime
import time
import logging

from ..segnatura.segnatura_xml import SegnaturaXML
from ..segnatura.conferma_xml import ConfermaXML
from ..segnatura.annullamento_xml import AnnullamentoXML
_logger = logging.getLogger(__name__)
mimetypes.init()


class protocollo_typology(orm.Model):
    _name = 'protocollo.typology'
    _columns = {
        'name': fields.char('Nome', size=256, required=True),
        'pec': fields.boolean('PEC'),
        'aoo_id': fields.many2one('protocollo.aoo', 'AOO', required=True),
    }


class protocollo_sender_receiver(orm.Model):
    _name = 'protocollo.sender_receiver'

    def on_change_type(self, cr, uid, ids, type):
        res = {}
        res['value'] = {
            'partner_id': False,
            'pa_type': False,
            'ident_code': False,
            'ammi_code': False
        }
        return res

    def on_change_pa_type(self, cr, uid, ids, pa_type):
        res = {'value': {}}

        if pa_type == 'aoo':
            res['value']['super_type'] = 'pa'
        elif pa_type == 'uo':
            res['value']['super_type'] = 'aoo'

        return res

    def on_change_partner(self, cr, uid, ids, partner_id, context=None):
        values = {}
        if partner_id:
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context)
            values = {
                # 'type': partner.is_company and 'individual' or 'legal',
                'pa_type': partner.pa_type,
                'ident_code': partner.ident_code,
                'ammi_code': partner.ammi_code,
                'ipa_code': partner.ipa_code,
                'name': partner.name,
                'street': partner.street,
                'city': partner.city,
                'country_id': (
                    partner.country_id and
                    partner.country_id.id or False),
                'email': partner.email,
                'phone': partner.phone,
                'mobile': partner.mobile,
                'pec_mail': partner.pec_mail,
                'fax': partner.fax,
                'zip': partner.zip,
                'save_partner': False,
            }
        else:
            values = {
                'pa_type': False,
                'ident_code': False,
                'ammi_code': False,
                'ipa_code': False,
                'name': False,
                'street': False,
                'city': False,
                'country_id': False,
                'email': False,
                'phone': False,
                'mobile': False,
                'pec_mail': False,
                'fax': False,
                'zip': False,
                'save_partner': False,
            }
        return {'value': values}

    def on_change_pec_mail(self, cr, uid, ids, pec_mail, save_partner, context=None):
        res = {'value': {}}
        if pec_mail and save_partner:
            self.pool.get('res.partner').check_email_field(cr, uid, [('pec_mail', '=', pec_mail)], 'Mail PEC', pec_mail)
        elif pec_mail:
            self.pool.get('res.partner').check_email_validity('Mail PEC', pec_mail)
        return res

    def on_change_email(self, cr, uid, ids, email, save_partner, context=None):
        res = {'value': {}}
        if email and save_partner:
            self.pool.get('res.partner').check_email_field(cr, uid, [('email', '=', email)], 'Mail', email)
        elif email:
            self.pool.get('res.partner').check_email_validity('Mail', email)
        return res

    def on_change_save_partner(self, cr, uid, ids, pec_mail, email, save_partner, context=None):
        res = {'value': {}}
        errors = ''

        pec_mail_error = ''
        if pec_mail and save_partner:
            pec_mail_error = self.pool.get('res.partner').check_email_field(cr, uid, [('pec_mail', '=', pec_mail)], 'Mail PEC', pec_mail, False)
        elif pec_mail:
            pec_mail_error = self.pool.get('res.partner').check_email_validity('Mail PEC', pec_mail, False)
        if pec_mail_error:
            errors = errors + '\n' + pec_mail_error

        email_error = ''
        if email and save_partner:
            email_error = self.pool.get('res.partner').check_email_field(cr, uid, [('email', '=', email)], 'Mail', email, False)
        elif email:
            email_error = self.pool.get('res.partner').check_email_validity('Mail', email, False)
        if email_error:
            errors = errors + '\n' + email_error

        self.pool.get('res.partner').dispatch_email_error(errors)
        return res

    def _get_invio_status(self, cr, uid, ids, field, arg, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        res = dict.fromkeys(ids, False)
        for sr in self.browse(cr, uid, ids):
            if sr.protocollo_id.id:
                protocollo_obj = self.pool.get('protocollo.protocollo')
                for prot in protocollo_obj.browse(cr, uid, sr.protocollo_id.id):
                    messaggio_pec_obj = self.pool.get("protocollo.messaggio.pec")
                    for messaggio_pec_id in sr.pec_messaggio_ids.ids:
                        messaggio_pec = messaggio_pec_obj.browse(cr, uid, messaggio_pec_id)
                        if prot.state in ("waiting", "sent", "error", "notified", "canceled") and messaggio_pec.type in ("messaggio"):
                            res[sr.id] = True
        return res

    def _get_accettazione_status(self, cr, uid, ids, field, arg, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        res = dict.fromkeys(ids, False)
        for sr in self.browse(cr, uid, ids):
            if sr.protocollo_id.id:
                protocollo_obj = self.pool.get('protocollo.protocollo')
                for prot in protocollo_obj.browse(cr, uid, sr.protocollo_id.id):
                    messaggio_pec_obj = self.pool.get("protocollo.messaggio.pec")
                    for messaggio_pec_id in sr.pec_messaggio_ids.ids:
                        messaggio_pec = messaggio_pec_obj.browse(cr, uid, messaggio_pec_id)
                        if prot.state in ("waiting", "sent", "error", "notified", "canceled") and messaggio_pec.type in ("messaggio") and messaggio_pec.accettazione_ref.id:
                            res[sr.id] = True
        return res


    def _get_consegna_status(self, cr, uid, ids, field, arg, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        res = dict.fromkeys(ids, False)
        for sr in self.browse(cr, uid, ids):
            if sr.protocollo_id.id:
                protocollo_obj = self.pool.get('protocollo.protocollo')
                for prot in protocollo_obj.browse(cr, uid, sr.protocollo_id.id):
                    messaggio_pec_obj = self.pool.get("protocollo.messaggio.pec")
                    for messaggio_pec_id in sr.pec_messaggio_ids.ids:
                        messaggio_pec = messaggio_pec_obj.browse(cr, uid, messaggio_pec_id)
                        if prot.state in ("waiting", "sent", "error", "notified", "canceled") and messaggio_pec.type in ("messaggio") and messaggio_pec.consegna_ref.id:
                            res[sr.id] = True
        return res

    def _get_errore_consegna_status(self, cr, uid, ids, field, arg, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        res = dict.fromkeys(ids, False)
        for sr in self.browse(cr, uid, ids):
            if sr.protocollo_id.id:
                protocollo_obj = self.pool.get('protocollo.protocollo')
                for prot in protocollo_obj.browse(cr, uid, sr.protocollo_id.id):
                    messaggio_pec_obj = self.pool.get("protocollo.messaggio.pec")
                    for messaggio_pec_id in sr.pec_messaggio_ids.ids:
                        messaggio_pec = messaggio_pec_obj.browse(cr, uid, messaggio_pec_id)
                        if prot.state in ("waiting", "sent", "error", "notified", "canceled") and messaggio_pec.type in ("messaggio") and messaggio_pec.errore_consegna_ref.id:
                            res[sr.id] = True
        return res

    def _get_default_protocollo_id(self, cr, uid, context=None):
        if context and 'is_add_pec_receiver' in context and context['is_add_pec_receiver']:
            if context.has_key('protocollo_id') and context['protocollo_id']:
                return context['protocollo_id']

    def _get_default_source(self, cr, uid, context=None):
        if context and 'is_add_pec_receiver' in context and context['is_add_pec_receiver']:
            return 'receiver'
        return None

    def _get_add_pec_receiver_visibility(self, cr, uid, context=None):
        if context and 'is_add_pec_receiver' in context and context['is_add_pec_receiver']:
            return True
        return False

    _columns = {
        'protocollo_id': fields.many2one('protocollo.protocollo', 'Protocollo'),
        'source': fields.selection([
                ('sender', 'Mittente'),
                ('receiver', 'Destinatario'),
        ], 'Mittente/Destinatario', size=32, required=True, readonly=True),

        'type': fields.selection(
            [
                ('individual', 'Persona Fisica'),
                ('legal', 'Azienda Privata'),
                ('government', 'Amministrazione Pubblica')
            ], 'Tipologia', size=32, required=True),

        'pa_type': fields.selection(
            [
                ('pa', 'Amministrazione Principale'),
                ('aoo', 'Area Organizzativa Omogenea'),
                ('uo', 'Unità Organizzativa')],
            'Tipologia amministrazione', size=5, required=False),

        'ident_code': fields.char('Codice AOO', size=256, required=False),
        'ammi_code': fields.char('Codice iPA', size=256, required=False),
        'ipa_code': fields.char('Codice Unità Organizzativa', size=256, required=False),
        'save_partner': fields.boolean('Salva', help='Se spuntato salva i dati in anagrafica.'),
        'partner_id': fields.many2one('res.partner', 'Copia Anagrafica da Rubrica', domain="[('legal_type','=',type)]"),
        'name': fields.char('Nome Cognome/Ragione Sociale', size=512, required=True),
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
        'send_type': fields.many2one('protocollo.typology', 'Canale di Spedizione'),
        'send_date': fields.date('Data Spedizione'),
        'protocol_state': fields.related('protocollo_id', 'state', type='char', string='State', readonly=True),
        'protocol_pec': fields.related('protocollo_id', 'pec', type='boolean', string='Tipo PEC', readonly=True),
        'add_pec_receiver_visibility': fields.boolean('Button Visibility', readonly=True),
        'pec_ref': fields.many2one('protocollo.messaggio.pec', 'Messaggio PEC'),# campo pec_ref da eliminare
        'pec_messaggio_ids': fields.many2many('protocollo.messaggio.pec', 'protocollo_sender_receiver_messaggio_pec_rel', 'sender_receiver_id', 'messaggio_pec_id', 'Messaggi PEC'),
        'pec_invio_status': fields.function(_get_invio_status, type='boolean', string='Inviata'),
        'pec_accettazione_status': fields.function(_get_accettazione_status, type='boolean', string='Accettata'),
        'pec_consegna_status': fields.function(_get_consegna_status, type='boolean', string='Consegnata'),
        'pec_errore_consegna_status': fields.function(_get_errore_consegna_status, type='boolean', string='Errore Consegna'),
    }

    _defaults = {
        'type': 'individual',
        'protocollo_id':_get_default_protocollo_id,
        'source':_get_default_source,
        'add_pec_receiver_visibility': _get_add_pec_receiver_visibility,
    }

    def check_field_in_create(self, cr, uid, vals):
        partner_obj = self.pool.get('res.partner')
        errors = ''

        if vals.has_key('pec_mail') and vals['pec_mail']:
            pec_mail_error = ''
            if vals.has_key('save_partner') and vals['save_partner']:
                pec_mail_error = partner_obj.check_email_field(cr, uid, [('pec_mail', '=', vals['pec_mail'])],
                                                               'Mail PEC', vals['pec_mail'], False)
            else:
                pec_mail_error = partner_obj.check_email_validity('Mail PEC', vals['pec_mail'], False)
            if pec_mail_error:
                errors = errors + '\n' + pec_mail_error

        if vals.has_key('email') and vals['email']:
            email_error = ''
            if vals.has_key('save_partner') and vals['save_partner']:
                email_error = partner_obj.check_email_field(cr, uid, [('email', '=', vals['email'])],
                                                     'Mail', vals['email'], False)
            else:
                email_error = partner_obj.check_email_validity('Mail', vals['email'], False)
            if email_error:
                errors = errors + '\n' + email_error

        partner_obj.dispatch_email_error(errors)

    def check_field_in_write(self, cr, uid, ids, vals):
        partner_obj = self.pool.get('res.partner')
        errors = ''

        sender_receivers_vals = self.read(cr, uid, ids, ['id', 'pec_mail', 'email', 'save_partner'])
        if vals.has_key('pec_mail') or vals.has_key('email') or vals.has_key('save_partner'):
            for sender_receiver_vals in sender_receivers_vals:
                save_partner = sender_receiver_vals['save_partner']
                if vals.has_key('save_partner'):
                    save_partner = vals['save_partner']

                pec_mail = sender_receiver_vals['pec_mail']
                if vals.has_key('pec_mail'):
                    pec_mail = vals['pec_mail']
                pec_mail_error = ''
                if pec_mail and save_partner:
                    pec_mail_error = partner_obj.check_email_field(cr, uid, [('id', '!=', sender_receiver_vals['id']), ('pec_mail', '=', pec_mail)],
                                      'Mail PEC', pec_mail, False)
                elif pec_mail:
                    pec_mail_error = partner_obj.check_email_validity('Mail PEC', pec_mail, False)
                if pec_mail_error:
                    errors = errors + '\n' + pec_mail_error

                email = sender_receiver_vals['email']
                if vals.has_key('email'):
                    email = vals['email']
                email_error = ''
                if email and save_partner:
                    email_error = partner_obj.check_email_field(cr, uid, [('id', '!=', sender_receiver_vals['id']), ('email', '=', email)],
                                      'Mail', email, False)
                elif email:
                    email_error = partner_obj.check_email_validity('Mail', email, False)
                if email_error:
                    errors = errors + '\n' + email_error

                partner_obj.dispatch_email_error(errors)

    def create(self, cr, uid, vals, context=None):
        self.check_field_in_create(cr, uid, vals)
        sender_receiver = super(protocollo_sender_receiver, self).create(cr, uid, vals, context=context)
        sender_receiver_obj = self.browse(cr, uid, sender_receiver)

        if sender_receiver_obj.protocollo_id.state != "draft":
            action_class = "history_icon update"
            body = "<div class='%s'><ul><li>" \
                   "Aggiunto il destinatario %s (%s)</li></ul></div>" \
                    % (action_class, vals.get("name"), vals.get("pec_mail"))

            post_vars = {'subject': "Aggiunta destinatario PEC",
                         'body': body,
                         'model': "protocollo.protocollo",
                         'res_id': sender_receiver_obj.protocollo_id.id,
                        }

            thread_pool = self.pool.get('protocollo.protocollo')
            thread_pool.message_post(cr, uid, sender_receiver_obj.protocollo_id.id, type="notification", context=context, **post_vars)

        return sender_receiver

    def write(self, cr, uid, ids, vals, context=None):
        self.check_field_in_write(cr, uid, ids, vals)
        return super(protocollo_sender_receiver, self).write(cr, uid, ids, vals, context=context)

    def aggiungi_destinatario_pec_action(self, cr, uid, ids, context=None):
        return True


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
                'mimetype': ct
            }
        return {'value': values}

    def on_change_typology(self, cr, uid, ids, typology_id, context=None):
        values = {'pec': False}
        if typology_id:
            typology_obj = self.pool.get('protocollo.typology')
            typology = typology_obj.browse(cr, uid, typology_id)
            if typology.pec:
                values = {
                    'pec': True
                }
        return {'value': values}

    def on_change_reserved(self, cr, uid, ids, reserved, context=None):
        values = {}
        if reserved:
            values = {
                'assegnatari_competenza_uffici_ids': False,
                'assegnatari_conoscenza_uffici_ids': False,
                'assegnatari_conoscenza_dipendenti_ids': False,
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
                    sender_receiver_obj = self.pool.get('protocollo.sender_receiver').browse(cr, uid, sender_receiver_id, context=context)
                    # if sender_receiver_obj.pec_accettazione_status and sender_receiver_obj.pec_consegna_status:
                    #     check_notifications += 1
                if check_notifications == len(prot.sender_receivers.ids):
                    res[prot.id] = True
        return res

    # def _is_visible(self, cr, uid, ids, name, arg, context=None):
    #     return {}
    #
    # def _is_visible_search(self, cursor, user, obj, name, args, domain=None, context=None):
    #     office_ids = self.pool.get('res.users').get_user_offices(cursor, user, context)
    #     offices = ', '.join(map(str, office_ids)) or str(0)
    #     cursor.execute('''
    #         select p.id
    #         from protocollo_protocollo p join protocollo_offices_rel r on p.id = r.protocollo_id
    #         where p.state in ('notified', 'sent', 'waiting', 'error') and r.office_id in (%s)
    #     ''' % offices)
    #     office_protocol_ids = [ids[0] for ids in cursor.fetchall()]
    #     cursor.execute('''
    #         select p.id
    #         from protocollo_protocollo p join protocollo_user_rel pur on p.id = pur.protocollo_id
    #         where p.state in ('notified', 'sent', 'waiting', 'error') and pur.user_id = %s
    #     ''' % user)
    #     assignee_protocol_ids = [ids[0] for ids in cursor.fetchall()]
    #     if assignee_protocol_ids:
    #         office_protocol_ids.extend(assignee_protocol_ids)
    #     protocol_ids = list(set(office_protocol_ids))
    #     return [('id', 'in', protocol_ids)]

    def _get_assegnatari_competenza(self, cr, uid, protocollo):
        employees = []
        for assegnatari_competenza_ufficio in protocollo.assegnatari_competenza_uffici_ids:
            for assegnatari_dipendente in assegnatari_competenza_ufficio.assegnatari_dipendenti_ids:
                dipendente = assegnatari_dipendente.dipendente_id
                if dipendente and dipendente.user_id:
                    employees.append(dipendente)
        for assegnatari_competenza_dipendente in protocollo.assegnatari_competenza_dipendenti_ids:
            dipendente = assegnatari_competenza_dipendente.dipendente_id
            if dipendente and dipendente.user_id:
                employees.append(dipendente)
        employees = list(set(employees))
        return employees

    def _get_assegnatari_conoscenza(self, cr, uid, protocollo):
        employees = []
        for assegnatari_conoscenza_ufficio in protocollo.assegnatari_conoscenza_uffici_ids:
            for assegnatari_dipendente in assegnatari_conoscenza_ufficio.assegnatari_dipendenti_ids:
                dipendente = assegnatari_dipendente.dipendente_id
                if dipendente:
                    employees.append(dipendente)
        for assegnatari_conoscenza_dipendente in protocollo.assegnatari_conoscenza_dipendenti_ids:
            dipendente = assegnatari_conoscenza_dipendente.dipendente_id
            if dipendente:
                employees.append(dipendente)
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
        'user_id': fields.many2one('res.users',
                                   'Protocollatore', readonly=True),
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
            'protocollo.typology', 'Mezzo Trasmissione', readonly=True, required=True,
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
        'body': fields.html('Corpo della mail', readonly=True),
        'mail_pec_ref': fields.many2one('mail.message',
                                        'Riferimento PEC',
                                        readonly=True),
        'mail_out_ref': fields.many2one('mail.mail',
                                        'Riferimento mail PEC in uscita',
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
                                          required=True,
                                          readonly=True,
                                          states={
                                              'draft': [('readonly', False)]
                                          }),
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
        'mimetype': fields.char('Mime Type', size=64),
        'doc_id': fields.many2one(
            'ir.attachment', 'Documento Principale', readonly=True,
            domain="[('res_model', '=', 'protocollo.protocollo')]"),
        'doc_content': fields.related('doc_id', 'datas', type='binary', string='Documento principale', readonly=True),
        'doc_fname': fields.related('doc_id', 'datas_fname', type="char", readonly=True),
        'fingerprint': fields.char('Impronta Documento', size=256),
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
        'sender_registration_date': fields.char('Data Registrazione Mittente',
                                       size=64,
                                       required=False,
                                       readonly=True),
        'sender_receivers': fields.one2many('protocollo.sender_receiver', 'protocollo_id', 'Mittenti/Destinatari'),
        'senders': fields.one2many('protocollo.sender_receiver', 'protocollo_id', 'Mittenti', domain=[('source', '=', 'sender')]),
        'receivers': fields.one2many('protocollo.sender_receiver', 'protocollo_id', 'Destinatari', domain=[('source', '=', 'receiver')]),

        'sender_receivers_summary': fields.function(
            _get_sender_receivers_summary,
            type="char",
            string="Mittenti/Destinatari",
            store=False),
        # 'assigne': fields.many2many('hr.department',
        #                            'protocollo_offices_rel',
        #                            'protocollo_id', 'office_id',
        #                            'Uffici di Competenza'),
        # 'assigne_users': fields.many2many('res.users', 'protocollo_user_rel', 'protocollo_id', 'user_id', 'Utenti Assegnatari'),
        'assigne_emails': fields.function(_get_assigne_emails, type='char', string='Email Destinatari'),
        'assigne_cc': fields.boolean('Inserisci gli Assegnatari in CC'),
        'dossier_ids': fields.many2many('protocollo.dossier', 'dossier_protocollo_rel', 'protocollo_id', 'dossier_id',
                                        'Fascicoli'),

        'assegnatari_competenza_uffici_ids': fields.one2many('protocollo.assegnatario.ufficio', 'protocollo_id',
                                                             'Uffici Assegnatari per Competenza',
                                                             domain=[('tipo', '=', 'competenza')]),
        'assegnatari_competenza_dipendenti_ids': fields.one2many('protocollo.assegnatario.dipendente', 'protocollo_id',
                                                                 'Dipendenti Assegnatari per Competenza',
                                                                 domain=[('tipo', '=', 'competenza')]),
        'assegnatari_conoscenza_uffici_ids': fields.one2many('protocollo.assegnatario.ufficio', 'protocollo_id',
                                                             'Uffici Assegnatari per Conoscenza',
                                                             domain=[('tipo', '=', 'conoscenza')]),
        'assegnatari_conoscenza_dipendenti_ids': fields.one2many('protocollo.assegnatario.dipendente', 'protocollo_id',
                                                                 'Dipendenti Assegnatari per Conoscenza',
                                                                 domain=[('tipo', '=', 'conoscenza')]),

        'notes': fields.text('Note'),
        # 'is_visible': fields.function(_is_visible, fnct_search=_is_visible_search, type='boolean', string='Visibile'),
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
    }

    _sql_constraints = [
        ('protocol_number_unique', 'unique(name,year,aoo_id)',
         'Elemento già presente nel DB!'),
        ('protocol_mail_pec_ref_unique', 'unique(mail_pec_ref)',
         'Meggaggio PEC protocollato in precedenza!')
    ]

    def _get_next_number_normal(self, cr, uid, prot):
        sequence_obj = self.pool.get('ir.sequence')
        last_id = self.search(cr, uid,
                              [('state', 'in', ('registered', 'notified', 'sent', 'waiting', 'error', 'canceled'))],
                              limit=1, order='registration_date desc')
        if last_id:
            now = datetime.datetime.now()
            last = self.browse(cr, uid, last_id[0])
            if last.registration_date[0:4] < str(now.year):
                seq_id = sequence_obj.search(cr, uid, [('code', '=', prot.registry.sequence.code)])
                sequence_obj.write(cr, SUPERUSER_ID, seq_id, {'number_next': 1})
        next_num = sequence_obj.get(cr, uid, prot.registry.sequence.code) or None
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

        prot_def = "%s %s - %s - %s - %s - %s" % (
            prot.registry.company_id.ammi_code,
            prot.aoo_id.ident_code,
            prot.registry.code,
            prot_dir,
            prot_date.strftime(DSDT),
            prot_number
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
        #if prot.reserved:
        #    parent_id, ruid = self._create_protocol_security_folder(cr, SUPERUSER_ID, prot, prot_number)
        attachment_obj = self.pool.get('ir.attachment')
        old_attachment_id = prot.doc_id.id
        attachment = attachment_obj.browse(cr, uid, old_attachment_id)
        prot_date = datetime.datetime.strptime(prot_date.split(' ')[0], DSDT)
        gext = '.' + attachment.datas_fname.split('.')[-1]
        ext = gext in mimetypes.types_map and gext or ''
        attach_vals = {
            'name': 'Protocollo_' + prot_number + '_' + str(prot.year) + ext,
            'datas': attachment.datas,
            'datas_fname': 'Protocollo_' + prot_number + '_' + str(prot.year) + ext,
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
        location = self.pool.get('ir.config_parameter').get_param(cr, uid, 'ir_attachment.location') + '/protocollazioni'
        new_attachment = attachment_obj.browse(cr, user_id, attachment_id)
        file_path = self._full_path(
            cr, uid, location, new_attachment.store_fname)
        return sha1OfFile(file_path)

    def _create_protocol_security_folder(self, cr, uid, prot, prot_number):
        group_reserved_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'seedoo_protocollo', 'group_protocollazione_riservata')[1]
        directory_obj = self.pool.get('document.directory')
        directory_root_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'seedoo_protocollo', 'dir_protocol')[1]
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
                    #if send_rec.partner_id:
                    #    raise orm.except_orm('Attenzione!', 'Si sta tentando di salvare un\' anagrafica già presente nel sistema')
                    partner_obj = self.pool.get('res.partner')
                    values = self.get_partner_values(cr, uid, send_rec)
                    partner_id = partner_obj.create(cr, uid, values)
                    send_rec_obj.write(cr, uid, [send_rec.id], {'partner_id': partner_id})
        return True

    def action_register(self, cr, uid, ids, context=None, *args):
        configurazione_ids = self.pool.get('protocollo.configurazione').search(cr, uid, [])
        configurazione = self.pool.get('protocollo.configurazione').browse(cr, uid, configurazione_ids[0])

        for prot in self.browse(cr, uid, ids):

            self.pool.get('protocollo.configurazione').verifica_campi_obbligatori(cr, uid, prot)

            try:
                vals = {}
                prot_number = self._get_next_number(cr, uid, prot)
                prot_date = fields.datetime.now()
                vals['name'] = prot_number
                vals['registration_date'] = prot_date
                prot_complete_name = self.calculate_complete_name(prot_date, prot_number)

                if prot.doc_id:
                    if prot.mimetype == 'application/pdf':
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

                now = datetime.datetime.now()
                vals['year'] = now.year

                if context == None:
                    new_context = {}
                else:
                    new_context = dict(context).copy()

                # if prot.typology.name == 'PEC':
                new_context.update({'pec_messages': True})

            except Exception as e:
                _logger.error(e)
                raise openerp.exceptions.Warning(_('Errore nella registrazione del protocollo'))
                continue

            segnatura_xml = SegnaturaXML(prot, prot_number, prot_date, cr, uid)
            xml = segnatura_xml.generate_segnatura_root()
            etree_tostring = etree.tostring(xml, pretty_print=True)
            vals['xml_signature'] = etree_tostring

            self.write(cr, uid, [prot.id], vals)

            if prot.type == 'in' and prot.pec and configurazione.conferma_xml_invia:
                self.action_send_receipt(cr, uid, ids, 'conferma', context=context)

            action_class = "history_icon registration"
            post_vars = {'subject': "Registrazione protocollo",
                         'body': "<div class='%s'><ul><li>Creato protocollo %s</li></ul></div>" % (
                         action_class, prot_complete_name),
                         'model': "protocollo.protocollo",
                         'res_id': prot.id,
                         }

            thread_pool = self.pool.get('protocollo.protocollo')
            thread_pool.message_post(cr, uid, prot.id, type="notification", context=new_context, **post_vars)

        return True

    def action_notify(self, cr, uid, ids, *args):
        email_template_obj = self.pool.get('email.template')
        for prot in self.browse(cr, uid, ids):
            if prot.type == 'in' and (
                        not prot.assegnatari_competenza_uffici_ids and not prot.assegnatari_competenza_dipendenti_ids):
                raise openerp.exceptions.Warning(_('Errore nella notifica del protocollo, mancano gli assegnatari'))
            if prot.reserved:
                template_reserved_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'seedoo_protocollo',
                                                                                           'notify_reserved_protocol')[1]
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
        for prot in self.browse(cr, uid, ids):
            receipt_xml = None
            messaggio_pec_obj = self.pool.get('protocollo.messaggio.pec')
            if receipt_type == 'conferma':
                receipt_xml = ConfermaXML(prot, cr, uid)
            if receipt_type == 'annullamento':
                receipt_xml = AnnullamentoXML(cr, uid, prot, context['receipt_cancel_reason'], context['receipt_cancel_author'],context['receipt_cancel_date'])

            xml = receipt_xml.generate_receipt_root()
            etree_tostring = etree.tostring(xml, pretty_print=True)

            if etree_tostring:
                mail_mail = self.pool.get('mail.mail')
                mail_server = self.get_pec_mail_server(cr, uid, context)

                sender_receivers_pec_mails = []
                sender_receivers_pec_ids = []

                if prot.sender_receivers:
                    for sender_receiver_id in prot.sender_receivers.ids:
                        sender_receiver_obj = self.pool.get('protocollo.sender_receiver').browse(cr, uid, sender_receiver_id, context=context)
                        if not sender_receiver_obj.pec_invio_status:
                            sender_receivers_pec_mails.append(sender_receiver_obj.pec_mail)
                            sender_receivers_pec_ids.append(sender_receiver_obj.id)

                if receipt_type == 'conferma':
                    attachment = self.pool.get('ir.attachment').create(cr, uid, {'name': 'conferma.xml',
                                                                             'datas_fname': 'conferma.xml',
                                                                             'datas': etree_tostring.encode('base64')})
                elif receipt_type == 'annullamento':
                    attachment = self.pool.get('ir.attachment').create(cr, uid, {'name': 'annullamento.xml',
                                                                             'datas_fname': 'annullamento.xml',
                                                                             'datas': etree_tostring.encode('base64')})

                # vals = {'pec_conferma_ref': mail.mail_message_id.id}
                # self.write(cr, uid, [prot.id], vals)
                new_context = dict(context).copy()
                new_context.update({'receipt_email_from': mail_server.smtp_user})
                new_context.update({'receipt_email_to': ','.join([sr for sr in sender_receivers_pec_mails])})
                new_context.update({'pec_messages': True})

                email_template_obj = self.pool.get('email.template')

                if receipt_type == 'conferma':
                    template_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'seedoo_protocollo', 'confirm_protocol')[1]
                if receipt_type == 'annullamento':
                    template_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'seedoo_protocollo', 'cancel_protocol')[1]

                template = email_template_obj.browse(cr, uid, template_id, new_context)
                template.attachment_ids = [(6, 0, [attachment])]
                template.write({
                    'mail_server_id': mail_server.id
                })
                mail_receipt_id = template.send_mail(prot.id, force_send=True)

                for sender_receiver_id in sender_receivers_pec_ids:
                    vals = {}
                    sender_receiver_obj = self.pool.get('protocollo.sender_receiver').browse(cr, uid, sender_receiver_id, context=context)
                    message_obj = self.pool.get('mail.message')
                    mail_receipt = self.pool.get('mail.mail').browse(cr, uid, mail_receipt_id[0], context=context)
                    message_receipt = mail_mail.browse(cr, uid, mail_receipt.mail_message_id.id, context=context)
                    valsreceipt={}
                    valsreceipt['pec_protocol_ref'] = prot.id
                    valsreceipt['pec_state'] = 'protocol'
                    valsreceipt['pec_type'] = 'posta-certificata'
                    message_obj.write(cr, uid, mail_receipt.mail_message_id.id, valsreceipt)
                    messaggio_pec_id = messaggio_pec_obj.create(cr, uid, {'type': receipt_type, 'messaggio_ref': message_receipt.id})
                    vals['pec_messaggio_ids'] = [(4, [messaggio_pec_id])]
                    sender_receiver_obj.write(vals)

                # action_class = "history_icon mail"
                # post_vars = {'subject': "Invio PEC",
                #              'body': "<div class='%s'><ul><li>PEC protocollo inviato a: %s</li></ul></div>" % (
                #              action_class, values['email_to']),
                #              'model': "protocollo.protocollo",
                #              'res_id': prot.id,
                #              }
                #
                # thread_pool = self.pool.get('protocollo.protocollo')
                # thread_pool.message_post(cr, uid, prot.id, type="notification", context=context, **post_vars)

                # for sender_receiver_id in sender_receivers_pec_ids:
                #     sender_receiver_obj = self.pool.get('protocollo.sender_receiver').browse(cr, uid, sender_receiver_id, context=context)
                #     sender_receiver_obj.write({'pec_ref': mail.mail_message_id.id})
        return True

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
            mail_mail = self.pool.get('mail.mail')
            ir_attachment = self.pool.get('ir.attachment')
            messaggio_pec_obj = self.pool.get('protocollo.messaggio.pec')
            sender_receivers_pec_mails = []
            sender_receivers_pec_ids = []
            mail_server = self.get_pec_mail_server(cr, uid, context)

            self.allega_segnatura_xml(cr, uid, prot.id, prot.xml_signature)

            if prot.sender_receivers:
                for sender_receiver_id in prot.sender_receivers.ids:
                    sender_receiver_obj = self.pool.get('protocollo.sender_receiver').browse(cr, uid, sender_receiver_id, context=context)
                    if not sender_receiver_obj.pec_invio_status:
                        sender_receivers_pec_mails.append(sender_receiver_obj.pec_mail)
                        sender_receivers_pec_ids.append(sender_receiver_obj.id)

            values = {}
            values['subject'] = prot.subject
            values['body_html'] = prot.body
            values['body'] = prot.body
            values['email_from'] = mail_server.smtp_user
            values['reply_to'] = mail_server.in_server_id.user
            values['mail_server_id'] = mail_server.id
            values['email_to'] = ','.join([sr for sr in
                                           sender_receivers_pec_mails]
                                          )
            values['pec_protocol_ref'] = prot.id
            values['pec_state'] = 'protocol'
            values['pec_type'] = 'posta-certificata'
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
                         'body': "<div class='%s'><ul><li>PEC protocollo inviato a: %s</li></ul></div>" % (action_class, values['email_to']),
                         'model': "protocollo.protocollo",
                         'res_id': prot_id,
                         }

            thread_pool = self.pool.get('protocollo.protocollo')
            thread_pool.message_post(cr, uid, prot_id, type="notification", context=context, **post_vars)

            if res[0]['state'] != 'sent':
                raise openerp.exceptions.Warning(_('Errore nella \
                    notifica del protocollo, mail pec non spedita'))
            else:
                for sender_receiver_id in sender_receivers_pec_ids:
                    msgvals = {}
                    sender_receiver_obj = self.pool.get('protocollo.sender_receiver').browse(cr, uid, sender_receiver_id, context=context)
                    messaggio_pec_id = messaggio_pec_obj.create(cr, uid, {'type': 'messaggio', 'messaggio_ref': mail.mail_message_id.id})
                    msgvals['pec_messaggio_ids'] = [(4, [messaggio_pec_id])]
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

    def get_pec_mail_server(self, cr, uid, context=None):
        mail_server_obj = self.pool.get('ir.mail_server')
        fetch_server_obj = self.pool.get('fetchmail.server')
        fetch_server_ids = fetch_server_obj.get_fetch_server_pec(cr, uid, context)
        if not fetch_server_ids:
            raise openerp.exceptions.Warning(_('Errore nella \
                notifica del protocollo, nessun server pec associato all\'utente'))
        mail_server_ids = mail_server_obj.get_mail_server_pec(cr, uid, fetch_server_ids[0], context)
        if not mail_server_ids:
            raise openerp.exceptions.Warning(_('Errore nella \
                notifica del protocollo, manca il server pec in uscita'))
        mail_server = mail_server_obj.browse(cr, uid, mail_server_ids[0])
        return mail_server

    def action_pec_send(self, cr, uid, ids, *args):
        context = {'pec_messages': True}
        for prot_id in ids:
            self._create_outgoing_pec(cr, uid, prot_id, context=context)
        return True

    def action_resend(self, cr, uid, ids, context=None):
        protocollo_obj = self.pool.get('protocollo.protocollo')
        protocollo_obj._process_new_pec(cr, uid, ids, protocollo_obj, context)

    def mail_message_id_pec_get(self, cr, uid, ids, *args):
        res = {}
        if not ids:
            return []
        protocol_obj = self.pool.get('protocollo.protocollo')
        for prot in protocol_obj.browse(cr, uid, ids):
            res[prot.id] = [prot.mail_pec_ref.id]
        _logger.info('mail_message_id_pec_get')
        return res[ids[0]]

    def test_mail_message(self, cr, uid, ids, *args):
        _logger.info('test_mail_message')
        res = self.mail_message_id_pec_get(cr, SUPERUSER_ID, ids)
        if not res:
            return False
        mail_message_obj = self.pool.get('mail.message')
        mail_message = mail_message_obj.browse(cr, SUPERUSER_ID, res[0])
        ok = mail_message.message_ok and not \
            mail_message.error
        return ok

    def test_error_mail_message(self, cr, uid, ids, *args):
        _logger.info('test_error_mail_message')
        res = self.mail_message_id_pec_get(cr, SUPERUSER_ID, ids)
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

    def has_offices(self, cr, uid, ids, *args):
        for protocol in self.browse(cr, uid, ids):
            if (
                        protocol.assegnatari_competenza_uffici_ids or protocol.assegnatari_competenza_dipendenti_ids) and protocol.type == 'in':
                return True
        return False

    def prendi_in_carico(self, cr, uid, ids, context=None):
        self.pool.get('protocollo.stato.dipendente').modifica_stato_dipendente(cr, uid, ids, 'preso')
        rec = self.pool.get('res.users').browse(cr, uid, uid)

        action_class = "history_icon taken"
        post_vars = {'subject': "Presa in carico",
                     'body': "<div class='%s'><ul><li>Protocollo preso in carico da <span style='color:#009900;'>%s</span></li></ul></div>" % (
                     action_class, rec.login),
                     'model': "protocollo.protocollo",
                     'res_id': ids[0],
                     }

        thread_pool = self.pool.get('protocollo.protocollo')
        thread_pool.message_post(cr, uid, ids[0], type="notification", context=context, **post_vars)

        return True

    def rifiuta_presa_in_carico(self, cr, uid, ids, context=None):
        self.pool.get('protocollo.stato.dipendente').modifica_stato_dipendente(cr, uid, ids, 'rifiutato')
        rec = self.pool.get('res.users').browse(cr, uid, uid)

        action_class = "history_icon refused"
        post_vars = {'subject': "Rifiuto presa in carico",
                     'body': "<div class='%s'><ul><li>Presa in carico rifiutata da <span style='color:#009900;'>%s</span></li></ul></div>" % (
                     action_class, rec.login),
                     'model': "protocollo.protocollo",
                     'res_id': ids[0],
                     }

        thread_pool = self.pool.get('protocollo.protocollo')
        thread_pool.message_post(cr, uid, ids[0], type="notification", context=context, **post_vars)

        return True

    def _verifica_dati_assegnatari_uffici(self, cr, uid, assegnatari_ufficio_vals, tipo):
        assegnatario_obj = self.pool.get('protocollo.assegnatario.ufficio')
        uffici_ids = []

        for assegnatario in assegnatari_ufficio_vals:
            if assegnatario[0] == 4:
                assegnatario_ufficio = assegnatario_obj.browse(cr, uid, assegnatario[1])
                uffici_ids.append(assegnatario_ufficio.department_id.id)

        for assegnatario in assegnatari_ufficio_vals:
            if assegnatario[0] == 1:
                assegnatario_data = assegnatario[2]
                if assegnatario_data.has_key('department_id'):
                    if assegnatario_data['department_id'] in uffici_ids:
                        raise orm.except_orm(_('Attenzione!'),
                                             _('Ci sono uffici duplicati fra gli assegnatari per %s!' % tipo))
                    else:
                        uffici_ids.append(assegnatario_data['department_id'])

        for assegnatario in assegnatari_ufficio_vals:
            if assegnatario[0] == 0:
                assegnatario_data = assegnatario[2]
                if assegnatario_data['department_id'] in uffici_ids:
                    raise orm.except_orm(_('Attenzione!'),
                                         _('Ci sono uffici duplicati fra gli assegnatari per %s!' % tipo))
                else:
                    uffici_ids.append(assegnatario_data['department_id'])
                    assegnatario_data['tipo'] = tipo

        return assegnatari_ufficio_vals

    def _verifica_dati_assegnatari_dipendenti(self, cr, uid, assegnatari_dipendente_vals, tipo):
        assegnatario_obj = self.pool.get('protocollo.assegnatario.dipendente')
        dipendenti_ids = []

        for assegnatario in assegnatari_dipendente_vals:
            if assegnatario[0] == 4:
                assegnatario_dipendente = assegnatario_obj.browse(cr, uid, assegnatario[1])
                dipendenti_ids.append(assegnatario_dipendente.dipendente_id.id)

        for assegnatario in assegnatari_dipendente_vals:
            if assegnatario[0] == 1:
                assegnatario_data = assegnatario[2]
                if assegnatario_data.has_key('dipendente_id'):
                    if assegnatario_data['dipendente_id'] in dipendenti_ids:
                        raise orm.except_orm(_('Attenzione!'),
                                             _('Ci sono dipendenti duplicati fra gli assegnatari per %s!' % tipo))
                    else:
                        dipendenti_ids.append(assegnatario_data['dipendente_id'])

        for assegnatario in assegnatari_dipendente_vals:
            if assegnatario[0] == 0:
                assegnatario_data = assegnatario[2]
                if assegnatario_data['dipendente_id'] in dipendenti_ids:
                    raise orm.except_orm(_('Attenzione!'),
                                         _('Ci sono dipendenti duplicati fra gli assegnatari per %s!' % tipo))
                else:
                    dipendenti_ids.append(assegnatario_data['dipendente_id'])
                    assegnatario_data['tipo'] = tipo

        return assegnatari_dipendente_vals

    def _verifica_dati_assegnatari(self, cr, uid, vals, context):
        if vals and vals.has_key('assegnatari_competenza_uffici_ids'):
            vals['assegnatari_competenza_uffici_ids'] = self._verifica_dati_assegnatari_uffici(cr, uid, vals[
                'assegnatari_competenza_uffici_ids'], 'competenza')
        if vals and vals.has_key('assegnatari_competenza_dipendenti_ids'):
            vals['assegnatari_competenza_dipendenti_ids'] = self._verifica_dati_assegnatari_dipendenti(cr, uid, vals[
                'assegnatari_competenza_dipendenti_ids'], 'competenza')
        if vals and vals.has_key('assegnatari_conoscenza_uffici_ids'):
            vals['assegnatari_conoscenza_uffici_ids'] = self._verifica_dati_assegnatari_uffici(cr, uid, vals[
                'assegnatari_conoscenza_uffici_ids'], 'conoscenza')
        if vals and vals.has_key('assegnatari_conoscenza_dipendenti_ids'):
            vals['assegnatari_competenza_conoscenza_ids'] = self._verifica_dati_assegnatari_dipendenti(cr, uid, vals[
                'assegnatari_conoscenza_dipendenti_ids'], 'conoscenza')
        return vals

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
        vals = self._verifica_dati_assegnatari(cr, uid, vals, context)
        vals = self._verifica_dati_sender_receiver(cr, uid, vals, context)
        protocollo_id = super(protocollo_protocollo, self).create(cr, uid, vals, context=context)
        return protocollo_id

    def write(self, cr, uid, ids, vals, context=None):
        vals = self._verifica_dati_assegnatari(cr, uid, vals, context)
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
                    prot_complete_name = prot.complete_name
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

                    if configurazione.genera_xml_segnatura:
                        segnatura_xml = SegnaturaXML(prot, prot_number, prot_date, cr, uid)
                        xml = segnatura_xml.generate_segnatura_root()
                        etree_tostring = etree.tostring(xml, pretty_print=True)
                        vals['xml_signature'] = etree_tostring

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
            thread_pool.message_post(cr, uid, protocollo_id, type="notification", context=context,
                                     **post_vars)

    # @api.cr_uid_ids_context
    # Gestione dello Storico attraverso Mail Thread
    def message_post(self, cr, uid, thread_id, body='', subject=None, type='notification',
                     subtype=None, parent_id=False, attachments=None, context=None,
                     content_subtype='html', **kwargs):
        if not context:
            context = {}
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, thread_id)
        if protocollo.state == 'draft' and str(subject).find('Registrazione') != 0 and context.has_key('is_pec_to_draft') == False :
            pass
        else:
            return super(protocollo_protocollo, self).message_post(
                cr, uid, thread_id, body=body,
                subject=subject, type=type,
                subtype=subtype, parent_id=parent_id,
                attachments=attachments, context=context,
                content_subtype=content_subtype, **kwargs)


    def aggiungi_destinatari_pec(self, cr, uid, ids, context=None):
        prot_id = ids[0]
        view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'seedoo_protocollo', 'protocollo_sender_receiver_form')
        view_id = view_ref[1] if view_ref else False
        context.update({
                'protocollo_id': prot_id,
        })

        if 'default_type' in context:
            del context['default_type']

        res = {
            'type': 'ir.actions.act_window',
            'name': _('Aggiungi Destinatario'),
            'res_model': 'protocollo.sender_receiver',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'new',
            'context': context
        }

        return res

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
        'aoo_id': fields.many2one('protocollo.aoo', 'AOO', required=True),
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


class protocollo_assegnatario_ufficio(orm.Model):
    _name = 'protocollo.assegnatario.ufficio'

    TIPO_SELECTION = [
        ('competenza', 'Per Competenza'),
        ('conoscenza', 'Per Conoscenza')
    ]

    def on_change_department_id(self, cr, uid, ids, department_id, context=None):
        dipendente_ids = []
        if department_id:
            department_obj = self.pool.get('hr.department')
            department = department_obj.browse(cr, uid, department_id)
            for dipendente_id in department.member_ids:
                dipendente_ids.append((0, 0, {'dipendente_id': dipendente_id}))
        return {'value': {'assegnatari_dipendenti_ids': dipendente_ids}}

    def _get_state(self, cr, uid, ids, prop, unknow_none, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]

        stato_dipendente_obj = self.pool.get('protocollo.stato.dipendente')
        reads = self.read(cr, uid, ids, ['id'], context=context)
        res = []

        for record in reads:
            preso_count = 0
            rifiutato_count = 0
            assegnato_count = 0
            assegnatario_ufficio = self.browse(cr, uid, record['id'])
            for assegnatario_dipendente in assegnatario_ufficio.assegnatari_dipendenti_ids:
                if assegnatario_dipendente.dipendente_id:
                    employee = assegnatario_dipendente.dipendente_id
                    stato_dipendente_ids = stato_dipendente_obj.search(cr, uid, [
                        ('dipendente_id', '=', employee.id),
                        ('protocollo_id', '=', assegnatario_ufficio.protocollo_id.id),
                    ])
                    if len(stato_dipendente_ids) > 0:
                        stato_dipendente = stato_dipendente_obj.browse(cr, uid, stato_dipendente_ids[0])
                        if stato_dipendente.state == 'rifiutato':
                            rifiutato_count = rifiutato_count + 1
                        elif stato_dipendente.state == 'preso':
                            preso_count = preso_count + 1
                        else:
                            assegnato_count = assegnato_count + 1

            if preso_count > 0:
                res.append((record['id'], 'preso'))
            elif rifiutato_count > 0 and rifiutato_count == len(assegnatario_ufficio.assegnatari_dipendenti_ids):
                res.append((record['id'], 'rifiutato'))
            else:
                res.append((record['id'], 'assegnato'))

        return dict(res)

    _columns = {
        'department_id': fields.many2one('hr.department', 'Ufficio', required=True),
        'protocollo_id': fields.many2one('protocollo.protocollo', 'Protocollo', required=True),
        'tipo': fields.selection(TIPO_SELECTION, 'Tipo', required=True, readonly=True),
        'assegnatari_dipendenti_ids': fields.one2many('protocollo.assegnatario.dipendente', 'ufficio_assegnatario_id',
                                                      'Dipendenti'),
        'state': fields.function(_get_state, type='selection', selection=STATE_ASSEGNATARIO_SELECTION, string='Stato',
                                 readonly=True),
    }

    def _verifica_dati_ufficio_assegnatari(self, cr, uid, vals, tipo, old_assegnatari_dipendenti):
        if vals and vals.has_key('department_id') and vals['department_id']:
            department_obj = self.pool.get('hr.department')
            department = department_obj.browse(cr, uid, vals['department_id'])
            old_dipendenti_ids = [old_assegnatario_dipendente.dipendente_id.id for old_assegnatario_dipendente in
                                  old_assegnatari_dipendenti]
            new_dipendenti_ids = department.member_ids.ids

            dipendente_ids = []
            for dipendente_id in new_dipendenti_ids:
                if dipendente_id not in old_dipendenti_ids:
                    dipendente_ids.append((0, 0, {
                        'dipendente_id': dipendente_id,
                        'tipo': tipo
                    }))

            for old_assegnatario_dipendente in old_assegnatari_dipendenti:
                if old_assegnatario_dipendente.dipendente_id.id not in new_dipendenti_ids:
                    dipendente_ids.append((2, old_assegnatario_dipendente.id, 0))

            vals['assegnatari_dipendenti_ids'] = dipendente_ids

        return vals

    def create(self, cr, uid, vals, context=None):
        vals = self._verifica_dati_ufficio_assegnatari(cr, uid, vals, vals['tipo'], [])
        assegnatario_ufficio_id = super(protocollo_assegnatario_ufficio, self).create(cr, uid, vals, context=context)
        return assegnatario_ufficio_id

    def write(self, cr, uid, ids, vals, context=None):
        assegnatari_uffici = self.browse(cr, uid, ids)
        if assegnatari_uffici and len(assegnatari_uffici) > 0:
            for assegnatario_ufficio in assegnatari_uffici:
                vals = self._verifica_dati_ufficio_assegnatari(cr, uid, vals, assegnatario_ufficio.tipo,
                                                               assegnatario_ufficio.assegnatari_dipendenti_ids)
                super(protocollo_assegnatario_ufficio, self).write(cr, uid, [assegnatario_ufficio.id], vals,
                                                                   context=context)
        else:
            return super(protocollo_assegnatario_ufficio, self).write(cr, uid, ids, vals, context=context)


class protocollo_assegnatario_dipendente(orm.Model):
    _name = 'protocollo.assegnatario.dipendente'

    _columns = {
        'dipendente_id': fields.many2one('hr.employee', 'Dipendente', required=True),
        'protocollo_id': fields.many2one('protocollo.protocollo', 'Protocollo', ondelete='cascade'),
        'ufficio_assegnatario_id': fields.many2one('protocollo.assegnatario.ufficio', 'Ufficio', ondelete='cascade'),
        'tipo': fields.selection(TIPO_ASSEGNAZIONE_SELECTION, 'Tipo', required=True, readonly=True),

        'stato_dipendente_id': fields.many2one('protocollo.stato.dipendente', 'Stato Dipendente', required=True,
                                               ondelete='cascade'),
        'state': fields.related('stato_dipendente_id', 'state', type='selection',
                                selection=STATE_ASSEGNATARIO_SELECTION, string='Stato', readonly=True),
    }

    def _verifica_stato_dipendente(self, cr, uid, vals):
        if vals and vals.has_key('dipendente_id') and vals['dipendente_id']:
            dipendente_id = vals['dipendente_id']
            protocollo_id = False
            if vals.has_key('protocollo_id') and vals['protocollo_id']:
                protocollo_id = vals['protocollo_id']
            if vals.has_key('ufficio_assegnatario_id') and vals['ufficio_assegnatario_id']:
                assegnatario_ufficio_obj = self.pool.get('protocollo.assegnatario.ufficio')
                assegnatario_ufficio = assegnatario_ufficio_obj.browse(cr, uid, vals['ufficio_assegnatario_id'])
                protocollo_id = assegnatario_ufficio.protocollo_id.id
            if protocollo_id:
                stato_dipendente_obj = self.pool.get('protocollo.stato.dipendente')
                stato_dipendente_ids = stato_dipendente_obj.search(cr, uid, [
                    ('dipendente_id', '=', dipendente_id),
                    ('protocollo_id', '=', protocollo_id)
                ])
                if stato_dipendente_ids and len(stato_dipendente_ids) > 0:
                    vals['stato_dipendente_id'] = stato_dipendente_ids[0]
                else:
                    stato_dipendente_id = stato_dipendente_obj.create(cr, uid, {
                        'dipendente_id': dipendente_id,
                        'protocollo_id': protocollo_id
                    })
                    vals['stato_dipendente_id'] = stato_dipendente_id
        return vals

    def create(self, cr, uid, vals, context=None):
        vals = self._verifica_stato_dipendente(cr, uid, vals)
        assegnatario_dipendente_id = super(protocollo_assegnatario_dipendente, self).create(cr, uid, vals,
                                                                                            context=context)
        return assegnatario_dipendente_id

    def write(self, cr, uid, ids, vals, context=None):
        vals = self._verifica_stato_dipendente(cr, uid, vals)
        return super(protocollo_assegnatario_dipendente, self).write(cr, uid, ids, vals, context=context)


class protocollo_stato_dipendente(orm.Model):
    _name = 'protocollo.stato.dipendente'

    _columns = {
        'dipendente_id': fields.many2one('hr.employee', 'Dipendente', required=True, ondelete='cascade'),
        'protocollo_id': fields.many2one('protocollo.protocollo', 'Protocollo', required=True, ondelete='cascade'),
        'state': fields.selection(STATE_ASSEGNATARIO_SELECTION, 'Stato', required=True),
    }

    _defaults = {
        'state': 'assegnato'
    }

    _sql_constraints = [
        ('protocol_state_unique', 'unique(dipendente_id,protocollo_id)',
         'Dipendente e Protocollo con già uno stato nel DB!'),
    ]

    def modifica_stato_dipendente(self, cr, uid, protocollo_ids, state):
        employee_obj = self.pool.get('hr.employee')
        employee_ids = employee_obj.search(cr, uid, [('user_id', '=', uid)])
        if len(employee_ids) == 0:
            raise orm.except_orm(_('Attenzione!'), _('Non è stato trovato l\'employee per la tua utenza!'))

        employee_id = employee_ids[0]
        stato_dipendente_obj = self.pool.get('protocollo.stato.dipendente')
        for protocollo_id in protocollo_ids:
            stato_dipendente_ids = stato_dipendente_obj.search(cr, uid, [
                ('dipendente_id', '=', employee_id),
                ('protocollo_id', '=', protocollo_id),
            ])

            if len(stato_dipendente_ids) == 0:
                raise orm.except_orm(_('Attenzione!'), _('Non sei uno degli assegnatari del protocollo!'))

            stato_dipendente_obj.write(cr, uid, [stato_dipendente_ids[0]], {'state': state})
