from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class VoceTitolario(models.Model):
    _inherit = "sd.dms.titolario.voce.titolario"

    assegnatario_default_in = fields.Many2one(
        string="Assegnatario Default Protocollo Ingresso",
        comodel_name="fl.set.voce.organigramma",
        domain=[("tipologia", "=", "ufficio"), ("parent_active", "=", True)]
    )

    assegnatario_default_out = fields.Many2one(
        string="Assegnatario Default Protocollo Uscita",
        comodel_name="fl.set.voce.organigramma",
        domain=[("tipologia", "=", "ufficio"), ("parent_active", "=", True)],
    )

    assegnatario_default_skip = fields.Boolean(
        string="Ignora Assegnatari Default",
        help="Solo se uguale a Ufficio Protocollatore"
    )

    @api.constrains("titolario_company_id")
    def _validate_voce_titolario(self):
        protocollo_obj = self.env["sd.protocollo.protocollo"]
        for rec in self:
            if protocollo_obj.search([("documento_id_voce_titolario_id", "=", rec.id)]) > 0:
                self._raise_error_message(
                    "Non è possibile cambiare la company in quanto il Titolario è stato già usato per la "
                    "protocollazione")

    def _raise_error_message(self, message=None):
        if not message:
            message = "Verificare la company"
        raise ValidationError(_(message))
