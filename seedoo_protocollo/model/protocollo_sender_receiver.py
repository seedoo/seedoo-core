# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import orm, fields, osv
import mimetypes
import logging

_logger = logging.getLogger(__name__)
mimetypes.init()

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
        'protocol_type': fields.related('protocollo_id', 'type', type='char', string='Tipo Protocollo', readonly=True),
        'add_pec_receiver_visibility': fields.boolean('Button Visibility', readonly=True),
        # 'pec_ref': fields.many2one('protocollo.messaggio.pec', 'Messaggio PEC'),# campo pec_ref da eliminare
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
