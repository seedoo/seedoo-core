from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Archivio(models.Model):
    _name = "sd.protocollo.archivio"
    _rec_name = "nome"

    _description = "Archivio"

    nome = fields.Char(
        string="Nome"
    )

    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        required=True,
        default=lambda self: self.env.company.id
    )

    corrente = fields.Boolean(
        string="Corrente",
        default=False
    )

    protocollo_ids = fields.One2many(
        string="Protocolli",
        comodel_name="sd.protocollo.protocollo",
        inverse_name="archivio_id",
        readonly=True
    )

    protocollo_count = fields.Integer(
        "# Protocollo",
        compute="_compute_protocollo_count",
    )

    can_used_to_protocol = fields.Boolean(
        string="Can Used To Protocol",
        compute="_compute_can_used_to_protocol",
        search="_search_can_used_to_protocol"
    )

    @api.depends("protocollo_ids")
    def _compute_protocollo_count(self):
        for rec in self:
            rec.protocollo_count = self.env["sd.protocollo.protocollo"].with_context(active_test=False).search([
                ("archivio_id", "=", rec.id)
            ], count=True)

    @api.model
    def get_domain_can_used_to_protocol(self):
        company_id = self.env.company.id
        if self.env.context.get("company_id", False):
            company_id = self.env.context.get("company_id")
        return [
            ("corrente", "=", True),
            ("company_id", "=", company_id)
        ]

    @api.model
    def get_ids_can_used_to_protocol(self):
        ids = self.search(self.get_domain_can_used_to_protocol()).ids
        return ids

    def _compute_can_used_to_protocol(self):
        ids = self.get_ids_can_used_to_protocol()
        for registro in self:
            if registro.id in ids:
                registro.can_used_to_protocol = True
            else:
                registro.can_used_to_protocol = False

    def _search_can_used_to_protocol(self, operator=None, operand=None):
        ids = self.get_ids_can_used_to_protocol()
        return [("id", "in", ids)]

    @api.constrains("company_id", "corrente")
    def _validate_archivio(self):
        protocollo_obj = self.env["sd.protocollo.protocollo"]

        for rec in self:
            validation = self._check_archivio(rec)

            # Se si sta cercando di disabilitare l'archivio verifica che non ci siano protocolli associati
            if not rec.corrente and protocollo_obj.search_count([("archivio_id", "=", rec.id)]) > 0:
                return self._raise_error_message(
                    "L'archivio è associato a dei protocolli, quindi non è più possibile modificare l'archivio corrente")

            if validation:
                return self._raise_error_message(validation)

    def _check_archivio(self, archivio):

        # Verifica se presenti più archivi abilitati
        if self.search_count([("corrente", "=", True), ("company_id", "=", archivio.company_id.id)]) > 1:
            return "L'archivio corrente è univoco per Company"

        return False

    def _raise_error_message(self, message=None):
        if not message or message is True:
            message = "L'archivio corrente è univoco per Company"
        raise ValidationError(_(message))
