from odoo import models, fields, api


class MezzoTrasmissione(models.Model):
    _name = "sd.protocollo.mezzo.trasmissione"
    _rec_name = "nome"
    _order = "ordinamento"
    _description = "Mezzo Trasmissione"

    nome = fields.Char(
        string="Nome"
    )

    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        required=True,
        default=lambda self: self.env.company.id
    )

    ordinamento = fields.Integer(
        string="Ordinamento"
    )

    icon = fields.Char(
        string="Icon",
        help="Font awesome icon e.g. fa-envelope"
    )

    icon_color = fields.Char(
        string="Icon Color",
        help="Icon color in RGB",
        default="#D2691E"
    )

    active = fields.Boolean(
        string="Archiviato",
        default=True
    )

    can_used_to_protocol = fields.Boolean(
        string="Can Used To Protocol",
        compute="_compute_can_used_to_protocol",
        search="_search_can_used_to_protocol"
    )

    def get_domain_can_used_to_protocol(self):
        company_id = self.env.company.id
        if self.env.context.get("company_id", False):
            company_id = self.env.context.get("company_id")
        return [("company_id", "=", company_id)]

    def get_ids_can_used_to_protocol(self):
        domain = self.get_domain_can_used_to_protocol()
        ids = self.search(domain).ids
        return ids

    def _compute_can_used_to_protocol(self):
        ids = self.get_ids_can_used_to_protocol()
        for mezzo_trasmissione in self:
            if mezzo_trasmissione.id in ids:
                mezzo_trasmissione.can_used_to_protocol = True
            else:
                mezzo_trasmissione.can_used_to_protocol = False

    def _search_can_used_to_protocol(self, operator=None, operand=None):
        ids = self.get_ids_can_used_to_protocol()
        return [("id", "in", ids)]

    @api.model
    def get_integrazione_values(self):
        return ["pec"]
