# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import fields, osv, orm
from ..model.util.selection import *



class protocollo_aggiungi_assegnatari_wizard(osv.TransientModel):
    _name = 'protocollo.aggiungi.assegnatari.wizard'
    _description = 'Aggiungi Assegnatari'

    _columns = {
        'assegnatario_competenza_id': fields.many2one('protocollo.assegnatario',
                                                      'Assegnatario per Competenza',
                                                      required=True),

        'assegnatario_conoscenza_ids': fields.many2many('protocollo.assegnatario',
                                                        'protocollo_aggiungi_assegnatari_rel',
                                                        'wizard_id',
                                                        'assegnatario_id',
                                                        'Assegnatari Conoscenza'),
    }

    def _default_assegnatario_competenza_id(self, cr, uid, context):
        assegnazione_obj = self.pool.get('protocollo.assegnazione')
        assegnazione_ids = assegnazione_obj.search(cr, uid, [
            ('protocollo_id', '=', context['active_id']),
            ('tipologia_assegnazione', '=', 'competenza'),
            ('parent_id', '=', False)
        ])
        if assegnazione_ids:
            assegnazione = assegnazione_obj.browse(cr, uid, assegnazione_ids[0])
            return assegnazione.assegnatario_id.id
        return False

    def _default_assegnatario_conoscenza_ids(self, cr, uid, context):
        assegnazione_obj = self.pool.get('protocollo.assegnazione')
        assegnazione_ids = assegnazione_obj.search(cr, uid, [
            ('protocollo_id', '=', context['active_id']),
            ('tipologia_assegnazione', '=', 'conoscenza'),
            ('parent_id', '=', False)
        ])
        if assegnazione_ids:
            assegnatario_ids = []
            assegnazione_ids = assegnazione_obj.browse(cr, uid, assegnazione_ids)
            for assegnazione in assegnazione_ids:
                assegnatario_ids.append(assegnazione.assegnatario_id.id)
            return assegnatario_ids
        return False

    _defaults = {
        'assegnatario_competenza_id': _default_assegnatario_competenza_id,
        'assegnatario_conoscenza_ids': _default_assegnatario_conoscenza_ids
    }

    def action_save(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids[0], context)
        employee_ids = self.pool.get('hr.employee').search(cr, uid, [('user_id', '=', uid)])
        self.pool.get('protocollo.assegnazione').salva_assegnazione_competenza(
            cr,
            uid,
            context.get('active_id', False),
            wizard.assegnatario_competenza_id.id if wizard.assegnatario_competenza_id else False,
            employee_ids[0] if employee_ids else False
        )

        assegnatario_conoscenza_to_save_ids = []
        assegnatario_conoscenza_ids = wizard.assegnatario_conoscenza_ids.ids
        for assegnatario in wizard.assegnatario_conoscenza_ids:
            if assegnatario.tipologia=='department' or (assegnatario.parent_id and assegnatario.parent_id.id not in assegnatario_conoscenza_ids):
                assegnatario_conoscenza_to_save_ids.append(assegnatario.id)

        self.pool.get('protocollo.assegnazione').salva_assegnazione_conoscenza(
            cr,
            uid,
            context.get('active_id', False),
            assegnatario_conoscenza_to_save_ids,
            employee_ids[0] if employee_ids else False
        )

        #if not protocollo.reserved:
            #self._salva_assegnatari_ufficio
        #self._salva_assegnatari_dipendente

        return {'type': 'ir.actions.act_window_close'}
