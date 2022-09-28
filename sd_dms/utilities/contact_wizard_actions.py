# Copyright 2020-2022 Flosslab S.r.l.
# Copyright 2017-2019 MuK IT GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, fields


class ContactWizardActions(models.Model):
    _inherit = "sd.dms.contact"

    def edit_contact_action(self):
        self.ensure_one()
        context = dict(
            self.env.context,
            documento_id=False
        )
        return {
            "name": context.get("wizard_label", ""),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "sd.dms.wizard.document.add.contact",
            "type": "ir.actions.act_window",
            "target": "new",
            "context": context
        }