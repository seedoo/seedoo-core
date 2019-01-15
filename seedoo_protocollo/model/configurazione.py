# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import orm, fields
from openerp.tools.translate import _


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

        'classificazione_senza_doc_required': fields.boolean('Classificazione Obbligatoria (senza documento)'),
        'fascicolazione_senza_doc_required': fields.boolean('Fascicolazione Obbligatoria (senza documento)'),

        'assegnatari_competenza_uffici_senza_doc_required': fields.boolean('Uffici assegnatari per competenza Obbligatori (senza documento)'),
        'assegnatari_competenza_dipendenti_senza_doc_required': fields.boolean(
            'Dipendenti assegnatari per competenza Obbligatori (senza documento)'),
        'assegnatari_conoscenza_uffici_senza_doc_required': fields.boolean('Uffici assegnatari per conoscenza Obbligatori (senza documento)'),
        'assegnatari_conoscenza_dipendenti_senza_doc_required': fields.boolean(
            'Dipendenti assegnatari per conoscenza Obbligatori (senza documento)'),

        'documento_required': fields.boolean('Documento Obbligatorio'),
        'documento_descrizione_required': fields.boolean('Descrizione Documento Obbligatoria'),
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
        'classificazione_senza_doc_required': False,
        'fascicolazione_senza_doc_required': False,
        'assegnatari_competenza_uffici_senza_doc_required': False,
        'assegnatari_competenza_dipendenti_senza_doc_required': False,
        'assegnatari_conoscenza_uffici_senza_doc_required': False,
        'assegnatari_conoscenza_dipendenti_senza_doc_required': False,
        'documento_required': False,
        'documento_descrizione_required': False,
        'allegati_descrizione_required': False,
        'data_ricezione_required': False,
        'aggiungi_allegati_post_registrazione': False,
        'lunghezza_massima_oggetto_mail': 256,
        'lunghezza_massima_oggetto_pec': 256,
        'email_pec_unique': True,
        'non_classificati_active': False,
        'non_fascicolati_active': False,
        'sostituisci_assegnatari': True,
        'assegnazione': 'all',
        'select_eml': True,
        'select_body': True,
        'select_attachments': True
    }


    def verifica_campi_non_configurati(self, cr, uid, protocollo):
        errors = []

        if not protocollo.registration_employee_department_id:
            errors.append(_("Ufficio del Protocollo"))
        else:
            employee_ids = self.pool.get('hr.employee').search(cr, uid, [
                ('user_id', '=', uid),
                ('department_id', '=', protocollo.registration_employee_department_id.id)
            ])
            if not employee_ids:
                errors.append(_("Ufficio del Protocollo: la tua utenza non ha dipendenti collegati all'ufficio selezionato"))
        if protocollo.type != 'internal' and not protocollo.typology:
            errors.append(_("Mezzo Trasmissione"))
        if not protocollo.subject:
            errors.append(_("Oggetto"))
        if protocollo.type != 'internal' and not protocollo.sender_receivers:
            send_rec = protocollo.type == 'in' and _("Mittenti") or _("Destinatari")
            errors.append(send_rec)
        if protocollo.type == 'in' and (protocollo.pec or protocollo.sharedmail):
            for sr in protocollo.sender_receivers:
                if not sr.name:
                    errors.append(_("Nome Cognome/Ragione sociale del Mittente"))
                    break

        if protocollo.type == 'internal' and not protocollo.sender_internal_name:
            errors.append(_("Mittente"))

        if protocollo.type == 'out' and protocollo.pec:
            for sr in protocollo.sender_receivers:
                if not sr.pec_mail:
                    errors.append(_("Mail PEC dei Destinatari"))
                    break

        if protocollo.type == 'out' and protocollo.sharedmail:
            for sr in protocollo.sender_receivers:
                if not sr.email:
                    errors.append(_("Mail dei Destinatari"))
                    break

        if not protocollo.doc_id.ids and protocollo.attachment_ids:
            errors.append(_("Documento principale (obbligatorio se sono presenti allegati)"))

        return errors


    def verifica_campi_obbligatori(self, cr, uid, protocollo):
        errors = self.verifica_campi_non_configurati(cr, uid, protocollo)

        configurazione_ids = self.pool.get('protocollo.configurazione').search(cr, uid, [])
        configurazione = self.pool.get('protocollo.configurazione').browse(cr, uid, configurazione_ids[0])
        if configurazione:
            if protocollo.doc_id:
                if configurazione.classificazione_required and not protocollo.classification:
                    errors.append(_("Titolario"))
                if configurazione.fascicolazione_required and not protocollo.dossier_ids:
                    errors.append(_("Fascicolario"))
            else:
                if configurazione.classificazione_senza_doc_required and not protocollo.classification:
                    errors.append(_("Titolario"))
                if configurazione.fascicolazione_senza_doc_required and not protocollo.dossier_ids:
                    errors.append(_("Fascicolario"))

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
                    errors.append(_("Dipendente Assegnatario per Competenza: i protocollo riservati non possono avere uffici come assegnatari per competenza"))
                elif not competenza_dipendente_found:
                    errors.append(_("Dipendente Assegnatario per Competenza"))
                if conoscenza_ufficio_found or conoscenza_dipendente_found:
                    errors.append(_("Assegnatari per Conoscenza: i protocolli riservati non possono avere assegnatari per conoscenza"))
                if protocollo.type == 'internal' and protocollo.sender_internal_department:
                    errors.append(_("Mittente: i protocolli riservati non possono avere uffici come mittenti"))
            else:
                if protocollo.doc_id:
                    if configurazione.assegnatari_competenza_uffici_required and \
                            not configurazione.assegnatari_competenza_dipendenti_required and \
                            not competenza_ufficio_found:
                        errors.append(_("Ufficio Assegnatario per Competenza"))
                    if configurazione.assegnatari_competenza_dipendenti_required \
                            and not configurazione.assegnatari_competenza_uffici_required and \
                            not competenza_dipendente_found:
                        errors.append(_("Dipendente Assegnatario per Competenza"))
                    if configurazione.assegnatari_competenza_dipendenti_required \
                            and configurazione.assegnatari_competenza_uffici_required \
                            and not competenza_ufficio_found and not competenza_dipendente_found:
                        errors.append(_("Assegnatario per Competenza"))
                    if configurazione.assegnatari_conoscenza_uffici_required and \
                            not conoscenza_ufficio_found:
                        errors.append(_("Uffici Assegnatari per Conoscenza"))
                    if configurazione.assegnatari_conoscenza_dipendenti_required and \
                            not conoscenza_dipendente_found:
                        errors.append(_("Dipendenti Assegnatari per Conoscenza"))
                else:
                    if configurazione.assegnatari_competenza_uffici_senza_doc_required and \
                            not configurazione.assegnatari_competenza_dipendenti_senza_doc_required and \
                            not competenza_ufficio_found:
                        errors.append(_("Ufficio Assegnatario per Competenza"))
                    if configurazione.assegnatari_competenza_dipendenti_senza_doc_required \
                            and not configurazione.assegnatari_competenza_uffici_senza_doc_required and \
                            not competenza_dipendente_found:
                        errors.append(_("Dipendente Assegnatario per Competenza"))
                    if configurazione.assegnatari_competenza_dipendenti_senza_doc_required \
                            and configurazione.assegnatari_competenza_uffici_senza_doc_required \
                            and not competenza_ufficio_found and not competenza_dipendente_found:
                        errors.append(_("Assegnatario per Competenza"))
                    if configurazione.assegnatari_conoscenza_uffici_senza_doc_required and \
                            not conoscenza_ufficio_found:
                        errors.append(_("Uffici Assegnatari per Conoscenza"))
                    if configurazione.assegnatari_conoscenza_dipendenti_senza_doc_required and \
                            not conoscenza_dipendente_found:
                        errors.append(_("Dipendenti Assegnatari per Conoscenza"))


            if configurazione.documento_required and not protocollo.doc_id:
                errors.append(_("Documento principale"))
            if configurazione.documento_descrizione_required and protocollo.doc_id and not protocollo.doc_id.datas_description:
                errors.append(_("Descrizione documento principale"))
            if configurazione.allegati_descrizione_required:
                for attach in protocollo.attachment_ids:
                    if not attach.datas_description:
                        errors.append(_("Descrizione allegato: ") + attach.name.encode('utf-8'))
            if protocollo.type == 'in' and configurazione.data_ricezione_required and not protocollo.receiving_date:
                errors.append(_("Data di ricezione"))

        if errors:
            error_message_start = '<div class="verifica-campi-container"><p><i class="fa fa-warning"/></i>'
            error_message_start += _("Valorizzare correttamente i seguenti campi per procedere alla registrazione:") + '</p><ul>'
            error_message_end = '</ul></div>'
            error_message = ''
            for error in errors:
                error_message += '<li>' + error + '</li>'
            return error_message_start + error_message + error_message_end

        return True