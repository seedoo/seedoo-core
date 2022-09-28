from odoo import models, fields, api


class AssegnazionePermissions(models.Model):
    _inherit = "sd.protocollo.assegnazione"

    button_elimina_assegnazione_invisible = fields.Boolean(
        string="button modifica assegnazione invisible",
        related="protocollo_id.button_elimina_assegnatari_invisible"
    )