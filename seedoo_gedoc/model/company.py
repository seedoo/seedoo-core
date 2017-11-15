# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import fields, osv


class res_company(osv.Model):
    _inherit = 'res.company'

    # FIXME: il codice identificativo comprende sia l'amministrazione
    #      che l' AOO, per cui attualmente il protocollo lo si può
    #      utilizzare solo quando la AOO è unica!
    _columns = {
        'ammi_code': fields.char(
            'Codice Identificativo Amministrazione',
            size=256,
            required=False),
        # 'ident_code': fields.char(
        #     'Codice Identificativo Area',
        #     size=256,
        #     required=False),
        #
        # 'reserved_user_id': fields.many2one(
        #     'res.users',
        #     'Resposabile Dati Sensibili'
        # ),
    }
