# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import fields, osv


class res_company(osv.Model):
    _inherit = 'res.company'

    def _get_default_logo(self, cr, uid, ids, field, arg, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        res = dict.fromkeys(ids, False)
        configurazione_ids = self.pool.get('protocollo.configurazione').search(cr, uid, [])
        configurazione = self.pool.get('protocollo.configurazione').browse(cr, uid, configurazione_ids[0])
        for item in self.browse(cr, uid, ids):
            res[item.id] = configurazione.ammi_logo
        return res


        return configurazione.logo

    # def _get_preview_datas(self, cr, uid, ids, field, arg, context=None):
    #     if isinstance(ids, (list, tuple)) and not len(ids):
    #         return []
    #     if isinstance(ids, (long, int)):
    #         ids = [ids]
    #     res = dict.fromkeys(ids, False)
    #     for attach in self.browse(cr, uid, ids):
    #         res[attach.id] = attach.datas
    #     return res

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
        'ammi_logo': fields.function(_get_default_logo, type='binary', string='Logo Amministrazione'),
    }

