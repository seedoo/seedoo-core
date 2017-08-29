# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

import dateutil
import inspect
import os
from lxml import etree

# from seedoo_protocollo.model.protocollo import protocollo_protocollo
import openerp
from openerp.tools.translate import _


class ConfermaXML:
    def __init__(self, protocollo, cr, uid):
        self.protocollo = protocollo
        # self.prot_number = prot_number
        # date_object = dateutil.parser.parse(prot_date)
        # self.prot_date = date_object
        self.prot_type = protocollo.type
        self.cr = cr
        self.uid = uid

        self.pooler = protocollo.pool
        self.resUsersObj = self.pooler.get("res.users")
        self.protocolloObj = self.pooler.get("protocollo.protocollo")
        self.resCompanyObj = self.pooler.get("res.company")
        self.irAttachmentObj = self.pooler.get("ir.attachment")

        self.currentUser = self.resUsersObj.browse(cr, uid, uid)
        companyId = self.currentUser.company_id.id
        self.company = self.resCompanyObj.browse(cr, uid, companyId)

        if protocollo.aoo_id.ident_code is not False:
            self.codiceAOO = str(protocollo.aoo_id.ident_code)
        else:
            self.codiceAOO = None

        pass

    def generate_conferma_root(self):
        root = etree.Element("Conferma")
        intestazione = self.create_intestazione()
        descrizione = self.createDescrizione()
        root.append(intestazione)
        root.append(descrizione)
        if self.validateXml(root):
            return root
        else:
            raise openerp.exceptions.Warning(
                _('Errore nella validazione xml conferma'))

    def validateXml(self, root):
        directory_path = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        fullPath = os.path.join(directory_path, '../data/segnatura.dtd')
        dtdfile = open(fullPath, 'r')
        dtd = etree.DTD(dtdfile)
        isValid = dtd.validate(root)
        if not isValid:
            print dtd.error_log.filter_from_errors()

        return isValid

    def createDescrizione(self):
        descrizione = etree.Element("Descrizione")
        testoDelMessaggio = self.createTestoDelMessaggio()
        descrizione.append(testoDelMessaggio)
        return descrizione

    def createNote(self, notes=""):
        note = etree.Element("Note")
        note.text = notes
        return note

    def createTestoDelMessaggio(self, body=""):
        testoDelMessaggio = etree.Element("TestoDelMessaggio")
        return testoDelMessaggio

    def createDestinatarioFromSenderReceiver(self, senderReceiver):
        destinatario = etree.Element("Destinatario")

        if senderReceiver.type == "individual":  # Persona fisica
            denominazione = self.createDenominazione(senderReceiver.name)
            destinatario.append(denominazione)
            persona = self.createPersonaFromSenderReceiver(senderReceiver)
            destinatario.append(persona)
            indirizzoTelematico = \
                self.createIndirizzoTelematicoFromSenderReceiver(
                    senderReceiver)
            destinatario.append(indirizzoTelematico)
            indirizzoPostale = self.createIndirizzoPostaleFromSenderReceiver(
                senderReceiver)
            destinatario.append(indirizzoPostale)
        elif senderReceiver.type == "legal":  # Azienda privata
            azienda = self.createAmministrazioneFakeFromSenderReceiver(
                senderReceiver)
            destinatario.append(azienda)
            aOO = self.createAOO()
            destinatario.append(aOO)
            privato = self.createPrivatoFromSenderReceiver(senderReceiver)
            destinatario.append(privato)
        elif senderReceiver.type == "government":  # Amministrazione pubblica
            amministrazione = self.createAmministrazioneFromSenderReceiver(
                senderReceiver)
            destinatario.append(amministrazione)
            aOO = self.createAOO()
            destinatario.append(aOO)

        return destinatario

    def createIdentificatore(self):
        identificatore = etree.Element("Identificatore")
        # TODO Recuperare da qualche parte il codice amministrazione (codice
        #  IPA??)
        codiceAmministrazione = self.createCodiceAmministrazione()
        codiceAOO = self.createCodiceAOO(self.codiceAOO)
        numeroRegistrazione = self.createNumeroRegistrazione(self.prot_number)
        dataRegistrazione = self.createDataRegistrazione(self.prot_date)
        identificatore.append(codiceAmministrazione)
        identificatore.append(codiceAOO)
        identificatore.append(numeroRegistrazione)
        identificatore.append(dataRegistrazione)
        return identificatore

    def createDataRegistrazione(self, dataRegistrazioneVal):
        dataRegistrazione = etree.Element("DataRegistrazione")
        dataRegistrazione.text = dataRegistrazioneVal.date().isoformat()
        return dataRegistrazione

    def createNumeroRegistrazione(self, numeroRegistrazioneVal):
        numeroRegistrazione = etree.Element("NumeroRegistrazione")
        numeroRegistrazione.text = numeroRegistrazioneVal
        return numeroRegistrazione

    def createCodiceAOO(self, codiceAOOVal=""):
        codiceAOO = etree.Element("CodiceAOO")
        codiceAOO.text = codiceAOOVal
        return codiceAOO

    def createCodiceAmministrazione(self, code=""):
        # TODO Recuperare da qualche parte il codice amministrazione (codice
        #  IPA??)
        codiceAmministrazione = etree.Element("CodiceAmministrazione")
        codiceAmministrazione.text = self.checkNullValue(code)
        return codiceAmministrazione

    def create_messaggio_ricevuto(self):
        messaggio_ricevuto = etree.Element("MessaggioRicevuto")
        return messaggio_ricevuto