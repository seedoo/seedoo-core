# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import orm
from openerp.osv import fields


class ResPartner(orm.Model):
    _inherit = 'res.partner'

    _columns = {
        'legal_type': fields.selection(
            [
                ('individual', 'Persona Fisica'),
                ('legal', 'Azienda privata'),
                ('government', 'Amministrazione pubblica')
            ], 'Tipologia', size=32, required=False),

        'pa_type': fields.selection(
            [
                ('pa', 'Amministrazione Principale'),
                ('aoo', 'Area Organizzativa Omogenea'),
                ('uo', 'Unità Organizzativa')],
            'Tipologia amministrazione', size=5, required=False),

        'super_type': fields.char('super_type', size=5, required=False),

        'ident_code': fields.char(
            'Codice Identificativo Area (AOO)',
            size=256,
            required=False),

        'ammi_code': fields.char(
            'Codice Amministrazione',
            size=256,
            required=False),

        'ipa_code': fields.char(
            'Codice Unità Organizzativa',
            size=256,
            required=False),

        'parent_pa_id': fields.many2one(
            "res.partner",
            "Organizzazione di Appartenenza",
            required=False),

        'parent_pa_type': fields.related(
            'parent_pa_id',
            'pa_type',
            type='char',
            readonly=True,
            string='Tipologia amministrazione padre'),

        'child_pa_ids': fields.one2many(
            "res.partner",
            "parent_pa_id",
            "Strutture Afferenti",
            required=False)

    }

    def on_change_pa_type(self, cr, uid, ids, pa_type):
        res = {'value': {}}

        if pa_type == 'aoo':
            res['value']['super_type'] = 'pa'
        elif pa_type == 'uo':
            res['value']['super_type'] = 'aoo'

        return res
