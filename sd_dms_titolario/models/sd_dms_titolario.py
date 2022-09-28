from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Titolario(models.Model):
    _name = "sd.dms.titolario.titolario"
    _description = "Titolario"

    name = fields.Char(
        string="Nome",
        required=True,
        readonly=False,
        default=lambda self: "Titolario #" + str(sum(
            x if x else 0 for x in
            [self.env['sd.dms.titolario.titolario'].sudo().search([], limit=1, order='id desc').id]))
    )

    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        default=lambda self: self.env.company.id
    )

    state = fields.Boolean(
        string="Stato",
        default=False
    )

    voce_titolario_ids = fields.One2many(
        string="Voci Titolario",
        comodel_name="sd.dms.titolario.voce.titolario",
        inverse_name="titolario_id",
    )

    count_voci_titolario = fields.Integer(
        string="Count voci titolario",
        compute="_compute_count_voci_titolario",
        readonly=True
    )

    active = fields.Boolean(
        string="Active",
        default=True
    )

    @api.depends("voce_titolario_ids")
    def _compute_count_voci_titolario(self):
        for rec in self:
            rec.count_voci_titolario = len(rec.voce_titolario_ids)

    @api.constrains("company_id", "state")
    def _validate_titolario(self):
        for rec in self:
            validate_company_titolario = self._check_company_titolario(rec)
            if validate_company_titolario:
                return self._raise_error_message(validate_company_titolario)

    def _check_company_titolario(self, titolario):
        # Verifica che esista solamente un titolario attivo per company
        if self.search_count([("company_id", "=", titolario.company_id.id), ("state", "=", True)]) > 1:
            return "Può esserci un solo titolario attivo per company"

        return False

    def _raise_error_message(self, message=None):
        if not message or message is True:
            message = "Verifica la Company del Titolario"
        raise ValidationError(_(message))

    def action_archive(self):
        super(Titolario, self).action_archive()
        voce_titolario_obj = self.env["sd.dms.titolario.voce.titolario"].sudo()
        voci_titolario = voce_titolario_obj.search([("titolario_id", "=", self.id)])
        for voce in voci_titolario:
            voce.action_archive()

    def action_unarchive(self):
        super(Titolario, self).action_unarchive()
        voce_titolario_obj = self.env["sd.dms.titolario.voce.titolario"].sudo()
        voci_titolario = voce_titolario_obj.search([("titolario_id", "=", self.id), ("active", "=", False)])
        for voce in voci_titolario:
            voce.action_unarchive()
