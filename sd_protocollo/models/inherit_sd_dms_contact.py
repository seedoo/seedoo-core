from odoo import models, fields


class InheritSdDmsContact(models.Model):

    _inherit = "sd.dms.contact"

    mezzo_trasmissione_id = fields.Many2one(
        string="Mezzo di Trasmissione",
        comodel_name="sd.protocollo.mezzo.trasmissione"
    )

    mezzo_trasmissione_nome = fields.Char(
        string="Mezzo Trasmissione Nome"
    )