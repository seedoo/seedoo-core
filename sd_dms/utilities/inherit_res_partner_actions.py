# Copyright 2020-2022 Flosslab S.r.l.
# Copyright 2017-2019 MuK IT GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, _


class ResPartner(models.Model):
    _inherit = "res.partner"

    def action_show_document_list(self):
        self.ensure_one()
        document_ids = self.env["sd.dms.document"].search([
            "|",
            ("recipient_ids.partner_id", "=", self.id),
            ("sender_ids.partner_id", "=", self.id)
        ]).ids
        context = dict(
            self.env.context,
            create=False
        )
        return {
            "name": _("Documents"),
            "view_mode": "tree,form",
            "res_model": "sd.dms.document",
            "domain": [("id", "in", document_ids)],
            "type": "ir.actions.act_window",
            "target": "current",
            "context":context
        }
