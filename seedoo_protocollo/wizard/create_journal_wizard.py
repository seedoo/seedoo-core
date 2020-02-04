# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

import logging

from openerp import models, fields, api

_logger = logging.getLogger(__name__)


class ProtocolloJournalWizard(models.TransientModel):
    _name = "protocollo.journal.wizard"
    _description = "Crea Registro Giornaliero"

    date_registro = fields.Date(
        string="Data Registro",
        help="Indicare la data per la quale si vuole creare il Registro Giornaliero",
        required=True
    )

    aoo_id = fields.Many2one(
        string="AOO",
        help="Indicare l'AOO di riferimento per il Registro Giornaliero da creare",
        comodel_name="protocollo.aoo",
        required=True,
        default=lambda self: self.get_aoo()
    )

    @api.model
    def get_aoo(self):
        aoo_obj = self.env["protocollo.aoo"]

        aoo_ids = aoo_obj.search([])
        for aoo_id in aoo_ids:
            if aoo_obj.is_visible_to_protocol_action(aoo_id.id):
                return aoo_id

        return False

    @api.multi
    def action_create(self):
        self.ensure_one()

        journal_obj = self.env["protocollo.journal"]

        journal_id = journal_obj.journal_create(self.aoo_id, self.date_registro)

        return {
            "type": "ir.actions.act_window",
            "name": "Registro Giornaliero di Protocollo",
            "view_type": "tree,form",
            "view_mode": "form",
            "res_model": journal_id._name,
            "res_id": journal_id.id,
            "target": "self",
            "context": self.env.context
        }

    # def action_create(self, cr, uid, ids, context=None):
    #     journal_obj = self.pool.get("protocollo.journal")
    #     journal_obj.action_create(cr, uid)

    # def get_aoo_id(self, cr, uid, wizard):
    #     aoo_ids = self.pool.get('protocollo.aoo').search(cr, uid, [])
    #     for aoo_id in aoo_ids:
    #         check = self.pool.get('protocollo.aoo').is_visible_to_protocol_action(cr, uid, aoo_id)
    #         if check:
    #             return aoo_id
    #     return False

    # def action_create(self, cr, uid, ids, context=None):
    #     wizard = self.browse(cr, uid, ids[0], context)
    #
    #     aoo_id = self.get_aoo_id(cr, uid, wizard)
    #
    #     journal_obj = self.pool.get('protocollo.journal')
    #     journal_today = journal_obj.search(cr, uid, [
    #         ('aoo_id', '=', aoo_id),
    #         ('state', '=', 'closed'),
    #         ('date', '=', wizard.date_register)
    #     ])
    #     if journal_today:
    #         raise osv.except_osv(
    #             _('Attenzione!'),
    #             _('Registro Giornaliero del Protocollo esistente per la data selezionata!')
    #         )
    #     protocollo_obj = self.pool.get('protocollo.protocollo')
    #     protocol_ids = protocollo_obj.search(cr, uid, [
    #         ('aoo_id', '=', aoo_id),
    #         ('state', 'in', ['registered', 'notified', 'waiting', 'error', 'sent']),
    #         ('registration_date', '>', wizard.date_register + ' 00:00:00'),
    #         ('registration_date', '<', wizard.date_register + ' 23:59:59'),
    #     ])
    #     journal_id = journal_obj.create(cr, uid, {
    #         'name': wizard.date_register,
    #         'date': wizard.date_register,
    #         'aoo_id': aoo_id,
    #         'user_id': uid,
    #         'protocol_ids': [[6, 0, protocol_ids]],
    #         'state': 'closed',
    #     })
    #
    #     datas = {'ids': [journal_id], 'model': 'protocollo.journal'}
    #     return {
    #         'type': 'ir.actions.report.xml',
    #         'report_name': 'seedoo_protocollo.journal_qweb',
    #         'datas': datas,
    #     }
