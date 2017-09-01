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


class SegnaturaXMLParser:
    def __init__(self, attach_path):
        tree = etree.parse(attach_path)
        self._root = tree.getroot()
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

    def getNumeroRegistrazione(self):
        vals = ''
        element = self._root.find("./Intestazione/Identificatore/NumeroRegistrazione")
        if element is not None and element.text is not None:
            vals = element.text
        return vals

    def getDataRegistrazione(self):
        vals = ''
        element = self._root.find("./Intestazione/Identificatore/DataRegistrazione")
        if element is not None and element.text is not None:
            vals = element.text
        return vals

    def getCodiceRegistro(self):
        vals = ''
        element = self._root.find("./Intestazione/Identificatore/CodiceRegistro")
        if element is not None and element.text is not None:
            vals = element.text
        return vals

    def getTipoMittente(self):
        vals = ''
        element = self._root.find("./Intestazione/Origine/Mittente/Amministrazione")
        if element is not None and element.tag is not None:
            vals = 'government'
        return vals

    def getDenominazioneAmministrazione(self):
        vals = ''
        element = self._root.find("./Intestazione/Origine/Mittente/Amministrazione/Denominazione")
        if element is not None and element.text is not None:
            vals = element.text
        return vals

    def getDenominazioneAOO(self):
        vals = ''
        element = self._root.find("./Intestazione/Origine/Mittente/AOO/Denominazione")
        if element is not None and element.text is not None:
            vals = element.text
        return vals

    def getDenominazioneUnitaOrganizzativa(self):
        vals = ''
        element = self._root.find("./Intestazione/Origine/Mittente/Amministrazione/UnitaOrganizzativa/Denominazione")
        if element is not None and element.text is not None:
            vals = element.text
        return vals

    def getDenominazioneCompleta(self):
        vals = ''
        denominazioneAmministrazione = self.getDenominazioneAmministrazione()
        denominazioneAOO = self.getDenominazioneAOO()
        denominazioneUnitaOrganizzativa = self.getDenominazioneUnitaOrganizzativa()
        if len(denominazioneAmministrazione) > 0:
            vals = " AMM " + denominazioneAmministrazione
        if len(denominazioneAOO) > 0 and denominazioneAmministrazione != denominazioneAOO:
            vals += " - AOO " + denominazioneAOO
        if len(denominazioneUnitaOrganizzativa) > 0:
            vals += " - UO " + denominazioneUnitaOrganizzativa
        return vals

    def getTipoAmministrazione(self):
        vals = ''
        denominazioneAmministrazione = self.getDenominazioneAmministrazione()
        denominazioneAOO = self.getDenominazioneAOO()
        denominazioneUnitaOrganizzativa = self.getDenominazioneUnitaOrganizzativa()
        if len(denominazioneUnitaOrganizzativa) > 0:
            vals = 'uo'
        elif len(denominazioneAOO) > 0:
            vals = 'aoo'
        elif len(denominazioneAmministrazione) > 0:
            vals = 'pa'
        return vals

    def getCodiceAmministrazione(self):
        vals = ''
        element = self._root.find("./Intestazione/Origine/Mittente/Amministrazione/CodiceAmministrazione")
        if element is not None and element.text is not None:
            vals = element.text
        else:
            element = self._root.find("./Intestazione/Identificatore/CodiceAmministrazione")
            if element is not None and element.text is not None:
                vals = element.text
        return vals

    def getCodiceAOO(self):
        vals = ''
        element = self._root.find("./Intestazione/Origine/Mittente/AOO/CodiceAOO")
        if element is not None and element.text is not None:
            vals = element.text
        else:
            element = self._root.find("./Intestazione/Identificatore/CodiceAOO")
            if element is not None and element.text is not None:
                vals = element.text
        return vals

    def getCodiceUnitaOrganizzativa(self):
        vals = ''
        element = self._root.find("./Intestazione/Origine/Mittente/Amministrazione/UnitaOrganizzativa/Identificativo")
        if element is not None and element.text is not None:
            vals = element.text
        return vals

    def getToponimo(self):
        vals = ''
        dug = ''
        element = self._root.find("./Intestazione/Origine/Mittente/*/UnitaOrganizzativa/IndirizzoPostale/Toponimo")
        if element is not None and element.text is not None:
            if element.attrib['dug'] is not None:
               dug = element.attrib['dug'] + " "
            vals = dug + element.text
            if len(self.getCivico()):
                vals = vals + " " + self.getCivico()
        return vals

    def getCivico(self):
        vals = ''
        element = self._root.find("./Intestazione/Origine/Mittente/*/UnitaOrganizzativa/IndirizzoPostale/Civico")
        if element is not None and element.text is not None:
            vals = element.text
        return vals

    def getCAP(self):
        vals = ''
        element = self._root.find("./Intestazione/Origine/Mittente/*/UnitaOrganizzativa/IndirizzoPostale/CAP")
        if element is not None and element.text is not None:
            vals = element.text
        return vals

    def getComune(self):
        vals = ''
        element = self._root.find("./Intestazione/Origine/Mittente/*/UnitaOrganizzativa/IndirizzoPostale/Comune")
        if element is not None and element.text is not None:
            vals = element.text
        return vals

    def getProvincia(self):
        vals = ''
        element = self._root.find("./Intestazione/Origine/Mittente/*/UnitaOrganizzativa/IndirizzoPostale/Provincia")
        if element is not None and element.text is not None:
            vals = element.text
        return vals

    def getNazione(self):
        vals = ''
        element = self._root.find("./Intestazione/Origine/Mittente/*/UnitaOrganizzativa/IndirizzoPostale/Nazione")
        if element is not None and element.text is not None:
            vals = element.text
        return vals

    def getTelefono(self):
        vals = ''
        element = self._root.find("./Intestazione/Origine/Mittente/*/UnitaOrganizzativa/Telefono")
        if element is not None and element.text is not None:
            vals = element.text
        return vals

    def getFax(self):
        vals = ''
        element = self._root.find("./Intestazione/Origine/Mittente/*/UnitaOrganizzativa/Fax")
        if element is not None and element.text is not None:
            vals = element.text
        return vals

    def getIndirizzoTelematico(self):
        vals = ''
        element = self._root.find("./Intestazione/Origine/Mittente/*/UnitaOrganizzativa/IndirizzoTelematico")
        if element is not None and element.text is not None:
            vals = element.text
        return vals