# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import orm, fields


class protocollo_configurazione(orm.Model):
    _name = 'protocollo.configurazione'
    _columns = {
        'genera_segnatura': fields.boolean('Genera Segnatura nel PDF'),
        'genera_xml_segnatura': fields.boolean('Genera XML Segnatura'),
    }

    _defaults = {
        'genera_segnatura': True,
        'genera_xml_segnatura': True,
    }
