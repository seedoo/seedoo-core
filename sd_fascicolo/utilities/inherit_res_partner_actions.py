from odoo import models, fields, api, _

class ResPartner(models.Model):
    _inherit = "res.partner"

    def action_show_dossiers(self):
        self.ensure_one()

        return {
            "name": _("Dossiers"),
            "view_mode": "tree,form",
            "res_model": "sd.fascicolo.fascicolo",
            "domain": ["|","|","|",
                        ("rup_ids.partner_id", "=", self.id),
                        ("soggetto_intestatario_ids.partner_id", "=", self.id),
                        ("amministrazione_partecipante_ids.partner_id", "=", self.id),
                        ("amministrazione_titolare_ids.partner_id", "=", self.id)],
            "type": "ir.actions.act_window",
            "target": "current",
        }