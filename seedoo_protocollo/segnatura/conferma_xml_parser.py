# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from lxml import etree

# from seedoo_protocollo.model.protocollo import protocollo_protocollo
import openerp
from openerp.tools.translate import _

class ConfermaXMLParser:
    def __init__(self, tree):
        if isinstance(tree, etree._ElementTree):
            self._root = tree.getroot()
        else:
            self._root = tree
        pass

    def getNumeroRegistrazioneMessaggioRicevuto(self):
        vals = ''
        element = self._root.find("./MessaggioRicevuto/Identificatore/NumeroRegistrazione")
        if element is not None and element.text is not None:
            vals = element.text
        return vals

    def getDataRegistrazioneMessaggioRicevuto(self):
        vals = ''
        element = self._root.find("./MessaggioRicevuto/Identificatore/DataRegistrazione")
        if element is not None and element.text is not None:
            vals = element.text
        return vals

    def getCodiceRegistroMessaggioRicevuto(self):
        vals = ''
        element = self._root.find("./MessaggioRicevuto/Identificatore/CodiceRegistro")
        if element is not None and element.text is not None:
            vals = element.text
        return vals