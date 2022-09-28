from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Registro(models.Model):
    _name = "sd.protocollo.registro"
    _rec_name = "nome"

    _description = "Registro"

    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        required=True,
        default=lambda self: self.env.company.id
    )

    ufficiale = fields.Boolean(
        string="Ufficiale",
        default=False
    )

    nome = fields.Char(
        string="Nome"
    )

    codice = fields.Char(
        string="Codice"
    )

    sequence_id = fields.Many2one(
        string="Sequence",
        comodel_name="ir.sequence",
        readonly=True,
    )

    utente_abilitato_ids = fields.Many2many(
        string="Utenti Abilitati",
        comodel_name="res.users",
        relation="sd_protocollo_registro_res_users_rel",
        column1="registro_id",
        column2="res_users_id",
    )

    ordinamento = fields.Integer(
        string="Ordinamento"
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

    @api.model
    def get_domain_can_used_to_protocol(self):
        company_id = self.env.company.id
        if self.env.context.get("company_id", False):
            company_id = self.env.context.get("company_id")
        return [
            ("ufficiale", "=", True),
            ("utente_abilitato_ids", "in", [self.env.uid]),
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

    @api.model
    def create(self, vals_list):
        ir_sequence_obj = self.env["ir.sequence"]

        res = super().create(vals_list)

        for rec in res:
            sequence = ir_sequence_obj.create({
                "name": "Sequence " + rec.nome,
                "code": rec.codice,
                'implementation': 'no_gap',
                'prefix': '',
                'suffix': '',
                'padding': 7,
            })
            rec.sequence_id = sequence

        return res

    def unlink(self):
        for rec in self:
            rec.sequence_id.unlink()
        return super().unlink()

    @api.constrains("company_id", "ufficiale")
    def _validate_registro(self):
        for rec in self:
            validation = self._check_registro(rec)
            # Se si sta cercando di disabilitare il registro verified che non ci siano protocolli associati
            rec._check_associate_protocol()
            if validation:
                return self._raise_error_message(validation)

    def _check_associate_protocol(self):
        protocollo_obj = self.env["sd.protocollo.protocollo"]
        if not self.ufficiale and protocollo_obj.search_count([("registro_id", "=", self.id)]) > 0:
            return self._raise_error_message(
                "Il registro è associato a dei protocolli, quindi non è più possibile modificare il registro corrente")


    def _check_registro(self, registro):
        # Verifica se presenti più registri abilitati
        if self.search_count([("ufficiale", "=", True), ("company_id", "=", registro.company_id.id)]) > 1:
            return "Il registro ufficiale è univoco per Company"

        return False

    def _raise_error_message(self, message=None):
        if not message or message is True:
            message = "Il registro ufficiale è univoco per Company"
        raise ValidationError(_(message))
