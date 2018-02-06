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

from openerp.osv import fields, osv
from openerp import SUPERUSER_ID

class protocollo_config_settings(osv.osv_memory):
    _name = 'protocollo.config.settings'
    _inherit = 'res.config.settings'

    _columns = {
        'config_id': fields.many2one('protocollo.configurazione', string='Configurazione', required=True),
        'inserisci_testo_mailpec': fields.related('config_id', 'inserisci_testo_mailpec', type='boolean', string='Abilita testo E-mail/PEC protocollo'),
        'rinomina_documento_allegati': fields.related('config_id', 'rinomina_documento_allegati', type='boolean', string='Rinomina Documento principale e allegati'),
        'rinomina_oggetto_mail_pec': fields.related('config_id', 'rinomina_oggetto_mail_pec', type='boolean', string='Rinomina oggetto mail/PEC'),
        'genera_segnatura': fields.related('config_id', 'genera_segnatura', type='boolean', string='Genera Segnatura nel PDF'),
        'genera_xml_segnatura': fields.related('config_id', 'genera_xml_segnatura', type='boolean', string='Genera XML Segnatura'),
        'segnatura_xml_parse': fields.related('config_id', 'segnatura_xml_parse', type='boolean', string='Leggi Segnatura.xml'),
        'segnatura_xml_invia': fields.related('config_id', 'segnatura_xml_invia', type='boolean', string='Invia Segnatura.xml'),
        'conferma_xml_parse': fields.related('config_id', 'conferma_xml_parse', type='boolean', string='Leggi Configurazione.xml relativi ai protocolli in uscita'),
        'conferma_xml_invia': fields.related('config_id', 'conferma_xml_invia', type='boolean', string='Invia Configurazione.xml nei protocolli in ingresso'),
        'annullamento_xml_parse': fields.related('config_id', 'annullamento_xml_parse', type='boolean', string='Leggi Annullamento.xml relativi ai protocolli in uscita'),
        'annullamento_xml_invia': fields.related('config_id', 'annullamento_xml_invia', type='boolean', string='Invia Annullamento.xml nei protocolli in ingresso'),
        'classificazione_required': fields.related('config_id', 'classificazione_required', type='boolean', string='Classificazione'),
        'fascicolazione_required': fields.related('config_id', 'fascicolazione_required', type='boolean', string='Fascicolazione'),

        'assegnatari_competenza_uffici_required': fields.related('config_id', 'assegnatari_competenza_uffici_required',
                 type='boolean', string='Uffici Assegnatari per Competenza'),
        'assegnatari_competenza_dipendenti_required': fields.related('config_id', 'assegnatari_competenza_dipendenti_required',
                 type='boolean', string='Dipendenti Assegnatari per Competenza'),
        'assegnatari_conoscenza_uffici_required': fields.related('config_id', 'assegnatari_conoscenza_uffici_required',
                 type='boolean', string='Uffici Assegnatari per Conoscenza'),
        'assegnatari_conoscenza_dipendenti_required': fields.related('config_id', 'assegnatari_conoscenza_dipendenti_required',
                 type='boolean', string='Dipendenti Assegnatari per Conoscenza'),
        'documento_required': fields.related('config_id', 'documento_required',
                 type='boolean', string='Documento Principale'),
        'aggiungi_allegati_post_registrazione': fields.related('config_id', 'aggiungi_allegati_post_registrazione',
                                             type='boolean', string='Aggiungi allegato post registrazione'),
        'email_pec_unique': fields.related('config_id', 'email_pec_unique', type='boolean', string='PEC/Email Univoca'),
        'lunghezza_massima_oggetto_mail': fields.related('config_id', 'lunghezza_massima_oggetto_mail', type='integer', string='Lunghezza massima dell\'oggetto della mail', help='Inserire 0 per non limitare l\'oggetto'),
        'lunghezza_massima_oggetto_pec': fields.related('config_id', 'lunghezza_massima_oggetto_pec', type='integer', string='Lunghezza massima dell\'oggetto della pec', help='Inserire 0 per non limitare l\'oggetto'),
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

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
