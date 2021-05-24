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

    def on_change_type(self, cr, uid, ids, type, context=None):
        value = {'title': False}
        if 'is_type_selection' in context:
            value = {
                'title': False,
                'partner_id': False,
                'pa_type': False,
                'ident_code': False,
                'ammi_code': False
            }
        if type == 'legal' or type == 'government':
            value['title_domain'] = 'partner'
        else:
            value['title_domain'] = 'contact'
        return {'value': value}

    def on_change_pa_type(self, cr, uid, ids, pa_type, context=None):
        res = {'value': {}}

        if pa_type == 'aoo':
            res['value']['super_type'] = 'pa'
        elif pa_type == 'uo':
            res['value']['super_type'] = 'aoo'

        return res

    def on_change_partner(self, cr, uid, ids, partner_id, context=None):
        if partner_id:
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context)
            values = {
                # 'type': partner.is_company and 'individual' or 'legal',
                'type': partner.legal_type,
                'pa_type': partner.pa_type,
                'ident_code': partner.ident_code,
                'ammi_code': partner.ammi_code,
                'ipa_code': partner.ipa_code,
                'name': partner.display_name,
                'tax_code': partner.tax_code,
                'vat': partner.vat,
                'street': partner.street,
                'city': partner.city,
                'country_id': (partner.country_id and partner.country_id.id or False),
                'email': partner.email,
                'phone': partner.phone,
                'mobile': partner.mobile,
                'pec_mail': partner.pec_mail,
                'fax': partner.fax,
                'zip': partner.zip,
                'street2': partner.street2,
                'state_id': (partner.state_id and partner.state_id.id or False),
                'function': partner.function,
                'website': partner.website,
                'title': (partner.title and partner.title.id or False),
                'save_partner': False,
                'partner_id': partner.id
            }
        else:
            values = {
                'type': False,
                'pa_type': False,
                'ident_code': False,
                'ammi_code': False,
                'ipa_code': False,
                'name': False,
                'tax_code': False,
                'vat': False,
                'street': False,
                'city': False,
                'country_id': False,
                'email': False,
                'phone': False,
                'mobile': False,
                'pec_mail': False,
                'fax': False,
                'zip': False,
                'street2': False,
                'state_id': False,
                'function': False,
                'website': False,
                'title': False,
                'save_partner': False,
                'partner_id': False
            }
        return {'value': values}

    def on_change_pec_mail(self, cr, uid, ids, pec_mail, save_partner, context=None):
        res = {'value': {}}
        if pec_mail and save_partner:
            self.pool.get('res.partner').check_email_field(cr, uid, [('pec_mail', '=ilike', pec_mail)], 'Mail PEC', pec_mail)
        elif pec_mail:
            self.pool.get('res.partner').check_email_validity('Mail PEC', pec_mail)
        return res

    def on_change_email(self, cr, uid, ids, email, save_partner, context=None):
        res = {'value': {}}
        if email and save_partner:
            self.pool.get('res.partner').check_email_field(cr, uid, [('email', '=ilike', email)], 'Mail', email)
        elif email:
            self.pool.get('res.partner').check_email_validity('Mail', email)
        return res

    def on_change_save_partner(self, cr, uid, ids, pec_mail, email, save_partner, context=None):
        res = {'value': {}}
        errors = ''

        pec_mail_error = ''
        if pec_mail and save_partner:
            pec_mail_error = self.pool.get('res.partner').check_email_field(cr, uid, [('pec_mail', '=ilike', pec_mail)], 'Mail PEC', pec_mail, False)
        elif pec_mail:
            pec_mail_error = self.pool.get('res.partner').check_email_validity('Mail PEC', pec_mail, False)
        if pec_mail_error:
            errors = errors + '\n' + pec_mail_error

        email_error = ''
        if email and save_partner:
            email_error = self.pool.get('res.partner').check_email_field(cr, uid, [('email', '=ilike', email)], 'Mail', email, False)
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
        messaggio_pec_obj = self.pool.get('protocollo.messaggio.pec')
        for sr in self.browse(cr, uid, ids, context={'skip_check': True}):
            prot = sr.protocollo_id
            if prot:
                pec_messaggio_ids = messaggio_pec_obj.search(cr, uid, [
                    ('sender_receiver_ids', '=', sr.id),
                    ('type', '=', 'messaggio')
                ], order='id DESC', limit=1)
                if pec_messaggio_ids and prot.type == 'out' and prot.state in ('waiting', 'sent', 'error', 'notified', 'canceled'):
                    res[sr.id] = True
        return res

    def _get_accettazione_status(self, cr, uid, ids, field, arg, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        res = dict.fromkeys(ids, False)
        messaggio_pec_obj = self.pool.get('protocollo.messaggio.pec')
        for sr in self.browse(cr, uid, ids, context={'skip_check': True}):
            prot = sr.protocollo_id
            if prot:
                pec_messaggio_ids = messaggio_pec_obj.search(cr, uid, [
                    ('sender_receiver_ids', '=', sr.id),
                    ('type', '=', 'messaggio')
                ], order='id DESC', limit=1)
                if pec_messaggio_ids and prot.state in ('waiting', 'sent', 'error', 'notified', 'canceled'):
                    pec_messaggio = messaggio_pec_obj.browse(cr, uid, pec_messaggio_ids[0])
                    res[sr.id] = True if pec_messaggio.accettazione_ref else False
        return res

    def _get_consegna_status(self, cr, uid, ids, field, arg, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        res = dict.fromkeys(ids, False)
        messaggio_pec_obj = self.pool.get('protocollo.messaggio.pec')
        for sr in self.browse(cr, uid, ids, context={'skip_check': True}):
            prot = sr.protocollo_id
            if prot:
                pec_messaggio_ids = messaggio_pec_obj.search(cr, uid, [
                    ('sender_receiver_ids', '=', sr.id),
                    ('type', '=', 'messaggio')
                ], order='id DESC', limit=1)
                if pec_messaggio_ids and prot.state in ('waiting', 'sent', 'error', 'notified', 'canceled'):
                    pec_messaggio = messaggio_pec_obj.browse(cr, uid, pec_messaggio_ids[0])
                    res[sr.id] = True if pec_messaggio.consegna_ref else False
        return res

    def _get_non_accettazione_status(self, cr, uid, ids, field, arg, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        res = dict.fromkeys(ids, False)
        messaggio_pec_obj = self.pool.get('protocollo.messaggio.pec')
        for sr in self.browse(cr, uid, ids, context={'skip_check': True}):
            prot = sr.protocollo_id
            if prot:
                pec_messaggio_ids = messaggio_pec_obj.search(cr, uid, [
                    ('sender_receiver_ids', '=', sr.id),
                    ('type', '=', 'messaggio')
                ], order='id DESC', limit=1)
                if pec_messaggio_ids and prot.state in ('waiting', 'sent', 'error', 'notified', 'canceled'):
                    pec_messaggio = messaggio_pec_obj.browse(cr, uid, pec_messaggio_ids[0])
                    res[sr.id] = True if pec_messaggio.non_accettazione_ref else False
        return res

    def _get_errore_consegna_status(self, cr, uid, ids, field, arg, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        res = dict.fromkeys(ids, False)
        messaggio_pec_obj = self.pool.get('protocollo.messaggio.pec')
        for sr in self.browse(cr, uid, ids, context={'skip_check': True}):
            prot = sr.protocollo_id
            if prot:
                pec_messaggio_ids = messaggio_pec_obj.search(cr, uid, [
                    ('sender_receiver_ids', '=', sr.id),
                    ('type', '=', 'messaggio')
                ], order='id DESC', limit=1)
                if pec_messaggio_ids and prot.state in ('waiting', 'sent', 'error', 'notified', 'canceled'):
                    pec_messaggio = messaggio_pec_obj.browse(cr, uid, pec_messaggio_ids[0])
                    res[sr.id] = True if pec_messaggio.errore_consegna_ref else False
        return res

    def _get_conferma_status(self, cr, uid, ids, field, arg, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        res = dict.fromkeys(ids, False)
        messaggio_pec_obj = self.pool.get('protocollo.messaggio.pec')
        for sr in self.browse(cr, uid, ids, context={'skip_check': True}):
            prot = sr.protocollo_id
            if prot:
                pec_messaggio_ids = messaggio_pec_obj.search(cr, uid, [
                    ('sender_receiver_ids', '=', sr.id),
                    ('type', '=', 'conferma')
                ], order='id DESC')
                if pec_messaggio_ids and prot.state in ('registered', 'waiting', 'sent', 'error', 'notified', 'canceled'):
                    res[sr.id] = True
        return res

    def _get_pec_numero_invii(self, cr, uid, ids, field, arg, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        res = dict.fromkeys(ids, False)
        for sr in self.browse(cr, uid, ids, {'skip_check': True}):
            res[sr.id] = self.pool.get('protocollo.messaggio.pec').search(cr, uid, [('id', 'in', sr.pec_messaggio_ids.ids),('type', '=', 'messaggio')], count=1)
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

    def _get_title_domain(self, cr, uid, ids, field, arg, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        res = dict.fromkeys(ids, False)
        for sender_receiver in self.browse(cr, uid, ids, context):
            if sender_receiver.type=='legal' or sender_receiver.type=='government':
                res[sender_receiver.id] = 'partner'
            else:
                res[sender_receiver.id] = 'contact'
        return res

    _columns = {
        'protocollo_id': fields.many2one('protocollo.protocollo', 'Protocollo'),
        'source': fields.selection([
                ('sender', 'Mittente'),
                ('receiver', 'Destinatario'),
        ], 'Mittente/Destinatario', size=32, required=True, readonly=True),

        'type': fields.selection(
            [
                ('individual', 'Persona'),
                ('legal', 'Azienda'),
                ('government', 'PA')
            ], 'Tipologia', size=32, required=True),

        'pa_type': fields.selection(
            [
                ('pa', 'Ente'),
                ('aoo', 'AOO'),
                ('uo', 'UO')],
            'Tipo PA', size=5, required=False),

        'ident_code': fields.char('Codice AOO', size=256, required=False),
        'ammi_code': fields.char('Codice iPA', size=256, required=False),
        'ipa_code': fields.char('Codice Unità Organizzativa', size=256, required=False),
        'save_partner': fields.boolean('Salva contatto nella rubrica', help='Se spuntato salva i dati in anagrafica.'),
        'partner_id': fields.many2one('res.partner', 'Cerca in Contatti'),
        'name': fields.char('Nome Cognome / Ragione Sociale', size=512, required=True),
        'tax_code': fields.char('Codice Fiscale'),
        'vat': fields.char('Partita IVA'),
        'street': fields.char('Via/Piazza num civico', size=128),
        'street2': fields.char('Street2'),
        'zip': fields.char('Cap', change_default=True, size=24),
        'city': fields.char('Citta\'', size=128),
        'state_id': fields.many2one("res.country.state", 'Provincia', ondelete='restrict'),
        'country_id': fields.many2one('res.country', 'Paese'),
        'function': fields.char('Posizione lavorativa'),
        'email': fields.char('Email', size=240),
        'pec_mail': fields.char('Email PEC', size=240),
        'phone': fields.char('Telefono', size=64),
        'fax': fields.char('Fax', size=64),
        'mobile': fields.char('Cellulare', size=64),
        'website': fields.char('Website'),
        'title': fields.many2one('res.partner.title', 'Qualifica'),
        'notes': fields.text('Note'),
        'send_type': fields.many2one('protocollo.typology', 'Canale di Spedizione'),
        'send_date': fields.date('Data Spedizione'),
        'protocol_state': fields.related('protocollo_id', 'state', type='char', string='State', readonly=True),
        'protocol_sharedmail': fields.related('protocollo_id', 'sharedmail', type='boolean', string='Tipo Sharedmail', readonly=True),
        'protocol_pec': fields.related('protocollo_id', 'pec', type='boolean', string='Tipo PEC', readonly=True),
        'protocol_type': fields.related('protocollo_id', 'type', type='char', string='Tipo Protocollo', readonly=True),
        'add_pec_receiver_visibility': fields.boolean('Button Visibility', readonly=True),
        # 'pec_ref': fields.many2one('protocollo.messaggio.pec', 'Messaggio PEC'),# campo pec_ref da eliminare
        'pec_messaggio_ids': fields.many2many('protocollo.messaggio.pec', 'protocollo_sender_receiver_messaggio_pec_rel', 'sender_receiver_id', 'messaggio_pec_id', 'Messaggi PEC'),
        'pec_invio_status': fields.function(_get_invio_status, type='boolean', string='Inviata'),
        'pec_accettazione_status': fields.function(_get_accettazione_status, type='boolean', string='Accettata'),
        'pec_consegna_status': fields.function(_get_consegna_status, type='boolean', string='Consegnata'),
        #TODO: aggiungere un campo function booleano email_consegna_status che parsa il contenuto dell'email di
        # accettazione per individuare se la PEC è stata mandanda ad un indirizzo di posta ordinaria. Si dovrà
        # utilizzare questo campo per far avanzare lo stato del protocollo in "Inviato" pur non avendo il messaggio di
        # avvenuta consegna per il destinatario con email.
        'pec_non_accettazione_status': fields.function(_get_non_accettazione_status, type='boolean', string='Non Accettazione'),
        'pec_errore_consegna_status': fields.function(_get_errore_consegna_status, type='boolean', string='Errore Consegna'),
        'pec_conferma_status': fields.function(_get_conferma_status, type='boolean', string='Conferma Protocollazione'),
        'pec_numero_invii': fields.function(_get_pec_numero_invii, type='integer', string='PEC - Numero invii'),
        'sharedmail_messaggio_ids': fields.many2many('mail.message', 'protocollo_sender_receiver_messaggio_sharedmail_rel', 'sender_receiver_id', 'mail_message_id', 'Messaggi Sharedmail'),
        'sharedmail_numero_invii': fields.integer('Sharedmail - Numero invii', readonly=True, required=False),
        'to_resend': fields.boolean("Da reinviare", help="Destinatario modificato, da reinviare"),
        'title_domain': fields.function(_get_title_domain, type='char', string='Title domain', store=False),
    }

    _defaults = {
        'protocollo_id':_get_default_protocollo_id,
        'source':_get_default_source,
        'add_pec_receiver_visibility': _get_add_pec_receiver_visibility,
        'to_resend': False,
        'sharedmail_numero_invii': 0,
    }

    def init(self, cr):
        cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = \'idx_protocollo_sender_receiver_protocollo_id\'')
        if not cr.fetchone():
            cr.execute("""
                CREATE INDEX idx_protocollo_sender_receiver_protocollo_id
                ON public.protocollo_sender_receiver
                USING btree
                (protocollo_id);
            """)

    def check_field_in_create(self, cr, uid, vals, context=None):
        partner_obj = self.pool.get('res.partner')
        errors = ''

        if vals.has_key('pec_mail') and vals['pec_mail']:
            pec_mail_error = ''
            if vals.has_key('save_partner') and vals['save_partner'] and (not context or not ('skip_check_email' in context)):
                pec_mail_error = partner_obj.check_email_field(cr, uid, [('pec_mail', '=ilike', vals['pec_mail'])], 'Mail PEC', vals['pec_mail'], False)
            else:
                pec_mail_error = partner_obj.check_email_validity('Mail PEC', vals['pec_mail'], False)
            if pec_mail_error:
                errors = errors + '\n' + pec_mail_error

        if vals.has_key('email') and vals['email']:
            email_error = ''
            if vals.has_key('save_partner') and vals['save_partner'] and (not context or not ('skip_check_email' in context)):
                email_error = partner_obj.check_email_field(cr, uid, [('email', '=ilike', vals['email'])], 'Mail', vals['email'], False)
            else:
                email_error = partner_obj.check_email_validity('Mail', vals['email'], False)
            if email_error:
                errors = errors + '\n' + email_error

        partner_obj.dispatch_email_error(errors)

    def check_field_in_write(self, cr, uid, ids, vals, context=None):
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
                if pec_mail and save_partner and (not context or not ('skip_check_email' in context)):
                    pec_mail_error = partner_obj.check_email_field(cr, uid, [('pec_mail', '=ilike', pec_mail)], 'Mail PEC', pec_mail, False)
                elif pec_mail:
                    pec_mail_error = partner_obj.check_email_validity('Mail PEC', pec_mail, False)
                if pec_mail_error:
                    errors = errors + '\n' + pec_mail_error

                email = sender_receiver_vals['email']
                if vals.has_key('email'):
                    email = vals['email']
                email_error = ''
                if email and save_partner and (not context or not ('skip_check_email' in context)):
                    email_error = partner_obj.check_email_field(cr, uid, [('email', '=ilike', email)], 'Mail', email, False)
                elif email:
                    email_error = partner_obj.check_email_validity('Mail', email, False)
                if email_error:
                    errors = errors + '\n' + email_error

                partner_obj.dispatch_email_error(errors)

    def create_partner_from_sender_receiver(self, cr, uid, sender_receiver_id):
        partner_obj = self.pool.get('res.partner')
        sender_receiver = self.browse(cr, uid, sender_receiver_id)

        values = self.get_partner_values(cr, uid, sender_receiver)
        partner_id = partner_obj.create(cr, uid, values)
        return partner_id


    def get_partner_values(self, cr, uid, send_rec):
        values = {
            'name': send_rec.name,
            'is_company': True if (send_rec.type=='legal' or send_rec.type=='government') else False,
            'tax_code': send_rec.tax_code,
            'vat': send_rec.vat,
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
            'ipa_code': send_rec.ipa_code,
            'street2': send_rec.street2,
            'state_id': (send_rec.state_id and send_rec.state_id.id or False),
            'function': send_rec.function,
            'website': send_rec.website,
            'title': (send_rec.title and send_rec.title.id or False),
        }
        return values

    def create(self, cr, uid, vals, context=None):
        if 'partner_id' in vals and vals['partner_id']:
            copy_vals = self.on_change_partner(cr, uid, [], vals['partner_id'])
            vals.update(copy_vals['value'])
        self.check_field_in_create(cr, uid, vals)
        sender_receiver_id = super(protocollo_sender_receiver, self).create(cr, uid, vals, context=context)
        sender_receiver = self.browse(cr, uid, sender_receiver_id, {'skip_check': True})
        self.save_history(cr, uid, sender_receiver, 'create', context=context)
        return sender_receiver_id

    def write(self, cr, uid, ids, vals, context=None):
        self.check_field_in_write(cr, uid, ids, vals, context)
        if isinstance(ids, int):
            ids = [ids]
        for sender_receiver_id in ids:
            sender_receiver = self.browse(cr, uid, sender_receiver_id, {'skip_check': True})
            # creazione del partner se save_partner viene modificato dal form
            if 'partner_id' not in vals and vals.get("save_partner", False):
                vals.update({'partner_id': self.create_partner_from_sender_receiver(cr, uid, sender_receiver.id)})
            if 'partner_id' in vals and vals['partner_id'] and not vals.get("save_partner", False):
                copy_vals = self.on_change_partner(cr, uid, [], vals['partner_id'])
                vals.update(copy_vals['value'])
            if 'pec_messaggio_ids' not in vals and 'sharedmail_messaggio_ids' not in vals and \
                    ('to_resend' not in vals or not vals['to_resend']):
                self.save_history(cr, uid, sender_receiver, 'write', vals, context=context)
        return super(protocollo_sender_receiver, self).write(cr, uid, ids, vals, context=context)

    def elimina_mittente_destinatario(self, cr, uid, ids, context={}):
        mittente_destinatario = self.browse(cr, uid, ids[0])
        protocollo = mittente_destinatario.protocollo_id
        self.save_history(cr, uid, mittente_destinatario, 'unlink', context=context)
        self.unlink(cr, uid, ids, context)

        return {
            'name': 'Protocollo',
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'protocollo.protocollo',
            'res_id': protocollo.id,
            'context': context,
            'type': 'ir.actions.act_window',
            'flags': {'initial_mode': 'edit'}
        }

    def copy(self, cr, uid, id, default=None, context=None):
        sender_receiver_obj = self.pool.get('protocollo.sender_receiver')
        sender_receiver = sender_receiver_obj.browse(cr, uid, id)
        vals = {
            'ammi_code': sender_receiver.ammi_code,
            'ident_code': sender_receiver.ident_code,
            'ipa_code': sender_receiver.ipa_code,
            'name': sender_receiver.name,
            'display_name': sender_receiver.display_name,
            'tax_code': sender_receiver.tax_code,
            'vat': sender_receiver.vat,
            'street': sender_receiver.street,
            'city': sender_receiver.city,
            'country_id': sender_receiver.country_id.id,
            'email': sender_receiver.email,
            'phone': sender_receiver.phone,
            'mobile': sender_receiver.mobile,
            'pec_mail': sender_receiver.pec_mail,
            'fax': sender_receiver.fax,
            'zip': sender_receiver.zip,
            'notes': sender_receiver.notes,
            'pa_type': sender_receiver.pa_type,
            'partner_id': sender_receiver.partner_id.id,
            'send_type': sender_receiver.send_type,
            'source': sender_receiver.source,
            'type': sender_receiver.type,
            'street2': sender_receiver.street2,
            'state_id': sender_receiver.state_id.id,
            'function': sender_receiver.function,
            'website': sender_receiver.website,
            'title': sender_receiver.title.id,
        }

        return sender_receiver_obj.create(cr, uid, vals)


    def save_history(self, cr, uid, sender_receiver, operation, vals={}, context={}):
        protocollo_obj = self.pool.get('protocollo.protocollo')
        save_history = True if sender_receiver.protocollo_id.state in protocollo_obj.get_history_state_list(cr, uid) else False
        if save_history and str(self) == 'protocollo.sender_receiver':
            if operation == 'create':
                operation_label = 'Inserimento '
                template = "<li>%s: <span style='color:#007ea6'> %s </span></li>"
            elif operation == 'write':
                operation_label = 'Modifica '
                template = "<li>%s: <span style='color:#990000'> %s</span> -> <span style='color:#007ea6'> %s </span></li>"
            else:
                operation_label = 'Cancellazione '
                template = "<li>%s: <span style='color:#990000'> %s </span></li>"
            operation_label += 'mittente' if sender_receiver.source == 'sender' else 'destinatario'
            action_class = 'history_icon update'


            body = "<div class='%s'><ul>" % action_class
            if operation == 'write':
                if 'name' in vals:
                    if sender_receiver.name != vals['name']:
                        body += template % ('Nome Cognome/Ragione Sociale', sender_receiver.name, vals['name'])
                if 'email' in vals:
                    if sender_receiver.email != vals['email']:
                        body += template % ('Email', sender_receiver.email, vals['email'])
                if 'pec_mail' in vals:
                    if sender_receiver.pec_mail != vals['pec_mail']:
                        body += template % ('Email PEC', sender_receiver.pec_mail, vals['pec_mail'])
            else:
                template
                if sender_receiver.email:
                    body += template % ('Email', sender_receiver.email)
                if sender_receiver.pec_mail:
                    body += template % ('Email PEC', sender_receiver.pec_mail)
            body += "</ul></div>"

            post_vars = {
                'subject': "%s: %s" % (operation_label, sender_receiver.name),
                'body': body,
                'model': 'protocollo.protocollo',
                'res_id': sender_receiver.protocollo_id.id
            }
            protocollo_obj.message_post(cr, uid, sender_receiver.protocollo_id.id, type="notification", context=context, **post_vars)