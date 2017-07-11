# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp import exceptions
from openerp.osv import orm, fields
from openerp.tools.translate import _


class protocollo_configurazione(orm.Model):
    _name = 'protocollo.configurazione'
    _columns = {
        'genera_segnatura': fields.boolean('Genera Segnatura nel PDF'),
        'genera_xml_segnatura': fields.boolean('Genera XML Segnatura'),

        'classificazione_required': fields.boolean('Classificazione Obbligatoria'),
        'fascicolazione_required': fields.boolean('Fascicolazione Obbligatoria'),

        'assegnatari_competenza_uffici_required': fields.boolean('Uffici Assegnatari per Competenza Obbligatori'),
        'assegnatari_competenza_dipendenti_required': fields.boolean('Dipendenti Assegnatari per Competenza Obbligatori'),
        'assegnatari_conoscenza_uffici_required': fields.boolean('Uffici Assegnatari per Conoscenza Obbligatori'),
        'assegnatari_conoscenza_dipendenti_required': fields.boolean('Dipendenti Assegnatari per Conoscenza Obbligatori'),
    }

    _defaults = {
        'genera_segnatura': True,
        'genera_xml_segnatura': True,
        'classificazione_required': False,
        'fascicolazione_required': False,
        'assegnatari_competenza_uffici_required': False,
        'assegnatari_competenza_dipendenti_required': False,
        'assegnatari_conoscenza_uffici_required': False,
        'assegnatari_conoscenza_dipendenti_required': False,
    }

    def verifica_campi_obbligatori(self, cr, uid, protocollo):
        configurazione_ids = self.pool.get('protocollo.configurazione').search(cr, uid, [])
        configurazione = self.pool.get('protocollo.configurazione').browse(cr, uid, configurazione_ids[0])

        campi_obbligatori = ''

        if not protocollo.subject:
            campi_obbligatori = campi_obbligatori + '\n- Oggetto'
        if not protocollo.sender_receivers:
            send_rec = protocollo.type == 'in' and '\n- Mittenti' or '\n- Destinatari'
            campi_obbligatori = campi_obbligatori + send_rec
        if protocollo.type == 'out' and protocollo.pec:
            for sr in protocollo.sender_receivers:
                if not sr.pec_mail:
                    campi_obbligatori = campi_obbligatori + '\n- Mail PEC dei Destinatari'
                    break

        if configurazione:
            if configurazione.classificazione_required and not protocollo.classification:
                campi_obbligatori = campi_obbligatori + '\n- Titolario'
            if configurazione.fascicolazione_required and not protocollo.dossier_ids:
                campi_obbligatori = campi_obbligatori + '\n- Fascicolario'
            if configurazione.assegnatari_competenza_uffici_required and not protocollo.assegnatari_competenza_uffici_ids:
                campi_obbligatori = campi_obbligatori + '\n- Uffici Assegnatari per Competenza'
            if configurazione.assegnatari_competenza_dipendenti_required and not protocollo.assegnatari_competenza_dipendenti_ids:
                campi_obbligatori = campi_obbligatori + '\n- Dipendenti Assegnatari per Competenza'
            if configurazione.assegnatari_conoscenza_uffici_required and not protocollo.assegnatari_conoscenza_uffici_ids:
                campi_obbligatori = campi_obbligatori + '\n- Uffici Assegnatari per Conoscenza'
            if configurazione.assegnatari_conoscenza_dipendenti_required and not protocollo.assegnatari_conoscenza_dipendenti_ids:
                campi_obbligatori = campi_obbligatori + '\n- Dipendenti Assegnatari per Conoscenza'

        if campi_obbligatori:
            raise exceptions.Warning('Prima di procedere con la registrazione è necessario valorizzare i seguenti campi: ' + campi_obbligatori)

        return True
