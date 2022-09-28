from odoo import models


class InheritSdDmsContactPermissions(models.Model):
    _inherit = "sd.dms.contact"

    def _compute_button_edit_contact_invisible(self):
        protocollo_id = self.env.context.get("protocollo_id", False)
        if not protocollo_id:
            return super(InheritSdDmsContactPermissions, self)._compute_button_edit_contact_invisible()
        protocollo = self.env["sd.protocollo.protocollo"].browse(protocollo_id)
        button_edit_contact_invisible = not (protocollo.state == "bozza") or not protocollo.perm_write
        for rec in self:
            rec.button_edit_contact_invisible = button_edit_contact_invisible