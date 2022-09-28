import xmltodict
import base64
from odoo import models, _, api
from odoo.exceptions import ValidationError
from datetime import datetime
from lxml import etree, objectify
import pandas as pd
import logging
import inspect
import os
from xml.dom import minidom
from signxml import XMLSigner
import hashlib

_logger = logging.getLogger(__name__)


class ProtocolloSegnaturaXml(models.Model):
    _inherit = "sd.protocollo.protocollo"

    # metodo usato per costruire la segnatura xml partendo dall'istanza del protocollo
    def get_segnatura_xml(self, mail_list=False):
        doc = minidom.Document()
        element = doc.createElementNS('', 'SegnaturaInformatica')
        element.setAttribute("xmlns", "http://www.agid.gov.it/protocollo/")
        element.setAttribute("xmlns:ds", "http://www.agid.gov.it/protocollo/")
        element.setAttribute("xsi:schemaLocation", "http://www.agid.gov.it/protocollo/ schema.xsd")
        element.setAttribute("p3:versione", "3.0.0")
        element.setAttribute("p3:lang", "it")
        element.setAttribute("xmlns:p3", "http://www.agid.gov.it/protocollo/")
        element.setAttribute("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        doc.appendChild(element)
        root_xml = objectify.fromstring(doc.toprettyxml())
        intestazione_xml = self._get_intestazione()
        descrizione_xml = self._get_descrizione(mail_list)
        root_xml.extend([intestazione_xml, descrizione_xml])
        #firmata con un certificato fake, giusto per baipassare il validator xml in attesa dei servizi aruba
        signed_xml = self._get_signature(root_xml)
        is_valid = self._validate_xml(etree.tostring(signed_xml))
        if is_valid:
            return etree.tostring(signed_xml, pretty_print=True)
        else:
            raise ValidationError(_("Errore nella validazione del file segnatura.xml"))

    # metodo usato per fare il parsing del content del file segnatura.xml proveniente da una fonte esterna (PEC)
    @api.model
    def parse_content_xml(self, content, file):
        try:
            return xmltodict.parse(content)
        except Exception as e:
            _logger.error("Errore nel parsing del file %s: %s" % (file, str(e)))
            return {}

    def _validate_2001_xml(self, root):
        directory_path = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        full_path = os.path.join(directory_path, '../static/dtd/segnatura.dtd')
        dtdfile = open(full_path, 'r')
        dtd = etree.DTD(dtdfile)
        is_valid = dtd.validate(root)
        if not is_valid:
            print(dtd.error_log.filter_from_errors())
        return is_valid

    def _validate_xml(self, root, path="../static/xsd/pec_message.xsd"):
        directory_path = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        full_path = os.path.join(directory_path, path)
        xml_validator = etree.XMLSchema(file=full_path)
        try:
            xml_file = etree.fromstring(root)
        except:
            return _("Unable to read xml segnatura")
        is_valid = xml_validator.validate(xml_file)
        if not is_valid:
            print(xml_validator.error_log.filter_from_errors())
        return is_valid

    def _get_descrizione(self, mail_list):
        descrizione_xml = etree.Element("Descrizione")
        if self.tipologia_protocollo == "ingresso":
            #non genero la segnatura in ingresso
            #descrizione_xml.extend(self._get_descrizione_ingresso())
            return
        elif self.tipologia_protocollo == "uscita":
            descrizione_xml.extend(self._get_descrizione_uscita(mail_list))
        allegato_ids = self.allegato_ids
        documento = self.documento_id
        if documento:
            documento = self._get_documento_from_sd_dms_document(documento)
            descrizione_xml.append(documento)
        # verifico la presenza di allegati, se presenti verifico che esista più di un allegato o l'unico allegato non
        # sia la segnatura_xml
        if len(allegato_ids) > 1 or (len(allegato_ids) == 1 and not allegato_ids[0].protocollo_segnatura_xml):
            allegati_xml = self._get_allegati(allegato_ids)
            for allegato in allegati_xml:
                descrizione_xml.append(allegato)

        return descrizione_xml

    def _get_documento_from_sd_dms_document(self, document, allegato=False):
        doc = minidom.Document()
        if allegato:
            element = doc.createElementNS('', 'Allegato')
        else:
            element = doc.createElementNS('', 'DocumentoPrimario')
        element.setAttribute("xmlns:p6", "http://www.agid.gov.it/protocollo/")
        element.setAttribute("p6:nomeFile", document.filename)
        element.setAttribute("p6:mimeType", document.mimetype)
        doc.appendChild(element)
        documento_xml = objectify.fromstring(doc.toprettyxml())
        documento_xml.set("xmlns", "http://www.agid.gov.it/protocollo/")
        impronta_xml = etree.Element("Impronta")
        impronta_xml.text = document.checksum
        documento_xml.extend([impronta_xml])
        return documento_xml

    def _get_allegati(self, allegato_ids):
        allegati = []
        for allegato in allegato_ids:
            if not allegato.protocollo_segnatura_xml:
                documento = self._get_documento_from_sd_dms_document(allegato, True)
                allegati.append(documento)
        return allegati

    def _get_fascicolo(self):
        fascicolo_xml = etree.Element("Fascicolo")
        denominazione_fascicolo = self._get_denominazione_fascicolo()
        codice_fascicolo = self._get_codice_fascicolo()
        fascicolo_xml.extend([denominazione_fascicolo, codice_fascicolo])
        return fascicolo_xml

    def _get_denominazione_fascicolo(self):
        denominazione_xml = etree.Element("Denominazione")
        denominazione_xml.text = self.fascicolo_ids.nome
        return denominazione_xml

    def _get_codice_fascicolo(self):
        codice_xml = etree.Element("CodiceFascicolo")
        codice_xml.text = str(self.fascicolo_ids.codice_sequenza)
        return codice_xml

    def _get_classifica(self):
        classifica_xml = etree.Element("Classifica")
        voce_titolario_name = self._get_voce_titolario_name()
        codice_flat = self._get_codice_flat()
        classifica_xml.extend([voce_titolario_name, codice_flat])
        return classifica_xml

    # ----------------------------------------------------------
    # #Oggetto: Recupero Oggetto Protocollo
    # ----------------------------------------------------------
    def _get_voce_titolario_name(self):
        voce_titolario_name_xml = etree.Element("Denominazione")
        voce_titolario_name = self.documento_id.voce_titolario_id.name
        voce_titolario_name_xml.text = voce_titolario_name if voce_titolario_name else " "
        return voce_titolario_name_xml

    def _get_codice_flat(self):
        codice_flat_xml = etree.Element("CodiceFlat")
        codice_flat_xml.text = self.documento_id.voce_titolario_id.path_name
        return codice_flat_xml

    def _get_oggetto(self):
        oggetto_xml = etree.Element("Oggetto")
        oggetto_documento_id = self.documento_id.subject
        oggetto_xml.text = oggetto_documento_id if oggetto_documento_id else ""
        return oggetto_xml

    # -----------------------------------------------------------------
    # #Signature: Recupero signature XAdES baseline B level signatures
    # -----------------------------------------------------------------

    def _get_signature(self, root_xml):
        directory_path = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        cert = os.path.join(directory_path, '../static/pem/cert.pem')
        key = os.path.join(directory_path, '../static/pem/key.pem')
        cert, key = [open(f, "rb").read() for f in (cert, key)]
        root_xml_signed = XMLSigner().sign(root_xml, key=key, cert=cert)
        return root_xml_signed

    # ----------------------------------------------------------
    # #Intestazione: Recupero Intestazione Protocollo
    # ----------------------------------------------------------
    def _get_intestazione(self):
        intestazione_xml = etree.Element("Intestazione")
        intestazione_xml.append(self._get_identificatore())
        intestazione_xml.append(self._get_oggetto())
        intestazione_xml.append(self._get_classifica())
        if self.fascicolo_ids:
            intestazione_xml.append(self._get_fascicolo())
        return intestazione_xml

    """def _get_descrizione_ingresso(self):
        origine = self._get_origine_ingresso()
        destinazione = self._get_destinazione_ingresso()
        return [origine, destinazione]"""

    def _get_descrizione_uscita(self, mail_list):
        descrizione_uscita_xml = []
        origine = self._get_origine_uscita(mail_list)
        descrizione_uscita_xml.append(origine)
        for destinatario in self._get_destinazione_uscita():
            descrizione_uscita_xml.append(destinatario)
        return descrizione_uscita_xml

    # ----------------------------------------------------------
    # #Origine: Recupero origine Protocollo
    # ----------------------------------------------------------

    """def _get_origine_ingresso(self):
        mittente_xml = self._get_mittente_from_sd_protocollo_contatto(self.mittente_ids)
        return mittente_xml"""

    def _get_origine_uscita(self, mail_list):
        mittente_xml = self._get_mittente_uscita(mail_list)
        return mittente_xml

    # ----------------------------------------------------------
    # #Destinazione: Recupero destinazione Protocollo
    # ----------------------------------------------------------

    """def _get_destinazione_ingresso(self):
        destinatario_xml = self._get_destinatario()
        amministrazione = self._get_amministrazione_ingresso()
        destinatario_xml.append(amministrazione)
        return destinatario_xml"""

    def _get_destinazione_uscita(self):
        destinatari = []
        generate = False
        for destinatario_id in self.destinatario_ids:
            destinatari.append(self._get_destinatario_from_sd_protocollo_contatto(destinatario_id))
            if destinatario_id.is_aoo or destinatario_id.is_uo or destinatario_id.is_pa or destinatario_id.is_gps:
               generate = True
        if generate:
            return destinatari
        else:
            return
    # ----------------------------------------------------------
    # #Destinatario: Recupero destinatario Protocollo
    # ----------------------------------------------------------
    def _get_destinatario(self):
        destinatario_xml = etree.Element("Destinatario")
        return destinatario_xml

    def _get_destinatario_from_sd_protocollo_contatto(self, contatto_id):
        destinatario_xml = self._get_destinatario()
        if contatto_id.company_type == "person":
            persona = self._get_persona_from_contatto(contatto_id)
            if persona:
                destinatario_xml.append(persona)
        elif contatto_id.is_private_company:
            persona_giuridica = self._get_persona_giuridica_from_contatto(contatto_id)
            if persona_giuridica:
                destinatario_xml.append(persona_giuridica)
        else:
            amministrazione = self._get_amministrazione_from_contatto(
                contatto_id)
            destinatario_xml.append(amministrazione)

        return destinatario_xml

    # ----------------------------------------------------------
    # #Mittente: Recupero mittente Protocollo
    # ----------------------------------------------------------
    def _get_mittente(self):
        mittente_xml = etree.Element("Mittente")
        return mittente_xml

    def _get_mittente_from_sd_protocollo_contatto(self, contatto_id):
        mittente_xml = self._get_mittente()

        if contatto_id.company_type == "person":  # Persona fisica
            persona = self._get_persona_from_contatto(contatto_id)
            if persona:
                mittente_xml.append(persona)
        else:  # Amministrazione pubblica
            amministrazione = self._get_amministrazione_from_contatto(
                contatto_id)
            mittente_xml.append(amministrazione)

        return mittente_xml

    def _get_mittente_uscita(self, mail_list):
        mittente = etree.Element("Mittente")
        amministrazione = self._get_amministrazione_uscita(mail_list)
        mittente.append(amministrazione)
        return mittente

    # ----------------------------------------------------------
    # #IndirizzoTelematico: Recupero indirizzo telematico Protocollo
    # ----------------------------------------------------------

    def _get_indirizzo_telematico(self, element):
        l_mail = []

        if element.email == False and element.pec_mail == False:
            return False
        if element.email:
            indirizzo_mail_xml = etree.Element("IndirizzoTelematico")
            indirizzo_mail_xml.text = element.email
            l_mail.append(indirizzo_mail_xml)
        if element.pec_mail:
            indirizzo_pec_xml = etree.Element("IndirizzoTelematico")
            indirizzo_pec_xml.text = element.pec_mail
            l_mail.append(indirizzo_pec_xml)
        return l_mail

    # ----------------------------------------------------------
    # #DomicilioDigitale: Recupero domicilio digitale
    # ----------------------------------------------------------

    def _get_domicilio_digitale(self, element):
        l_pec = []
        for domicilio in element.digital_domicile_ids:
            indirizzo_telematico_xml = etree.Element("IndirizzoTelematico")
            indirizzo_telematico_xml.text = domicilio.email_address
            l_pec.append(indirizzo_telematico_xml)
        return l_pec

    # ----------------------------------------------------------
    # #Amministrazione: Recupero amministrazione Protocollo
    # ----------------------------------------------------------
    def _get_amministrazione_uscita(self, mail_list):
        amministrazione_xml = etree.Element("Amministrazione")
        denominazione = self._get_denominazione(self.aoo_id.company_id.name)
        l_amministrazione = [denominazione]
        if self.aoo_id.company_id.partner_id.fiscalcode:
            cf_amministrazione = self._get_cf_amministrazione(self.aoo_id.company_id.partner_id.fiscalcode)
            l_amministrazione.append(cf_amministrazione)
        codice_amministrazione = self._get_codice_ipa(self.aoo_id.company_id.codice_ipa, True)
        l_amministrazione.append(codice_amministrazione)
        contatti_amministrazione = self._get_contatti(self.company_id.partner_id, "amministrazione")
        if contatti_amministrazione:
            l_amministrazione.append(contatti_amministrazione)
        codica_ipa_aoo = self._get_codice_aoo(self.aoo_id.cod_aoo, True)
        l_amministrazione.append(codica_ipa_aoo)
        contatti_aoo = self._get_contatti_from_fl_set(self.aoo_id,"aoo")
        if contatti_aoo:
            l_amministrazione.append(contatti_aoo)
        if self.mittente_interno_id.ufficio_id.cod_ou:
            codice_ipa_uo = self._get_codice_ipa_uo(self.mittente_interno_id.ufficio_id.cod_ou)
            l_amministrazione.append(codice_ipa_uo)
        elif self.mittente_interno_id.parent_id.ufficio_id.cod_ou:
            codice_ipa_uo = self._get_codice_ipa_uo(self.mittente_interno_id.parent_id.ufficio_id.cod_ou)
            l_amministrazione.append(codice_ipa_uo)
        contatti_uo = self._get_contatti_from_fl_set(self.mittente_interno_id.parent_id.ufficio_id, "uo")
        if contatti_uo:
            l_amministrazione.append(contatti_uo)
        persona_fisica = self._get_persona_from_contatto(self.mittente_interno_id.utente_id.partner_id)
        if persona_fisica:
            l_amministrazione.append(persona_fisica)
        amministrazione_xml.extend(l_amministrazione)
        return amministrazione_xml

    """def _get_amministrazione_ingresso(self):
        amministrazione_xml = etree.Element("Amministrazione")
        denominazione = self._get_denominazione(self.aoo_id.company_id.name)
        #da riscrivere
        cf_amministrazione = self._get_cf_amministrazione(
            self.aoo_id.company_id.partner_id.fiscalcode if self.aoo_id.company_id.partner_id.fiscalcode else False)
        codice_amministrazione = self._get_codice_ipa(self.aoo_id.company_id.codice_ipa, True)
        contatti_amministrazione = self._get_contatti(self.aoo_id.company_id, "amministrazione")
        codica_ipa_aoo = self._get_codice_aoo(self.aoo_id.cod_aoo, True)
        contatti_aoo = self._get_contatti(self.aoo_id, "aoo")
        codice_ipa_uo = self._get_codice_ipa_uo(self.mittente_interno_id.ufficio_id.cod_ou)
        persona_fisica = self._get_persona_from_contatto(self.mittente_interno_id.utente_id)
        xml_list = [denominazione, codice_amministrazione,
                    contatti_amministrazione, codica_ipa_aoo, contatti_aoo, codice_ipa_uo]
        if cf_amministrazione != False:
            xml_list.append(cf_amministrazione)
        if persona_fisica:
            xml_list.append(persona_fisica)

        amministrazione_xml.extend(xml_list)

        return amministrazione_xml"""

    def _get_codice_ipa_uo(self, codice):
        codice_ipa_uo_xml = etree.Element("CodiceIPAUO")
        codice_ipa_uo_xml.text = codice
        return codice_ipa_uo_xml

    def _get_contatti_from_fl_set(self, element, type=""):
        if type == "aoo":
            contatti = etree.Element("ContattiAOO")
        else:
            contatti = etree.Element("ContattiUO")
        indirizzo_postale = self._get_indirizzo_postale(element)
        if indirizzo_postale != False:
            contatti.extend([indirizzo_postale])
        else:
            return False
        return contatti



    def _get_contatti(self, element, type="", domicilio_digitale=False):
        domicilio = []
        l_xml = []
        if type == "aoo":
            contatti = etree.Element("ContattiAOO")
            domicilio = self._get_domicilio_digitale(element)
        elif type == "amministrazione":
            contatti = etree.Element("ContattiAmministrazione")
            if domicilio_digitale!=False:
                domicilio = self._get_domicilio_digitale(domicilio_digitale)
        elif type == "uo":
            contatti = etree.Element("ContattiUO")
        elif type == "personagiuridica":
            contatti = etree.Element("ContattiPersonaGiuridica")
        else:
            contatti = etree.Element("Contatti")

        indirizzo_postale = self._get_indirizzo_postale(element)
        indirizzo_telematico = self._get_indirizzo_telematico(element)
        telefono = self._get_telefono(element)

        if indirizzo_postale == False and indirizzo_telematico == False and telefono == False and  len(domicilio) == 0:
            return False
        if indirizzo_postale != False:
            l_xml.append(indirizzo_postale)
        if len(domicilio)>0:
            for i in domicilio:
                l_xml.append(i)
        if indirizzo_telematico != False:
            for i in indirizzo_telematico:
                l_xml.append(i)
        if telefono != False:
            l_xml.append(telefono)
        contatti.extend(l_xml)
        return contatti


    def _get_cf_amministrazione(self, cf):
        cf_amministrazione = etree.Element("CFAmministrazione")
        cf_amministrazione.text = cf
        return cf_amministrazione

    def _get_amministrazione_from_contatto(self, contatto):
        amministrazione_xml = etree.Element("Amministrazione")
        denominazione = self._get_denominazione(contatto.name_amm)
        xml_list = [denominazione]
        if contatto.fiscalcode:
            cf_amministrazione = self._get_cf_amministrazione(contatto.fiscalcode)
            xml_list.append(cf_amministrazione)
        if contatto.cod_amm:
            codice_amministrazione = self._get_codice_ipa(contatto.cod_amm, True)
            xml_list.append(codice_amministrazione)
        # add pa contact
        if contatto.is_pa or contatto.is_gps:
            if contatto.is_uo or contatto.is_aoo:
                partner_pa = contatto.partner_id.aoo_id.amministrazione_id
            else:
                partner_pa = contatto
            contatti_pa = self._get_contatti(partner_pa, "amministrazione", contatto)
            if contatti_pa != False:
                xml_list.append(contatti_pa)
        if contatto.cod_aoo:
            codica_ipa_aoo = self._get_codice_aoo(contatto.cod_aoo, True)
            xml_list.append(codica_ipa_aoo)
        if contatto.partner_id:
            contatti_aoo = self._get_contatti(contatto, "aoo")
            if contatti_aoo != False:
                xml_list.append(contatti_aoo)
        #add uo contact
        if contatto.is_uo:
            codice_uo = self._get_codice_ipa_uo(contatto.cod_ou)
            contatti_uo = self._get_contatti(contatto.partner_id, "uo")
            xml_list.append(codice_uo)
            if contatti_uo!= False:
                xml_list.append(contatti_uo)
        amministrazione_xml.extend(xml_list)
        return amministrazione_xml

    # ----------------------------------------------------------
    # #Utility: utility Protocollo
    # ----------------------------------------------------------
    def _get_identificatore(self):
        identificatore_xml = etree.Element("Identificatore")
        codice_amministrazione = self._get_codice_ipa(self.aoo_id.company_id.codice_ipa)
        codice_aoo = self._get_codice_aoo(self.aoo_id.cod_aoo)
        codice_registro = self._get_codice_registro(self.registro_id.codice)
        numero_registrazione = self._get_numero_registrazione(self.numero_protocollo)
        data_registrazione = self._get_data_registrazione(self.data_registrazione)
        identificatore_xml.extend(
            [codice_amministrazione, codice_aoo, codice_registro, numero_registrazione, data_registrazione])
        return identificatore_xml

    def _get_data_registrazione(self, data_registrazione):
        data_registrazione_xml = etree.Element("DataRegistrazione")
        data_registrazione_xml.text = data_registrazione.date().isoformat()  # TODO isoformat????
        return data_registrazione_xml

    def _get_numero_registrazione(self, numero_registrazione):
        numero_registrazione_xml = etree.Element("NumeroRegistrazione")
        numero_registrazione_xml.text = numero_registrazione if numero_registrazione else ""
        return numero_registrazione_xml

    def _get_codice_registro(self, codice_registro):
        codice_registro_xml = etree.Element("CodiceRegistro")
        codice_registro_xml.text = codice_registro if codice_registro else ""
        return codice_registro_xml

    def _get_codice_aoo(self, val_codice_aoo="", from_descrizione=False):
        if from_descrizione:
            codice_aoo_xml = etree.Element("CodiceIPAAOO")
        else:
            codice_aoo_xml = etree.Element("CodiceAOO")
        codice_aoo_xml.text = val_codice_aoo if val_codice_aoo else " "
        return codice_aoo_xml

    def _get_codice_ipa(self, code="", per_descrizione=False):
        if per_descrizione:
            codice_amministrazione_xml = etree.Element("CodiceIPAAmministrazione")
            codice_amministrazione_xml.text = code if code else " "
        else:
            codice_amministrazione_xml = etree.Element("CodiceAmministrazione")
            codice_amministrazione_xml.text = code if code else " "
        return codice_amministrazione_xml

    def _get_persona_from_contatto(self, contatto):
        persona_xml = etree.Element("PersonaFisica")
        if contatto.name:
            nome, cognome = self._get_nome_cognome(contatto.name, contatto.name)
        else:
            return False
        l_xml = [nome, cognome]
        if contatto.fiscalcode:
            codice_fiscale = self._get_codice_fiscale(contatto)
            l_xml.append(codice_fiscale)

        contatti = self._get_contatti(contatto, "personafisica")
        if contatti != False:
            l_xml.append(contatti)
        persona_xml.extend(l_xml)
        return persona_xml

    def _get_persona_giuridica_from_contatto(self, contatto):
        persona_xml = etree.Element("PersonaGiuridica")
        if contatto.name:
            denominazione = self._get_denominazione_persona_giuridica(contatto.name)
        else:
            denominazione=""
        xml_list = [denominazione]
        codice_fiscale_piva = self._get_codice_fiscale_piva(contatto)
        contatti = self._get_contatti(contatto, "personagiuridica")
        if codice_fiscale_piva != False:
            xml_list.append(codice_fiscale_piva)
        if contatti!=False:
            xml_list.append(contatti)
        persona_xml.extend(xml_list)
        return persona_xml

    def _get_codice_fiscale_piva(self, contatto):
        codice_fiscale_piva_xml = etree.Element("PIVAoCF")
        if contatto.fiscalcode:
            codice_fiscale_piva_xml.text = contatto.fiscalcode
        elif contatto.vat:
            codice_fiscale_piva_xml.text = contatto.vat
        else:
            return False
        return codice_fiscale_piva_xml

    def _get_codice_fiscale(self, contatto):
        codice_fiscale_xml = etree.Element("CodiceFiscale")
        codice_fiscale_xml.text = contatto.fiscalcode if contatto.fiscalcode else ""
        return codice_fiscale_xml

    def _get_telefono(self, company):
        telefono_xml = etree.Element("Telefono")
        if company.phone:
            telefono_xml.text = company.phone
            return telefono_xml
        else:
            return False

    def _get_denominazione_persona_giuridica(self, denominazione=""):
        denominazione_xml = etree.Element("Denominazione")
        denominazione_xml.text = denominazione
        return denominazione_xml

    def _get_denominazione(self, denominazione=""):
        denominazione_xml = etree.Element("DenominazioneAmministrazione")
        denominazione_xml.text = denominazione
        return denominazione_xml

    def _get_nome_cognome(self, nome, cognome):
        nome_xml = etree.Element("Nome")
        nome_xml.text = nome
        cognome_xml = etree.Element("Cognome")
        cognome_xml.text = cognome
        return nome_xml, cognome_xml

    def _get_indirizzo_postale(self, element):
        indirizzo_postale_xml = etree.Element("IndirizzoPostale")
        toponimo = etree.Element("Toponimo")
        if hasattr(element, "street") and element.street:
            street = element.street
            dug = self._get_dug(street)
            duf = self._get_duf(street)
            toponimo.extend([dug, duf])
        else:
            return False
        civico = etree.Element("Civico")
        civico.text = ""
        cap = self._get_cap(element.zip)
        comune = self._get_comune(element.city)
        nazione = self._get_nazione(element.country_id)
        if element.zip != False and element.city != False and element.country_id != False and cap != False:
            indirizzo_postale_xml.extend([toponimo, civico, cap, comune, nazione])
            return indirizzo_postale_xml
        else:
            return False

    # denominazione urbanistica generica o qualitficatore del toponimo (e.g., via, viale, piazza, ecc.)
    def _get_dug(self, street):
        dug_xml = etree.Element("dug")
        dug_xml.text = street.split(" ")[0]
        return dug_xml

    # duf, denominazione urbanistica ufficiale o nome della strada
    def _get_duf(self, street):
        duf_xml = etree.Element("duf")
        duf_xml.text = street.split(" ")[1]
        return duf_xml

    def _get_comune(self, comune):
        directory_path = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        full_path = os.path.join(directory_path, '../static/csv/Codici-statistici-e-denominazioni-al-30_06_2021.csv')
        df = pd.read_csv(full_path, dtype = str,
                         usecols=['Denominazione (Italiana e straniera)', 'Codice Comune formato alfanumerico'])

        istat_code = df.loc[df['Denominazione (Italiana e straniera)'] == comune.title()]['Codice Comune formato alfanumerico'].to_string(index=False)
        #soluzione temporanea da correggere se si trova un dataframe migliore (la codifica ha eliminato gli zeri iniziali)  TODO
        while len(istat_code) < 6:
            istat_code = "0" + istat_code
        doc = minidom.Document()
        element = doc.createElementNS('', 'Comune')
        element.setAttribute("xmlns:p3", "http://www.agid.gov.it/protocollo/")
        element.setAttribute("p3:CodiceISTAT",  istat_code )
        text = doc.createTextNode(comune)
        element.appendChild(text)
        doc.appendChild(element)
        comune_xml = objectify.fromstring(doc.toprettyxml())
        return comune_xml

    def _get_nazione(self, nazione):
        nazione_xml = etree.Element("Nazione")
        nazione_value = ""
        if nazione and nazione.name:
            nazione_value = nazione.name
        nazione_xml.text = nazione_value
        return nazione_xml

    def _get_cap(self, cap_val):
        cap = etree.Element("CAP")
        if cap_val:
            cap.text = cap_val
        else:
            return False
        return cap
    """
    @api.model
    def parse_segnatura_2001_xml_to_protocollo_data(self, content, email_from):
        data = {}
        try:
            parsed_data = self.parse_content_xml(content, "segnatura.xml")
            origine = self._find_data_in_path(
                parsed_data, "Segnatura/Intestazione/Origine"
            )
            uo = self._find_data_in_path(
                parsed_data, "Segnatura/Intestazione/Origine/Mittente/Amministrazione/UnitaOrganizzativa"
            )
            # mittente_numero_protocollo
            data["mittente_numero_protocollo"] = self._find_data_in_path(
                parsed_data, "Segnatura/Intestazione/Identificatore/NumeroRegistrazione"
            )
            # mittente_registro
            data["mittente_registro"] = self._find_data_in_path(
                parsed_data, "Segnatura/Intestazione/Identificatore/CodiceRegistro"
            )
            # mittente_data_registrazione
            data["mittente_data_registrazione"] = self._find_data_in_path(
                parsed_data, "Segnatura/Intestazione/Identificatore/DataRegistrazione", data_parse="datetime"
            )
            # recupero dati del mittente da inserire come contatto del protocollo
            mittente = {}
            denominazione_amministrazione = self._find_data_in_path(
                parsed_data, "Segnatura/Intestazione/Origine/Mittente/Amministrazione/Denominazione"
            )
            denominazione_aoo = self._find_data_in_path(
                parsed_data, "Segnatura/Intestazione/Origine/Mittente/AOO/Denominazione"
            )
            denominazione_uo = self._find_data_in_path(
                parsed_data,
                "Segnatura/Intestazione/Origine/Mittente/Amministrazione/UnitaOrganizzativa/Denominazione"
            )
            # name
            name = None
            if denominazione_amministrazione:
                name = "AMM %s" % denominazione_amministrazione
                mittente = {"company_subject_type": "pa","company_type": "company","name_amm":name}
            if denominazione_aoo and denominazione_amministrazione != denominazione_aoo:
                name = "%s - AOO %s" % (name, denominazione_aoo)
            if denominazione_uo:
                name = "%s - UO %s" % (name, denominazione_uo)
            mittente["name"] = name
            # cod_amm
            ipa_code = self._find_data_in_path(
                parsed_data, "Segnatura/Intestazione/Origine/Mittente/Amministrazione/CodiceAmministrazione"
            )
            if not ipa_code:
                ipa_code = self._find_data_in_path(
                    parsed_data, "Segnatura/Intestazione/Identificatore/CodiceAmministrazione"
                )

            mittente["cod_amm"] = ipa_code
            # cod_aoo
            aoo_code = self._find_data_in_path(
                parsed_data, "Segnatura/Intestazione/Origine/Mittente/AOO/CodiceAOO"
            )
            if not aoo_code:
                aoo_code = self._find_data_in_path(
                    parsed_data, "Intestazione/Identificatore/CodiceAOO"
                )
            mittente["cod_aoo"] = aoo_code
            l_indirizzi_telematici = [(0, 0, {"pec_mail": email_from, "use_in_sending": True})]
            mittente["domicile_ids"] = l_indirizzi_telematici
            # street
            indirizzo_postale = self._find_data_in_path(uo, "IndirizzoPostale")
            toponimo = self._find_data_in_path(indirizzo_postale, "Toponimo")
            dug = self._find_data_in_path(indirizzo_postale, "Toponimo/@dug")
            civico = self._find_data_in_path(indirizzo_postale, "Civico")
            street = toponimo
            if dug:
                street = "%s %s" % (street, dug)
            if civico:
                street = "%s %s" % (street, civico)
            mittente["street"] = street
            mittente["zip"] = self._find_data_in_path(indirizzo_postale, "CAP")
            mittente["city"] = self._find_data_in_path(indirizzo_postale, "Comune")
            # email
            mittente["email"] = self._find_data_in_path(origine, "IndirizzoTelematico")
            # phone
            mittente["phone"] = self._find_data_in_path(uo, "Telefono")
            # inserimento dei dati del mittente
            data["mittente"] = mittente
        except Exception as e:
            _logger.error("Errore nel parsing del file segnatura.xml: %s" % str(e))
        return data
    """
    # metodo usato per fare il parsing del content del file segnatura.xml proveniente da una fonte esterna (PEC) e
    # successivamente valorizzare un dizionario contenente i vals per creare un protocollo con i dati della segnatura
    @api.model
    def parse_segnatura_xml_to_protocollo_data(self, content,email_from):
        data = {}
        mittente = {}
        mittente_types = ["Amministrazione","PersonaGiuridica","PersonaFisica","AmministrazioneEstera"]
        try:
            fiscalcode =""
            parsed_data = self.parse_content_xml(content, "segnatura.xml")
            for mittente_type in mittente_types:
                if self._find_data_in_path(parsed_data, "SegnaturaInformatica/Descrizione/Mittente/" + mittente_type):
                    if mittente_type == "Amministrazione":
                        contact_data = self._find_data_in_path(
                            parsed_data,
                            "SegnaturaInformatica/Descrizione/Mittente/Amministrazione/ContattiAmministrazione"
                        )
                        name = self._find_data_in_path(
                            parsed_data,
                            "SegnaturaInformatica/Descrizione/Mittente/Amministrazione/DenominazioneAmministrazione"
                        )
                        fiscalcode = self._find_data_in_path(
                            parsed_data,
                            "SegnaturaInformatica/Descrizione/Mittente/Amministrazione/CFAmministrazione"
                        )
                        codiceipauo = self._find_data_in_path(parsed_data,
                            "SegnaturaInformatica/Descrizione/Mittente/Amministrazione/CodiceIPAUO")
                        mittente = {"company_subject_type": "pa","cod_ou":codiceipauo, "company_type": "company","name_amm":name}

                    elif mittente_type == "PersonaGiuridica":
                        contact_data = self._find_data_in_path(
                            parsed_data,
                            "SegnaturaInformatica/Descrizione/Mittente/PersonaGiuridica/ContattiPersonaGiuridica"
                        )
                        name = self._find_data_in_path(
                            parsed_data,
                            "SegnaturaInformatica/Descrizione/Mittente/PersonaGiuridica/Denominazione"
                        )
                        mittente["company_subject_type"] = "private"
                    elif mittente_type == "PersonaFisica":
                        contact_data = self._find_data_in_path(
                            parsed_data,
                            "SegnaturaInformatica/Descrizione/Mittente/PersonaFisica/Contatti"
                        )
                        nome = self._find_data_in_path(
                            parsed_data,
                            "SegnaturaInformatica/Descrizione/Mittente/PersonaFisica/Nome"
                        )
                        cognome = self._find_data_in_path(
                            parsed_data,
                            "SegnaturaInformatica/Descrizione/Mittente/PersonaFisica/Cognome"
                        )
                        name = "%s %s" % nome,cognome
                    else:
                        contact_data = self._find_data_in_path(
                            parsed_data,
                            "SegnaturaInformatica/Descrizione/Mittente/AmministrazioneEstera/ContattiAmministrazione"
                        )
                        name = self._find_data_in_path(
                            parsed_data,
                            "SegnaturaInformatica/Descrizione/Mittente/AmministrazioneEstera/DenominazioneAmministrazione"
                        )
            # mittente_numero_protocollo
            data["mittente_numero_protocollo"] = self._find_data_in_path(
                parsed_data, "SegnaturaInformatica/Intestazione/Identificatore/NumeroRegistrazione"
            )
            # mittente_registro
            data["mittente_registro"] = self._find_data_in_path(
                parsed_data, "SegnaturaInformatica/Intestazione/Identificatore/CodiceRegistro"
            )
            # mittente_data_registrazione
            data["mittente_data_registrazione"] = self._find_data_in_path(
                parsed_data, "SegnaturaInformatica/Intestazione/Identificatore/DataRegistrazione", data_parse="datetime"
            )
            # recupero dati del mittente da inserire come contatto del protocollo

            # cod_amm
            ipa_code = self._find_data_in_path(
                parsed_data, "SegnaturaInformatica/Intestazione/Identificatore/CodiceAmministrazione"
            )
            mittente["cod_amm"] = ipa_code
            # cod_aoo
            aoo_code = self._find_data_in_path(
                parsed_data, "SegnaturaInformatica/Intestazione/Identificatore/CodiceAOO"
            )
            mittente["cod_aoo"] = aoo_code
            mittente["name"] = name
            mittente["fiscalcode"] = fiscalcode
            #indirizzotelematico
            indirizzi_telematici= self._find_data_in_path(contact_data, "IndirizzoTelematico")
            l_indirizzi_telematici = [(0, 0, {"email_address":email_from,"use_in_sending":True})]
            if not isinstance(indirizzi_telematici, list) :
                indirizzi_telematici = [indirizzi_telematici]
            for indirizzo_t in indirizzi_telematici:
                if indirizzo_t != None and indirizzo_t != email_from:
                    l_indirizzi_telematici.append((0, 0, {"email_address":indirizzo_t}))

            mittente["digital_domicile_ids"]= l_indirizzi_telematici
            # street
            dug = self._find_data_in_path(contact_data, "IndirizzoPostale/Toponimo/dug")
            duf = self._find_data_in_path(contact_data, "IndirizzoPostale/Toponimo/duf")
            civico = self._find_data_in_path(contact_data, "Civico")
            street = False
            if dug and duf:
                street = "%s %s" % (dug, duf)
            if civico and street:
                street = "%s %s" % (street, civico)
            mittente["street"] = street
            mittente["zip"] = self._find_data_in_path(contact_data, "IndirizzoPostale/CAP")
            if self._find_data_in_path(contact_data, "IndirizzoPostale/Comune") != None and "#text" in self._find_data_in_path(contact_data, "IndirizzoPostale/Comune"):
                mittente["city"] = self._find_data_in_path(contact_data, "IndirizzoPostale/Comune")["#text"]
            # email
            mittente["email"] = self._find_data_in_path(contact_data, "IndirizzoTelematico")
            # phone
            mittente["phone"] = self._find_data_in_path(contact_data, "Telefono")
            # inserimento dei dati del mittente
            data["mittente"] = mittente
        except Exception as e:
            _logger.error("Errore nel parsing del file segnatura.xml: %s" % str(e))
        return data

    @api.model
    def _find_data_in_path(self, data, path, data_parse=None, default_value=None):
        try:
            path_components = path.split("/")
            for path_component in path_components:
                if data and path_component in data:
                    data = data[path_component]
                else:
                    return default_value
        except Exception as e:
            _logger.error("Errore nella ricerca del path %s nel file segnatura.xml: %s" % (path, str(e)))
            return default_value
        if data_parse == "datetime":
            try:
                data = datetime.strptime(data, "%Y-%m-%d")
            except ValueError:
                _logger.error("Errore nel parsing datetime del valore nel path %s nel file segnatura.xml" % path)
                return default_value
        if not data:
            return default_value
        return data

    def validate_segnatura(self,content,attachements, protocollo_id):
        """da aggiungere la parte di verifica firma segnatura"""
        exceptions = []
        protocollo = self.env["sd.protocollo.protocollo"].browse(protocollo_id)
        try:
            if self._validate_xml(content) != True:
                exceptions.append(_("Error validating signature.xml"))
                if self._validate_xml(content, "../static/xsd/segnatura_protocollo_circolare 60_2013.xsd") == True:
                    protocollo.write({"interoperability" : "2013"})
                elif self._validate_2001_xml(etree.fromstring(content)) == True:
                    protocollo.write({"interoperability": "2001"})
            else:
                protocollo.write({"interoperability": "2021"})
        except:
            _logger.error(_("error in the validation of the segnatura.xml"))
            return [_("error in the validation of the segnatura.xml")]
        return exceptions

    def _get_validation_error_xml(self, root):
        directory_path = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        full_path = os.path.join(directory_path, "../static/xsd/pec_message.xsd")
        xml_validator = etree.XMLSchema(file=full_path)
        xml_file = etree.fromstring(root)
        is_valid = xml_validator.validate(xml_file)
        if not is_valid:
            return str(xml_validator.error_log.filter_from_errors())
