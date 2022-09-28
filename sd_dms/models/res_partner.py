# Copyright 2020-2022 Flosslab S.r.l.
# Copyright 2017-2019 MuK IT GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, fields, api

LIST_HAS_CHANGE = [
    "name", "parent_id", "display_name", "company_type", "cod_amm", "cod_aoo", "cod_ou", "website", "vat", "function",
    "fiscalcode", "street", "street2", "zip", "city", "state_id", "country_id", "email", "pec_mail", "phone", "mobile", "title"
]


class ResPartner(models.Model):
    _inherit = "res.partner"

    has_changed = fields.Boolean(
        string="Has Change",
        default=False,
        store=False
    )

    documents_count = fields.Char(
        string="Documents count",
        compute="_compute_documents_count"
    )

    @api.onchange(*LIST_HAS_CHANGE)
    def _onchange_has_change(self):
        # Il campo has_change viene cambiato ogni volta che si modifica un campo nella vista, questo attiva il trigger
        # dell' api.depends, che avendo il campo store settato a False non viene salvato alla chiusura dell'istanza e quindi
        # alla modifica sarà possibile riattivare il trigger
        self.ensure_one()
        self.has_changed = True

    def _compute_documents_count(self):
        document_obj = self.env["sd.dms.document"]
        for rec in self:
            rec.documents_count = document_obj.search([
                "|",
                ("recipient_ids.partner_id", "=", self.id),
                ("sender_ids.partner_id", "=", self.id)
            ], count=True)