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


class AnnullamentoXML:
    def __init__(self, protocollo, cr, uid):
        self.protocollo = protocollo
        self.prot_number = protocollo.name
        self.creation_date = protocollo.creation_date
        # date_object = dateutil.parser.parse(protocollo.creation_date)
        self.sender_prot_number = protocollo.sender_protocol
        self.sender_register = protocollo.sender_register
        self.sender_registration_date = protocollo.sender_registration_date
        self.receiving_date = protocollo.receiving_date
        # self.prot_date = date_object
        self.prot_type = protocollo.type
        self.cr = cr
        self.uid = uid

        self.pooler = protocollo.pool
        self.resUsersObj = self.pooler.get("res.users")
        self.protocolloObj = self.pooler.get("protocollo.protocollo")
        self.currentUser = self.resUsersObj.browse(cr, uid, uid)

        if protocollo.aoo_id.ident_code is not False:
            self.codiceAOO = str(protocollo.aoo_id.ident_code)
        else:
            self.codiceAOO = None
        pass

    def generate_receipt_root(self):
        root = etree.Element("AnnullamentoProtocollazione")
        identificatore = self.createIdentificatore()
        motivo = self.createMotivo()
        provvedimento = self.createProvvedimento()
        root.append(identificatore)
        root.append(motivo)
        root.append(provvedimento)
        if self.validateXml(root):
            return root
        else:
            raise openerp.exceptions.Warning(
                _('Errore nella validazione xml di annullamento'))

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

    def createMotivo(self, motivoVal= ''):
        motivo = etree.Element("Motivo")
        motivo.text = motivoVal if motivoVal else ''
        return motivo

    def createProvvedimento(self, provvedimentoVal= ''):
        provvedimento = etree.Element("Provvedimento")
        provvedimento.text = provvedimentoVal if provvedimentoVal else ''
        return provvedimento

    def createIdentificatore(self):
        identificatore = etree.Element("Identificatore")
        codiceAmministrazione = self.createCodiceAmministrazione()
        codiceAOO = self.createCodiceAOO(self.codiceAOO)
        numeroRegistrazione = self.createNumeroRegistrazione(self.prot_number)
        dataRegistrazione = self.createDataRegistrazione(self.creation_date)
        identificatore.append(codiceAmministrazione)
        identificatore.append(codiceAOO)
        identificatore.append(numeroRegistrazione)
        identificatore.append(dataRegistrazione)
        return identificatore

    def createDataRegistrazione(self, dataRegistrazioneVal=''):
        dataRegistrazione = etree.Element("DataRegistrazione")
        dataRegistrazione.text = dataRegistrazioneVal if dataRegistrazioneVal else ''
        return dataRegistrazione

    def createCodiceRegistro(self, codiceRegistroVal=''):
        codiceRegistro = etree.Element("CodiceRegistro")
        codiceRegistro.text = codiceRegistroVal if codiceRegistroVal else ''
        return codiceRegistro

    def createNumeroRegistrazione(self, numeroRegistrazioneVal=''):
        numeroRegistrazione = etree.Element("NumeroRegistrazione")
        numeroRegistrazione.text = numeroRegistrazioneVal if numeroRegistrazioneVal else ''
        return numeroRegistrazione

    def createCodiceAOO(self, codiceAOOVal=""):
        codiceAOO = etree.Element("CodiceAOO")
        codiceAOO.text = codiceAOOVal if codiceAOOVal else ''
        return codiceAOO

    def createCodiceAmministrazione(self, codiceAmministrazioneVal=""):
        codiceAmministrazione = etree.Element("CodiceAmministrazione")
        codiceAmministrazione.text = codiceAmministrazioneVal if codiceAmministrazioneVal else ''
        return codiceAmministrazione