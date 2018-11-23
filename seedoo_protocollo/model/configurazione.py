# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import orm, fields


class protocollo_configurazione(orm.Model):
    _name = 'protocollo.configurazione'
    _columns = {
        'inserisci_testo_mailpec': fields.boolean('Abilita testo e-mail/PEC'),
        'rinomina_documento_allegati': fields.boolean('Rinomina documento principale e allegati'),
        'rinomina_oggetto_mail_pec': fields.boolean('Rinomina oggetto e-mail/PEC'),
        'genera_segnatura': fields.boolean('Genera Segnatura nel PDF'),
        'segnatura_xml_parse': fields.boolean('Leggi Segnatura.xml'),
        'segnatura_xml_invia': fields.boolean('Invia Segnatura.xml'),
        'conferma_xml_parse': fields.boolean('Leggi Configurazione.xml relativi ai protocolli in uscita'),
        'conferma_xml_invia': fields.boolean('Invia Configurazione.xml nei protocolli in ingresso'),
        'annullamento_xml_parse': fields.boolean('Leggi Annullamento.xml in ingresso'),
        'annullamento_xml_invia': fields.boolean('Invia Annullamento.xml nei protocolli in ingresso'),
        'classificazione_required': fields.boolean('Classificazione Obbligatoria'),
        'fascicolazione_required': fields.boolean('Fascicolazione Obbligatoria'),

        'assegnatari_competenza_uffici_required': fields.boolean('Uffici assegnatari per competenza Obbligatori'),
        'assegnatari_competenza_dipendenti_required': fields.boolean('Dipendenti assegnatari per competenza Obbligatori'),
        'assegnatari_conoscenza_uffici_required': fields.boolean('Uffici assegnatari per conoscenza Obbligatori'),
        'assegnatari_conoscenza_dipendenti_required': fields.boolean('Dipendenti assegnatari per conoscenza Obbligatori'),

        'documento_required': fields.boolean('Documento Obbligatorio'),
        'allegati_descrizione_required': fields.boolean('Descrizione allegati Obbligatoria'),
        'data_ricezione_required': fields.boolean('Data Ricezione (in ingresso) Obbligatoria'),

        'aggiungi_allegati_post_registrazione': fields.boolean('Aggiungi allegati Post Registrazione'),
        'lunghezza_massima_oggetto_mail': fields.integer('Lunghezza massima oggetto e-mail'),
        'lunghezza_massima_oggetto_pec': fields.integer('Lunghezza massima oggetto PEC'),
        'email_pec_unique': fields.boolean('PEC/Email Univoca'),

        'non_classificati_active': fields.boolean('Visualizza Box "Non Classificati" nella Dashboard'),
        'non_fascicolati_active': fields.boolean('Visualizza Box "Non Fascicolati" nella Dashboard'),

        'sostituisci_assegnatari': fields.boolean('Sostituisci Assegnatari Default in Modifica Classificazione'),

        'assegnazione': fields.selection([('all', 'Uffici e Utenti'), ('department', 'Solo Uffici')], 'Assegnazione'),

        'select_eml': fields.boolean('Abilita Scelta Intero Messaggio (file .EML)'),
        'select_body': fields.boolean('Abilita Scelta Corpo del Messaggio'),
        'select_attachments': fields.boolean('Abilita Scelta Allegati')
    }

    _defaults = {
        'inserisci_testo_mailpec': False,
        'rinomina_documento_allegati': True,
        'rinomina_oggetto_mail_pec': True,
        'genera_segnatura': False,
        'classificazione_required': False,
        'fascicolazione_required': False,
        'assegnatari_competenza_uffici_required': False,
        'assegnatari_competenza_dipendenti_required': False,
        'assegnatari_conoscenza_uffici_required': False,
        'assegnatari_conoscenza_dipendenti_required': False,
        'documento_required': False,
        'allegati_descrizione_required': False,
        'data_ricezione_required': False,
        'aggiungi_allegati_post_registrazione': False,
        'lunghezza_massima_oggetto_mail': 256,
        'lunghezza_massima_oggetto_pec': 256,
        'email_pec_unique': True,
        'non_classificati_active': True,
        'non_fascicolati_active': True,
        'sostituisci_assegnatari': True,
        'assegnazione': 'all',
        'select_eml': True,
        'select_body': True,
        'select_attachments': True
    }

    def verifica_campi_obbligatori(self, cr, uid, protocollo):
        configurazione_ids = self.pool.get('protocollo.configurazione').search(cr, uid, [])
        configurazione = self.pool.get('protocollo.configurazione').browse(cr, uid, configurazione_ids[0])

        campi_obbligatori = ''

        if not protocollo.registration_employee_department_id:
            campi_obbligatori = campi_obbligatori + '<li>Ufficio del Protocollo</li>'
        else:
            employee_ids = self.pool.get('hr.employee').search(cr, uid, [
                ('user_id', '=', uid),
                ('department_id', '=', protocollo.registration_employee_department_id.id)
            ])
            if not employee_ids:
                campi_obbligatori = campi_obbligatori + '<li>Ufficio del Protocollo: la tua utenza non ha dipendenti collegati all\'ufficio selezionato</li>'
        if not protocollo.typology:
            campi_obbligatori = campi_obbligatori + '<li>Mezzo Trasmissione</li>'
        if not protocollo.subject:
            campi_obbligatori = campi_obbligatori + '<li>Oggetto</li>'
        if not protocollo.sender_receivers:
            send_rec = protocollo.type == 'in' and '<li>Mittenti</li>' or '<li>Destinatari</li>'
            campi_obbligatori = campi_obbligatori + send_rec
        if protocollo.type == 'in' and (protocollo.pec or protocollo.sharedmail):
            for sr in protocollo.sender_receivers:
                if not sr.name:
                    campi_obbligatori = campi_obbligatori + '<li>Nome Cognome/Ragione sociale del Mittente</li>'
                    break

        if protocollo.type == 'out' and protocollo.pec:
            for sr in protocollo.sender_receivers:
                if not sr.pec_mail:
                    campi_obbligatori = campi_obbligatori + '<li>Mail PEC dei Destinatari</li>'
                    break

        if protocollo.type == 'out' and protocollo.sharedmail:
            for sr in protocollo.sender_receivers:
                if not sr.email:
                    campi_obbligatori = campi_obbligatori + '<li>Mail dei Destinatari</li>'
                    break

        if configurazione:
            if configurazione.classificazione_required and not protocollo.classification:
                campi_obbligatori = campi_obbligatori + '<li>Titolario</li>'
            if configurazione.fascicolazione_required and not protocollo.dossier_ids:
                campi_obbligatori = campi_obbligatori + '<li>Fascicolario</li>'

            competenza_ufficio_found = False
            competenza_dipendente_found = False
            conoscenza_ufficio_found = False
            conoscenza_dipendente_found = False
            for assegnazione in protocollo.assegnazione_first_level_ids:
                if assegnazione.tipologia_assegnazione=='competenza' and assegnazione.tipologia_assegnatario=='department':
                    competenza_ufficio_found = True
                if assegnazione.tipologia_assegnazione=='competenza' and assegnazione.tipologia_assegnatario=='employee':
                    competenza_dipendente_found = True
                if assegnazione.tipologia_assegnazione=='conoscenza' and assegnazione.tipologia_assegnatario=='department':
                    conoscenza_ufficio_found = True
                if assegnazione.tipologia_assegnazione=='conoscenza' and assegnazione.tipologia_assegnatario=='employee':
                    conoscenza_dipendente_found = True

            if protocollo.reserved:
                if competenza_ufficio_found:
                    campi_obbligatori = campi_obbligatori + '<li>Dipendente Assegnatario per Competenza: i protocollo riservati non possono avere uffici come assegnatari per competenza</li>'
                elif not competenza_dipendente_found:
                    campi_obbligatori = campi_obbligatori + '<li>Dipendente Assegnatario per Competenza</li>'
                if conoscenza_ufficio_found or conoscenza_dipendente_found:
                    campi_obbligatori = campi_obbligatori + '<li>Assegnatari per Conoscenza: i protocollo riservati non possono avere assegnatari per conoscenza</li>'
            else:
                if configurazione.assegnatari_competenza_uffici_required and \
                        not configurazione.assegnatari_competenza_dipendenti_required and \
                        not competenza_ufficio_found:
                    campi_obbligatori = campi_obbligatori + '<li>Ufficio Assegnatario per Competenza</li>'
                if configurazione.assegnatari_competenza_dipendenti_required \
                        and not configurazione.assegnatari_competenza_uffici_required and \
                        not competenza_dipendente_found:
                    campi_obbligatori = campi_obbligatori + '<li>Dipendente Assegnatario per Competenza</li>'
                if configurazione.assegnatari_competenza_dipendenti_required \
                        and configurazione.assegnatari_competenza_uffici_required \
                        and not competenza_ufficio_found and not competenza_dipendente_found:
                    campi_obbligatori = campi_obbligatori + '<li>Assegnatario per Competenza</li>'
                if configurazione.assegnatari_conoscenza_uffici_required and \
                        not conoscenza_ufficio_found:
                    campi_obbligatori = campi_obbligatori + '<li>Uffici Assegnatari per Conoscenza</li>'
                if configurazione.assegnatari_conoscenza_dipendenti_required and \
                        not conoscenza_dipendente_found:
                    campi_obbligatori = campi_obbligatori + '<li>Dipendenti Assegnatari per Conoscenza</li>'

            if configurazione.documento_required and not protocollo.doc_id:
                campi_obbligatori = campi_obbligatori + '<li>Documento principale</li>'
            if configurazione.allegati_descrizione_required:
                for attach in protocollo.attachment_ids:
                    if not attach.datas_description:
                        campi_obbligatori = campi_obbligatori + '<li>Descrizione allegato: ' + attach.name.encode('utf-8') + '</li>'
            if protocollo.type == 'in' and configurazione.data_ricezione_required and not protocollo.receiving_date:
                campi_obbligatori = campi_obbligatori + '<li>Data di ricezione</li>'

            if not protocollo.doc_id.ids and protocollo.attachment_ids:
                campi_obbligatori = campi_obbligatori + '<li>Documento principale (obbligatorio se sono presenti allegati)</li>'

        if campi_obbligatori:
            return '<div class="verifica-campi-container"><p><i class="fa fa-warning"/></i>Valorizzare correttamente i seguenti campi per procedere alla registrazione:</p><ul>' + campi_obbligatori + '</ul></div>'

        return True
