# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import orm, fields


class dematerializzazione_configurazione(orm.Model):
    _name = 'dematerializzazione.configurazione'
    _columns = {
        'etichetta_altezza': fields.integer('Altezza Etichetta'),
        'etichetta_larghezza': fields.integer('Larghezza Etichetta'),
        #'importer_ids': fields.one2many('dematerializzazione.importer', 'configurazione_id', 'Importer'),
    }

    _defaults = {
        'etichetta_altezza': 28,
        'etichetta_larghezza': 54,
    }
