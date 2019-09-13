# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Business Applications
#    Copyright (C) 2004-2012 OpenERP S.A. (<http://openerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import SUPERUSER_ID
from openerp.osv import fields, osv
from openerp.tools.safe_eval import safe_eval

class protocollo_config_settings(osv.osv_memory):
    _name = 'protocollo.config.settings'
    _inherit = 'res.config.settings'

    _columns = {
        'config_id': fields.many2one('protocollo.configurazione', string='Configurazione', required=True),
        'inserisci_testo_mailpec': fields.related('config_id', 'inserisci_testo_mailpec', type='boolean', string='Abilita testo e-mail/PEC protocollo'),
        'rinomina_documento_allegati': fields.related('config_id', 'rinomina_documento_allegati', type='boolean', string='Rinomina documento principale e allegati'),
        'rinomina_oggetto_mail_pec': fields.related('config_id', 'rinomina_oggetto_mail_pec', type='boolean', string='Rinomina oggetto e-mail/PEC'),
        'genera_segnatura': fields.related('config_id', 'genera_segnatura', type='boolean', string='Genera Segnatura in PDF Post-Registrazione'),
        'segnatura_xml_parse': fields.related('config_id', 'segnatura_xml_parse', type='boolean', string='Leggi "Segnatura.xml"'),
        'segnatura_xml_invia': fields.related('config_id', 'segnatura_xml_invia', type='boolean', string='Invia "Segnatura.xml"'),
        'conferma_xml_parse': fields.related('config_id', 'conferma_xml_parse', type='boolean', string='Leggi "Conferma.xml" in Protocollazione in uscita'),
        'conferma_xml_invia': fields.related('config_id', 'conferma_xml_invia', type='boolean', string='Invia "Conferma.xml" in Protocollazione in ingresso'),
        'sender_segnatura_xml_parse': fields.related('config_id', 'sender_segnatura_xml_parse', type='boolean', string='Ricava mittente da "Segnature.xml"'),
        'annullamento_xml_parse': fields.related('config_id', 'annullamento_xml_parse', type='boolean', string='Leggi "Annullamento.xml" in Protocollazione in uscita'),
        'annullamento_xml_invia': fields.related('config_id', 'annullamento_xml_invia', type='boolean', string='Invia "Annullamento.xml" in Protocollazione in ingresso'),
        'classificazione_required': fields.related('config_id', 'classificazione_required', type='boolean', string='Classificazione'),
        'fascicolazione_required': fields.related('config_id', 'fascicolazione_required', type='boolean', string='Fascicolazione'),

        'assegnatari_competenza_uffici_required': fields.related('config_id', 'assegnatari_competenza_uffici_required',
                 type='boolean', string='Uffici assegnatari per competenza'),
        'assegnatari_competenza_dipendenti_required': fields.related('config_id', 'assegnatari_competenza_dipendenti_required',
                 type='boolean', string='Dipendenti assegnatari per competenza'),
        'assegnatari_conoscenza_uffici_required': fields.related('config_id', 'assegnatari_conoscenza_uffici_required',
                 type='boolean', string='Uffici assegnatari per conoscenza'),
        'assegnatari_conoscenza_dipendenti_required': fields.related('config_id', 'assegnatari_conoscenza_dipendenti_required',
                 type='boolean', string='Dipendenti assegnatari per conoscenza'),
        'classificazione_senza_doc_required': fields.related('config_id', 'classificazione_senza_doc_required', type='boolean',
                                                   string='Classificazione (senza documento)'),
        'fascicolazione_senza_doc_required': fields.related('config_id', 'fascicolazione_senza_doc_required', type='boolean',
                                                  string='Fascicolazione (senza documento)'),

        'assegnatari_competenza_uffici_senza_doc_required': fields.related('config_id', 'assegnatari_competenza_uffici_senza_doc_required',
                                                                 type='boolean',
                                                                 string='Uffici assegnatari per competenza (senza documento)'),
        'assegnatari_competenza_dipendenti_senza_doc_required': fields.related('config_id',
                                                                     'assegnatari_competenza_dipendenti_senza_doc_required',
                                                                     type='boolean',
                                                                     string='Dipendenti assegnatari per competenza (senza documento)'),
        'assegnatari_conoscenza_uffici_senza_doc_required': fields.related('config_id', 'assegnatari_conoscenza_uffici_senza_doc_required',
                                                                 type='boolean',
                                                                 string='Uffici assegnatari per conoscenza (senza documento)'),
        'assegnatari_conoscenza_dipendenti_senza_doc_required': fields.related('config_id',
                                                                     'assegnatari_conoscenza_dipendenti_senza_doc_required',
                                                                     type='boolean',
                                                                     string='Dipendenti assegnatari per conoscenza (senza documento)'),
        'documento_required': fields.related('config_id', 'documento_required',
                 type='boolean', string='Documento principale'),
        'documento_descrizione_required': fields.related('config_id', 'documento_descrizione_required',
                                                        type='boolean', string='Descrizione documento'),
        'allegati_descrizione_required': fields.related('config_id', 'allegati_descrizione_required',
                                             type='boolean', string='Descrizione allegati'),
        'data_ricezione_required': fields.related('config_id', 'data_ricezione_required',
                                             type='boolean', string='Data di ricezione (in ingresso)'),
        'aggiungi_allegati_post_registrazione': fields.related('config_id', 'aggiungi_allegati_post_registrazione',
                                             type='boolean', string='Aggiungi allegato Post-Registrazione'),
        'email_pec_unique': fields.related('config_id', 'email_pec_unique', type='boolean', string='PEC/Email Univoca'),
        'lunghezza_massima_oggetto_mail': fields.related('config_id', 'lunghezza_massima_oggetto_mail', type='integer', string='Lunghezza massima dell\'oggetto dell\'e-mail', help='Inserire 0 per non limitare l\'oggetto'),
        'lunghezza_massima_oggetto_pec': fields.related('config_id', 'lunghezza_massima_oggetto_pec', type='integer', string='Lunghezza massima dell\'oggetto della PEC', help='Inserire 0 per non limitare l\'oggetto'),
        'send_email_for_each_receiver': fields.related('config_id', 'send_email_for_each_receiver', type='boolean', string='Invia una e-mail per ogni destinatario'),
        'send_pec_for_each_receiver': fields.related('config_id', 'send_pec_for_each_receiver', type='boolean', string='Invia una PEC per ogni destinatario'),

        'non_classificati_active': fields.related('config_id', 'non_classificati_active', type='boolean',
                                                  string='Visualizza Box "Da Classificare"'),
        'non_fascicolati_active': fields.related('config_id', 'non_fascicolati_active', type='boolean',
                                                  string='Visualizza Box "Da Fascicolare"'),

        'sostituisci_assegnatari': fields.related('config_id', 'sostituisci_assegnatari', type='boolean',
                                                 string='Sostituisci Assegnatari Default in Modifica Classificazione'),

        'assegnazione': fields.related('config_id', 'assegnazione', type='selection', selection=[('all', 'Uffici e Utenti'), ('department', 'Solo Uffici')], string='Assegnazione'),

        'select_eml': fields.related('config_id', 'select_eml', type='boolean', string='Abilita Scelta Intero Messaggio (file .EML)'),
        'select_body': fields.related('config_id', 'select_body', type='boolean', string='Abilita Scelta Corpo del Messaggio'),
        'select_attachments': fields.related('config_id', 'select_attachments', type='boolean', string='Abilita Scelta Allegati'),
        'ammi_logo': fields.related('config_id', 'ammi_logo', type='binary', attacchment=True, string="Logo")
    }

    def _default_config_id(self, cr, uid, context):
        ir_model_data_obj = self.pool.get('ir.model.data')
        ir_model_data_id = ir_model_data_obj.search(cr, uid, [('name', '=', 'configurazione_protocollo_default')])[0]
        ir_model_data = ir_model_data_obj.browse(cr, uid, ir_model_data_id)
        return ir_model_data.res_id

    _defaults = {
        'config_id': lambda self,cr,uid,c: self._default_config_id(cr, uid, c),
    }

    def on_change_config_id(self, cr, uid, ids, config_id, context=None):
        config_data = self.pool.get('protocollo.configurazione').read(cr, uid, [config_id], [], context=context)[0]
        values = {}
        for fname, v in config_data.items():
            if fname in self._columns:
                values[fname] = v[0] if v and self._columns[fname]._type == 'many2one' else v
        return {'value': values}


    # FIXME in trunk for god sake. Change the fields above to fields.char instead of fields.related,
    # and create the function set_website who will set the value on the website_id
    # create does not forward the values to the related many2one. Write does.
    def create(self, cr, uid, vals, context=None):
        config_id = super(protocollo_config_settings, self).create(cr, SUPERUSER_ID, vals, context=context)
        self.write(cr, SUPERUSER_ID, config_id, vals, context=context)
        return config_id



class base_config_settings(osv.TransientModel):
    _inherit = 'base.config.settings'

    _columns = {
        'auth_signup_disable_email_create_user': fields.boolean('Disabilita l\'invio email alla creazione dell\'utente'),
        'auth_signup_disable_email_create_employee': fields.boolean('Disabilita l\'invio email alla creazione del dipendente')
    }

    def get_default_auth_signup_settings(self, cr, uid, fields, context=None):
        default_values = {}
        icp = self.pool.get('ir.config_parameter')
        # we use safe_eval on the result, since the value of the parameter is a nonempty string
        default_values['auth_signup_disable_email_create_user'] = safe_eval(icp.get_param(cr, uid, 'auth_signup.disable_email_create_user', 'False'))
        default_values['auth_signup_disable_email_create_employee'] = safe_eval(icp.get_param(cr, uid, 'auth_signup.disable_email_create_employee', 'False'))
        return default_values

    def set_auth_signup_settings(self, cr, uid, ids, context=None):
        config = self.browse(cr, uid, ids[0], context=context)
        icp = self.pool.get('ir.config_parameter')
        # we store the repr of the values, since the value of the parameter is a required string
        icp.set_param(cr, uid, 'auth_signup.disable_email_create_user', repr(config.auth_signup_disable_email_create_user))
        icp.set_param(cr, uid, 'auth_signup.disable_email_create_employee', repr(config.auth_signup_disable_email_create_employee))

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
