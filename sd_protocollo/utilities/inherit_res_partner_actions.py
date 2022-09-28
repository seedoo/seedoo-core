from odoo import models, fields, api, _

class ResPartner(models.Model):
    _inherit = "res.partner"

    def action_show_protocols(self):
        self.ensure_one()
        contacts = self.env["sd.protocollo.protocollo"].search([
            "|",
            ("destinatario_ids.partner_id", "=", self.id),
            ("mittente_ids.partner_id", "=", self.id)
        ]).ids
        return {
            "name": _("Protocols"),
            "view_mode": "tree,form",
            "res_model": "sd.protocollo.protocollo",
            "domain": [("id", "in", contacts)],
            "type": "ir.actions.act_window",
            "target": "current",
        }