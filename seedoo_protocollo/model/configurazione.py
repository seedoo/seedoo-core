# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp import exceptions
from openerp.osv import orm, fields
from openerp.tools.translate import _


class protocollo_configurazione(orm.Model):
    _name = 'protocollo.configurazione'
    _columns = {
        'inserisci_testo_mailpec': fields.boolean('Abilita testo E-mail/PEC'),
        'rinomina_documento_allegati': fields.boolean('Rinomina documento principale e allegati'),
        'rinomina_oggetto_mail_pec': fields.boolean('Rinomina oggetto mail/PEC'),
        'genera_segnatura': fields.boolean('Genera Segnatura nel PDF'),
        'segnatura_xml_parse': fields.boolean('Leggi Segnatura.xml'),
        'segnatura_xml_invia': fields.boolean('Invia Segnatura.xml'),
        'conferma_xml_parse': fields.boolean('Leggi Configurazione.xml relativi ai protocolli in uscita'),
        'conferma_xml_invia': fields.boolean('Invia Configurazione.xml nei protocolli in ingresso'),
        'annullamento_xml_parse': fields.boolean('Leggi Annullamento.xml in ingresso'),
        'annullamento_xml_invia': fields.boolean('Invia Annullamento.xml nei protocolli in ingresso'),
        'classificazione_required': fields.boolean('Classificazione Obbligatoria'),
        'fascicolazione_required': fields.boolean('Fascicolazione Obbligatoria'),

        'assegnatari_competenza_uffici_required': fields.boolean('Uffici Assegnatari per Competenza Obbligatori'),
        'assegnatari_competenza_dipendenti_required': fields.boolean('Dipendenti Assegnatari per Competenza Obbligatori'),
        'assegnatari_conoscenza_uffici_required': fields.boolean('Uffici Assegnatari per Conoscenza Obbligatori'),
        'assegnatari_conoscenza_dipendenti_required': fields.boolean('Dipendenti Assegnatari per Conoscenza Obbligatori'),

        'documento_required': fields.boolean('Documento Obbligatorio'),
        'allegati_descrizione_required': fields.boolean('Descrizione Allegati Obbligatoria'),

        'aggiungi_allegati_post_registrazione': fields.boolean('Aggiungi allegati post registrazione'),
        'lunghezza_massima_oggetto_mail': fields.integer('Lunghezza massima dell\'oggetto della mail'),
        'lunghezza_massima_oggetto_pec': fields.integer('Lunghezza massima dell\'oggetto della PEC'),
        'email_pec_unique': fields.boolean('PEC/Email Univoca'),
    }

    _defaults = {
        'inserisci_testo_mailpec': False,
        'rinomina_documento_allegati': True,
        'rinomina_oggetto_mail_pec': True,
        'genera_segnatura': True,
        'classificazione_required': False,
        'fascicolazione_required': False,
        'assegnatari_competenza_uffici_required': False,
        'assegnatari_competenza_dipendenti_required': False,
        'assegnatari_conoscenza_uffici_required': False,
        'assegnatari_conoscenza_dipendenti_required': False,
        'documento_required': False,
        'allegati_descrizione_required': False,
        'aggiungi_allegati_post_registrazione': False,
        'lunghezza_massima_oggetto_mail': 256,
        'lunghezza_massima_oggetto_pec': 256,
        'email_pec_unique': True,
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

        if protocollo.type == 'in' and (protocollo.pec or protocollo.sharedmail):
            for sr in protocollo.sender_receivers:
                if not sr.name:
                    campi_obbligatori = campi_obbligatori + '\n- Nome Cognome/Ragione sociale del Mittente'
                    break

        if protocollo.type == 'out' and protocollo.pec:
            for sr in protocollo.sender_receivers:
                if not sr.pec_mail:
                    campi_obbligatori = campi_obbligatori + '\n- Mail PEC dei Destinatari'
                    break

        if protocollo.type == 'out' and protocollo.sharedmail:
            for sr in protocollo.sender_receivers:
                if not sr.email:
                    campi_obbligatori = campi_obbligatori + '\n- Mail dei Destinatari'
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
            if configurazione.allegati_descrizione_required and not protocollo.doc_id:
                campi_obbligatori = campi_obbligatori + '\n- Documento principale'
            if configurazione.allegati_descrizione_required:
                for attach in protocollo.attachment_ids:
                    if len(attach.datas_description) == 0:
                        campi_obbligatori = campi_obbligatori + '\n- Descrizione allegato: ' + attach.name.encode('utf-8')

        if campi_obbligatori:
            raise exceptions.Warning('Prima di procedere con la registrazione è necessario valorizzare i seguenti campi: ' + campi_obbligatori)

        return True
