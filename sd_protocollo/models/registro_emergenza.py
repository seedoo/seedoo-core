from odoo import models, fields, api, _
from odoo.exceptions import UserError

SELCTION_STATE = [
    ("bozza", "Bozza"),
    ("aperto", "Aperto"),
    ("chiuso", "Chiuso")
]


class RegistroEmergenza(models.Model):
    _name = "sd.protocollo.registro.emergenza"
    _description = "Registro Emergenza"
    _rec_name = "causa"

    numero_protocolli = fields.Integer(
        string="Numero Protocolli",
        required=True
    )

    causa = fields.Char(
        string="Causa",
        required=True
    )

    state = fields.Selection(
        string="Stato",
        selection=SELCTION_STATE,
        default=SELCTION_STATE[0][0],
        required=True
    )

    utente_id = fields.Many2one(
        string="Responsabile",
        comodel_name="res.users",
        default=lambda self: self.env.user
    )

    data_inizio = fields.Datetime(
        string="Data Inizio",
        required=True
    )

    data_fine = fields.Datetime(
        string="Data Fine",
        required=True
    )

    registro_id = fields.Many2one(
        string="Registro",
        comodel_name="sd.protocollo.registro",
        required=True
    )

    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        related="registro_id.company_id",
        readonly=True
    )

    numero_ids = fields.One2many(
        string="Numero",
        comodel_name="sd.protocollo.registro.emergenza.numero",
        inverse_name="registro_emergenza_id",
        readonly=True
    )

    field_readonly = fields.Boolean(
        string="Field Invisible",
        compute="compute_field_readonly",
        readonly=True
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
            ("state", "=", "aperto"),
            ("company_id", "=", company_id),
        ]

    @api.model
    def get_ids_can_used_to_protocol(self):
        ids = self.search(self.get_domain_can_used_to_protocol()).ids
        return ids

    def _compute_can_used_to_protocol(self):
        ids = self.get_ids_can_used_to_protocol()
        for registro_emergenza in self:
            if registro_emergenza.id in ids:
                registro_emergenza.can_used_to_protocol = True
            else:
                registro_emergenza.can_used_to_protocol = False

    def _search_can_used_to_protocol(self, operator=None, operand=None):
        ids = self.get_ids_can_used_to_protocol()
        return [("id", "in", ids)]

    @api.depends("state")
    def compute_field_readonly(self):
        for rec in self:
            field_readonly = True
            if rec.state in ["chiuso"]:
                field_readonly = False
            rec.field_readonly = field_readonly

    def unlink(self):
        for rec in self:
            if rec.state == "bozza":
                return super().unlink()
            else:
                raise UserError(_("Non puoi cancellare un registro emergenza che non sia in stato bozza"))

    def action_apri(self):
        registro_emergenza_obj = self.env["sd.protocollo.registro.emergenza"]
        for rec in self:
            if rec.state == "bozza":
                if registro_emergenza_obj.search_count(self._get_domain_registro_emergenza_aperto(rec)) != 0:
                    raise UserError(_("Non è possibile avere più di un registro aperto per la stessa AOO"))
            rec.state = "aperto"

    def _get_domain_registro_emergenza_aperto(self, rec):
        return [("state", "=", "aperto")]
