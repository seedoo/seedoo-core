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


class SegnaturaXML:
    def __init__(self, protocollo, prot_number, prot_date, cr, uid):
        self.protocollo = protocollo
        self.prot_number = prot_number
        date_object = dateutil.parser.parse(prot_date)
        self.prot_date = date_object
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

        if protocollo.server_pec_id.user is not False:
            self.accountPecProtocollo = protocollo.server_pec_id.user
        else:
            self.accountPecProtocollo = None

        if self.currentUser.employee_ids.department_id.name is not False:
            self.ufficioProtocollatore = self.currentUser.employee_ids.department_id.name
        else:
            self.ufficioProtocollatore = None

        if protocollo.aoo_id.ident_code is not False:
            self.codiceAOO = str(protocollo.aoo_id.ident_code)
            self.denominazioneAOO = str(protocollo.aoo_id.name)
        else:
            self.codiceAOO = None
            self.denominazioneAOO = None

        pass

    def generate_segnatura_root(self):
        root = etree.Element("Segnatura")
        intestazione = self.create_intestazione()
        descrizione = self.createDescrizione()
        root.append(intestazione)
        root.append(descrizione)
        if self.validateXml(root):
            return root
        else:
            raise openerp.exceptions.Warning(
                _('Errore nella validazione xml segnatura'))

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

        protocollo_id = self.protocollo.id
        attachments = self.irAttachmentObj.search(self.cr, self.uid, [
            ('res_model', '=', 'protocollo.protocollo'),
            ('res_id', '=', protocollo_id)])

        docObj = self.protocollo.doc_id
        if docObj and hasattr(docObj, 'name'):
            documento = self.createDocumentoFromIrAttachment(docObj)
            descrizione.append(documento)
        elif self.protocollo.datas_fname:
            documento = self.createDocumento(self.protocollo.datas_fname)
            descrizione.append(documento)
        else:
            testoDelMessaggio = self.createTestoDelMessaggio()
            descrizione.append(testoDelMessaggio)
        if len(attachments) > 1:
            allegati = self.createAllegati(attachments)
            descrizione.append(allegati)
        if self.protocollo.notes:
            note = self.createNote()
            descrizione.append(note)
        return descrizione

    def createNote(self, notes=""):
        note = etree.Element("Note")
        note.text = notes
        return note

    def createTestoDelMessaggio(self, body=""):
        testoDelMessaggio = etree.Element("TestoDelMessaggio")
        return testoDelMessaggio

    def createDocumentoFromIrAttachment(self, document):
        documento = etree.Element("Documento", nome=document.name,
                                  tipoRiferimento="MIME")

        return documento

    def createDocumento(self, name):
        documento = etree.Element("Documento", nome=name,
                                  tipoRiferimento="MIME")

        return documento

    def createAllegati(self, attachments):
        allegati = etree.Element("Allegati")
        for attachment in attachments:
            attachmentObj = self.irAttachmentObj.browse(self.cr, self.uid,
                                                        attachment)
            if attachmentObj is not None:
                documento = self.createDocumentoFromIrAttachment(attachmentObj)
                allegati.append(documento)
        return allegati

    def createFascicolo(self):
        fascicolo = etree.Element("Fascicolo")
        codiceAmministrazione = self.createCodiceAmministrazione()
        codiceAOO = self.createCodiceAOO()
        oggetto = self.createOggetto()
        identificativo = etree.Element("Identificativo")
        classifica = self.createClassifica()
        note = self.createNote()
        documento = self.createDocumentoFromIrAttachment(None)
        fascicolo.append(codiceAmministrazione)
        fascicolo.append(codiceAOO)
        fascicolo.append(oggetto)
        fascicolo.append(identificativo)
        fascicolo.append(classifica)
        fascicolo.append(note)
        fascicolo.append(documento)
        return fascicolo

    def createClassifica(self):
        classifica = etree.Element("Classifica")
        codiceAmministrazione = self.createCodiceAmministrazione()
        codiceAOO = self.createCodiceAOO()
        denominazione = etree.Element("Denominazione")
        livello = etree.Element("Livello")

        classifica.append(codiceAmministrazione)
        classifica.append(codiceAOO)
        classifica.append(denominazione)
        classifica.append(livello)

        return classifica

    def create_intestazione(self):
        intestazione = etree.Element("Intestazione")
        identificatore = self.createIdentificatore()
        intestazione.append(identificatore)

        if self.prot_type == "in":
            origine = self.createOrigineIN()
            intestazione.append(origine)
            destinazione = self.createDestinazioneIN()
            intestazione.append(destinazione)

        elif self.prot_type == "out":
            origine = self.createOrigineOUT()
            intestazione.append(origine)
            destinazione = self.createDestinazioneOUT()
            intestazione.append(destinazione)

        oggetto = self.createOggetto()
        intestazione.append(oggetto)
        return intestazione

    def createOggetto(self):
        oggetto = etree.Element("Oggetto")
        oggetto.text = self.checkNullValue(self.protocollo.subject)

        return oggetto

    def createOggettoFascicolo(self):
        oggetto = etree.Element("Oggetto")
        return oggetto

    def createDestinazioneIN(self):
        destinazione = etree.Element("Destinazione")
        indirizzoTelematico = self.createIndirizzoTelematicoFromCompany(
            self.company)
        destinatario = self.createDestinatarioIN()

        destinazione.append(indirizzoTelematico)
        destinazione.append(destinatario)
        return destinazione

    def createDestinazioneOUT(self):
        destinazione = etree.Element("Destinazione")
        indirizzoTelematico = self.createIndirizzoTelematico("")
        destinazione.append(indirizzoTelematico)
        receivers = self.protocollo.sender_receivers
        for receiver in receivers:
            destinatario = self.createDestinatarioFromSenderReceiver(receiver)
            destinazione.append(destinatario)

        return destinazione

    def createPerConoscenza(self):
        destinazione = etree.Element("Destinazione")
        return destinazione

    def createDestinatarioIN(self):
        destinatario = etree.Element("Destinatario")
        amministrazione = self.createAmministrazioneFromCompany(self.company)
        destinatario.append(amministrazione)

        return destinatario

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
            # privato = self.createPrivatoFromSenderReceiver(senderReceiver)
            # destinatario.append(privato)
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

    def createOrigine(self, senderReceiver):
        origine = etree.Element("Origine")
        indirizzoTelematico = self.createIndirizzoTelematicoFromSenderReceiver(
            senderReceiver)
        mittente = self.createMittenteIN()
        origine.append(indirizzoTelematico)
        origine.append(mittente)
        return origine

    def createOrigineIN(self):
        origine = etree.Element("Origine")
        indirizzoTelematico = self.createIndirizzoTelematico("")
        origine.append(indirizzoTelematico)

        mittente = self.createMittenteIN()
        origine.append(mittente)
        return origine

    def createOrigineOUT(self):
        origine = etree.Element("Origine")
        indirizzoTelematico = self.createIndirizzoTelematico("")
        origine.append(indirizzoTelematico)

        mittente = self.createMittenteOUT()
        origine.append(mittente)

        return origine

    def createIndirizzoTelematicoFromSenderReceiver(self, senderReceiver):
        indirizzoTelematico = etree.Element("IndirizzoTelematico")
        indirizzoTelematicoVal = ""
        if senderReceiver.pec_mail:
            indirizzoTelematicoVal = senderReceiver.pec_mail
        elif senderReceiver.email:
            indirizzoTelematicoVal = senderReceiver.email

        indirizzoTelematico.text = indirizzoTelematicoVal
        return indirizzoTelematico

    def createIndirizzoTelematicoFromCompany(self, company):
        indirizzoTelematico = etree.Element("IndirizzoTelematico")
        indirizzoTelematicoVal = ""
        if company.email:
            indirizzoTelematicoVal = company.email

        indirizzoTelematico.text = indirizzoTelematicoVal
        return indirizzoTelematico

    def createIndirizzoTelematico(self, addressVal):
        indirizzoTelematico = etree.Element("IndirizzoTelematico")
        indirizzoTelematicoVal = ""
        if addressVal:
            indirizzoTelematicoVal = addressVal

        indirizzoTelematico.text = indirizzoTelematicoVal
        return indirizzoTelematico

    def createMittente(self, senderReceiver):
        mittente = etree.Element("Mittente")
        # TODO creare una discriminante per le pubbliche amministrazioni
        privato = self.createPrivatoFromSenderReceiver(senderReceiver)
        mittente.append(privato)

        return mittente

    def createMittenteIN(self):
        mittente = etree.Element("Mittente")

        senders = self.protocollo.sender_receivers
        for sender in senders:
            if sender.type == "individual":  # Persona fisica
                persona = self.createAmministrazioneFakeFromSenderReceiver(
                    sender)
                mittente.append(persona)
            elif sender.type == "legal":  # Azienda privata
                azienda = self.createAmministrazioneFakeFromSenderReceiver(
                    sender)
                mittente.append(azienda)
            elif sender.type == "government":  # Amministrazione pubblica
                privato = self.createAmministrazioneFromSenderReceiver(sender)
                mittente.append(privato)
            break

        aOO = self.createAOO()
        mittente.append(aOO)
        return mittente

    def createMittenteOUT(self):
        mittente = etree.Element("Mittente")

        # TODO creare una discriminante per le pubbliche amministrazioni
        amministrazione = self.createAmministrazioneOUT()
        mittente.append(amministrazione)
        aOO = self.createAOO()
        mittente.append(aOO)

        return mittente

    def createPersonaFromSenderReceiver(self, senderReceiver):
        persona = etree.Element("Persona")
        denominazione = self.createDenominazione(senderReceiver.name)
        persona.append(denominazione)
        return persona

    def createPrivatoFromSenderReceiver(self, senderReceiver):
        privato = etree.Element("Privato")

        identificativo = self.createIdentificativo()
        privato.append(identificativo)

        if senderReceiver.type == "legal":
            privato.attrib["tipo"] = "impresa"
            denominazioneImpresa = self.createDenominazioneImpresa(
                senderReceiver.name)
            privato.append(denominazioneImpresa)
            partitaIva = etree.Element("PartitaIva")
            privato.append(partitaIva)
            nome = self.createNome()
            privato.append(nome)
        elif senderReceiver.type == "individual":
            privato.attrib["tipo"] = "cittadino"
            denominazioneImpresa = self.createDenominazioneImpresa()
            privato.append(denominazioneImpresa)
            partitaIva = etree.Element("PartitaIva")
            privato.append(partitaIva)
            nome = self.createNome(senderReceiver.name)
            privato.append(nome)

        cognome = etree.Element("Cognome")
        privato.append(cognome)
        codiceFiscale = etree.Element("CodiceFiscale")
        privato.append(codiceFiscale)
        indirizzoTelematico = self.createIndirizzoTelematicoFromSenderReceiver(
            senderReceiver)
        privato.append(indirizzoTelematico)
        indirizzoPostale = self.createIndirizzoPostaleFromSenderReceiver(
            senderReceiver)
        privato.append(indirizzoPostale)
        telefono = self.createTelefono(senderReceiver)
        privato.append(telefono)

        return privato

    def createPrivatoFromCompany(self, company):
        privato = etree.Element("Privato")
        if company.type == "legal":
            privato.attrib["tipo"] = "impresa"
            denominazioneImpresa = self.createDenominazioneImpresa(company)
            privato.append(denominazioneImpresa)
            partitaIva = etree.Element("PartitaIva")
            privato.append(partitaIva)
        elif company.type == "individual":
            privato.attrib["tipo"] = "cittadino"
            nome = self.createNome(company)
            privato.append(nome)

        identificativo = self.createIdentificativo()
        indirizzoTelematico = self.createIndirizzoTelematicoFromSenderReceiver(
            company)
        indirizzoPostale = self.createIndirizzoPostale(company)
        telefono = self.createTelefono(company)

        privato.append(identificativo)
        privato.append(indirizzoTelematico)
        privato.append(indirizzoPostale)
        privato.append(telefono)
        return privato

    def createTelefono(self, senderReceiver):
        telefono = etree.Element("Telefono")
        telefonoValue = ""
        if hasattr(senderReceiver, "mobile") and senderReceiver.mobile:
            telefonoValue = senderReceiver.mobile
        elif senderReceiver.phone:
            telefonoValue = senderReceiver.phone

        telefono.text = self.checkNullValue(telefonoValue)
        return telefono

    def createNome(self, name=''):
        nome = etree.Element("Nome")
        nome.text = self.checkNullValue(name)
        return nome

    def createDenominazioneImpresa(self, name=''):
        denominazioneImpresa = etree.Element("DenominazioneImpresa")
        denominazioneImpresa.text = self.checkNullValue(name)
        return denominazioneImpresa

    def createIdentificativo(self):
        return etree.Element("Identificativo")

    def createAOO(self):
        aOO = etree.Element("AOO")
        denominazione = self.createDenominazione(self.denominazioneAOO)
        codiceAOO = self.createCodiceAOO(self.codiceAOO)

        aOO.append(denominazione)
        aOO.append(codiceAOO)
        return aOO

    def createAOOFromDepartment(self, department):
        aOO = etree.Element("AOO")
        denominazione = self.createDenominazione()
        denominazioneVal = ""
        if hasattr(department, "name") and department.name:
            denominazioneVal = department.name
        denominazione.text = denominazioneVal
        codiceAOO = self.createCodiceAOO()

        aOO.append(denominazione)
        aOO.append(codiceAOO)
        return aOO

    def createDenominazione(self, denominazioneVal=""):
        denominazione = etree.Element("Denominazione")
        denominazione.text = denominazioneVal
        return denominazione

    def createAmministrazioneOUT(self):
        amministrazione = etree.Element("Amministrazione")
        denominazione = self.createDenominazione(self.company.name)
        # TODO Recuperare da qualche parte il codice amministrazione (codice
        #  IPA??)
        codiceAmministrazione = self.createCodiceAmministrazione()
        unitaOrganizzativa = self.createUnitaOrganizzativaFromDepartment(self.ufficioProtocollatore, self.accountPecProtocollo)

        amministrazione.append(denominazione)
        amministrazione.append(codiceAmministrazione)
        amministrazione.append(unitaOrganizzativa)
        return amministrazione

    def createAmministrazioneFromCompany(self, company):
        amministrazione = etree.Element("Amministrazione")
        denominazione = self.createDenominazione(company.name)
        amministrazione.append(denominazione)
        codiceAmministrazione = self.createCodiceAmministrazione(
            company.ammi_code)
        amministrazione.append(codiceAmministrazione)

        unitaOrganizzativa = self.createUnitaOrganizzativaFromCompany(company)
        amministrazione.append(unitaOrganizzativa)

        return amministrazione

    def createAmministrazioneFromSenderReceiver(self, senderReceiver):
        amministrazione = etree.Element("Amministrazione")
        denominazione = self.createDenominazione(senderReceiver.name)
        amministrazione.append(denominazione)

        # TODO Recuperare da qualche parte il codice amministrazione (codice
        #  IPA??)
        ammi_code = self.checkNullValue(senderReceiver.ammi_code)
        codiceAmministrazione = self.createCodiceAmministrazione(ammi_code)
        amministrazione.append(codiceAmministrazione)

        unitaOrganizzativa = self.createUnitaOrganizzativaFromSenderReceiver(
            senderReceiver)
        amministrazione.append(unitaOrganizzativa)

        return amministrazione

    # Finta amministrazione con i dati del privato per rispettare il DTD
    def createAmministrazioneFakeFromSenderReceiver(self, senderReceiver):
        amministrazione = etree.Element("Amministrazione")
        denominazione = self.createDenominazione(
            senderReceiver.name + " (PRIVATO)")
        amministrazione.append(denominazione)

        if senderReceiver.type == 'individual':
            persona = self.createPersonaFromSenderReceiver(senderReceiver)
            amministrazione.append(persona)

        indirizzoPostale = self.createIndirizzoPostaleFromSenderReceiver(
            senderReceiver)
        amministrazione.append(indirizzoPostale)
        indirizzoTelematico = self.createIndirizzoTelematicoFromSenderReceiver(
            senderReceiver)
        amministrazione.append(indirizzoTelematico)
        return amministrazione

    def createUnitaOrganizzativaFromSenderReceiver(self, senderReceiver):
        unitaOrganizzativa = etree.Element("UnitaOrganizzativa",
                                           tipo="permanente")
        denominazione = self.createDenominazione(senderReceiver.name)
        # identificativo = self.createIdentificativo()
        indirizzoPostale = self.createIndirizzoPostaleFromSenderReceiver(
            senderReceiver)
        indirizzoTelematico = self.createIndirizzoTelematicoFromSenderReceiver(
            senderReceiver)
        telefono = self.createTelefono(senderReceiver)
        fax = etree.Element("Fax")

        unitaOrganizzativa.append(denominazione)
        # unitaOrganizzativa.append(identificativo)
        unitaOrganizzativa.append(indirizzoPostale)
        unitaOrganizzativa.append(indirizzoTelematico)
        unitaOrganizzativa.append(telefono)
        unitaOrganizzativa.append(fax)
        return unitaOrganizzativa

    def createUnitaOrganizzativaFromDepartment(self, department, accountPec):
        unitaOrganizzativa = etree.Element("UnitaOrganizzativa",
                                           tipo="permanente")

        if department is not None:
            denominazione = self.createDenominazione(department)
            indirizzoPostale = self.createIndirizzoPostaleFromDepartment(self.company)
            indirizzoTelematico = self.createIndirizzoTelematico(accountPec)
            unitaOrganizzativa.append(denominazione)
            unitaOrganizzativa.append(indirizzoPostale)
            unitaOrganizzativa.append(indirizzoTelematico)
        else:
            return self.createUnitaOrganizzativaFromCompany(self.company, "")

        return unitaOrganizzativa

    def createUnitaOrganizzativaFromCompany(self, company, name=""):
        unitaOrganizzativa = etree.Element("UnitaOrganizzativa",
                                           tipo="permanente")
        if name == "":
            denominazione = self.createDenominazione(company.name)
        else:
            denominazione = self.createDenominazione(name)

        indirizzoPostale = self.createIndirizzoPostaleFromCompany(company)
        indirizzoTelematico = self.createIndirizzoTelematicoFromCompany(company)
        telefono = self.createTelefono(company)
        fax = etree.Element("Fax")

        unitaOrganizzativa.append(denominazione)
        unitaOrganizzativa.append(indirizzoPostale)
        unitaOrganizzativa.append(indirizzoTelematico)
        unitaOrganizzativa.append(telefono)
        unitaOrganizzativa.append(fax)
        return unitaOrganizzativa

    def createIndirizzoPostaleFromSenderReceiver(self, senderReceiver):
        indirizzoPostale = etree.Element("IndirizzoPostale")
        toponimo = etree.Element("Toponimo")
        toponimo.text = self.checkNullValue(senderReceiver.street)
        # TODO estrarre il civico dall'indirizzo
        civico = etree.Element("Civico")
        cap = self.createCap(senderReceiver.zip)
        comune = self.createComune(senderReceiver.city)

        # TODO recuperare la provincia da qualche parte o modellarla
        provincia = etree.Element("Provincia")
        nazione = self.createNazione(senderReceiver.country_id)

        indirizzoPostale.append(toponimo)
        indirizzoPostale.append(civico)
        indirizzoPostale.append(cap)
        indirizzoPostale.append(comune)
        indirizzoPostale.append(provincia)
        indirizzoPostale.append(nazione)
        return indirizzoPostale

    def createIndirizzoPostaleFromDepartment(self, company):
        indirizzoPostale = etree.Element("IndirizzoPostale")
        toponimo = etree.Element("Toponimo")
        # toponimo.text = self.checkNullValue(company.street)
        # # TODO inserire anagrafica anche per gli Uffici
        civico = etree.Element("Civico")
        cap = self.createCap("")
        comune = self.createComune("")
        #
        # # TODO recuperare la provincia da qualche parte o modellarla
        provincia = etree.Element("Provincia")
        nazione = self.createNazione(company.country_id)

        indirizzoPostale.append(toponimo)
        indirizzoPostale.append(civico)
        indirizzoPostale.append(cap)
        indirizzoPostale.append(comune)
        indirizzoPostale.append(provincia)
        indirizzoPostale.append(nazione)
        return indirizzoPostale

    def createIndirizzoPostaleFromCompany(self, company):
        indirizzoPostale = etree.Element("IndirizzoPostale")
        toponimo = etree.Element("Toponimo")
        toponimo.text = self.checkNullValue(company.street)
        # TODO estrarre il civico dall'indirizzo
        civico = etree.Element("Civico")
        cap = self.createCap(company.zip)
        comune = self.createComune(company.city)

        # TODO recuperare la provincia da qualche parte o modellarla
        provincia = etree.Element("Provincia")
        nazione = self.createNazione(company.country_id)

        indirizzoPostale.append(toponimo)
        indirizzoPostale.append(civico)
        indirizzoPostale.append(cap)
        indirizzoPostale.append(comune)
        indirizzoPostale.append(provincia)
        indirizzoPostale.append(nazione)
        return indirizzoPostale

    def createComune(self, comuneVal):
        comune = etree.Element("Comune")
        comuneValue = ""
        if comuneVal:
            comuneValue = comuneVal
        comune.text = comuneValue
        return comune

    def createNazione(self, nazioneObj):
        nazione = etree.Element("Nazione")
        nazioneValue = ""
        if nazioneObj and nazioneObj.name:
            nazioneValue = nazioneObj.name
        nazione.text = nazioneValue
        return nazione

    def createCap(self, capVal):
        cap = etree.Element("CAP")
        cap.text = self.checkNullValue(capVal)
        return cap

    def checkNullValue(self, value):
        tempValue = ""
        if value:
            tempValue = value
        return tempValue
