from odoo import models, fields, api


class InheritSdFascicoloFascicoloPermissions(models.Model):
    _inherit = "sd.fascicolo.fascicolo"

    def _compute_button_tree_disassocia_fascicolo_invisible(self):
        super(InheritSdFascicoloFascicoloPermissions, self)._compute_button_tree_disassocia_fascicolo_invisible()
        for rec in self:
            if not rec.button_tree_disassocia_fascicolo_invisible:
                continue
            if rec.env.context.get("disassocia_fascicolo_protocollo_id", False) and rec.perm_write:
                rec.button_tree_disassocia_fascicolo_invisible = False