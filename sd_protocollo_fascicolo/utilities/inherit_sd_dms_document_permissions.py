from odoo import models, fields, api


class InheritSdDmsDocumentPermissions(models.Model):
    _inherit = "sd.dms.document"

    def _compute_button_disassocia_documento_invisible(self):
        result = super(InheritSdDmsDocumentPermissions, self)._compute_button_disassocia_documento_invisible()
        if result:
            return result
        # se il documento è associato ad un protocollo allora si deve controllare se si hanno i permessi di
        # fascicolazione sul protocollo
        return self.protocollo_id._is_fascicolazione_disabled() if self.protocollo_id else False