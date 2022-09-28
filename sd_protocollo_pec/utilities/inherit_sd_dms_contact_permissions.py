from odoo import models, fields, api


class InheritSdDmsContactPermissions(models.Model):
    _inherit = "sd.dms.contact"

    use_in_sending_invisible = fields.Boolean(
        string="field use_in_sending_invisible",
        compute="_compute_field_use_in_sending_invisible"
    )

    @api.depends("typology")
    def _compute_field_use_in_sending_invisible(self):
        for rec in self:
            rec.use_in_sending_invisible = False if rec.typology == "recipient" else True