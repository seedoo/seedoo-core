from odoo import models, fields


class ResPartner(models.Model):
    _inherit = "res.partner"

    soggetto_coinvolto_fascicolo_ids = fields.Many2many(
        string="Partner",
        comodel_name="sd.fascicolo.fascicolo",
        relation="sd_fascicolo_fascicolo_soggetto_coinvolto_rel",
        column1="partner_id",
        column2="fascicolo_id"
    )

    fascicolo_ids_count = fields.Integer(
        string="# Dossiers ",
        compute="_compute_fascicolo_ids_count",
    )

    def _compute_fascicolo_ids_count(self):
        partners_dossiers_obj = self.env["sd.fascicolo.fascicolo"]
        for partner in self:
            fascicolo_ids_count = partners_dossiers_obj.search(["|","|","|",
                                                                ("rup_ids.partner_id", "=", self.id),
                                                                ("soggetto_intestatario_ids.partner_id", "=", self.id),
                                                                ("amministrazione_partecipante_ids.partner_id", "=", self.id),
                                                                ("amministrazione_titolare_ids.partner_id", "=", self.id)], count=True)
            partner.fascicolo_ids_count = fascicolo_ids_count
