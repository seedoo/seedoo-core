from odoo import models


class InheritSdDmsDocumentPermissions(models.Model):
    _inherit = "sd.dms.document"

    def _compute_voce_titolario_id_readonly(self):
        super(InheritSdDmsDocumentPermissions, self)._compute_voce_titolario_id_readonly()
        for rec in self:
            if not rec.protocollo_id:
                continue
            rec.voce_titolario_id_readonly = rec.protocollo_id.documento_id_voce_titolario_readonly