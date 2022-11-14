from odoo import models, fields, api


class AssegnazionePermissions(models.Model):
    _inherit = "sd.protocollo.assegnazione"

    button_elimina_assegnazione_invisible = fields.Boolean(
        string="button modifica assegnazione invisible",
        compute="compute_buttons_invisible"
    )

    def compute_buttons_invisible(self):
        for rec in self:
            rec.button_elimina_assegnazione_invisible = rec._compute_button_elimina_assegnazione_invisible()

    def _compute_button_elimina_assegnazione_invisible(self):
        return self.protocollo_id.button_elimina_assegnatari_invisible
