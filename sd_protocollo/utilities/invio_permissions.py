from odoo import models, fields, api


class InvioPermissions(models.Model):
    _inherit = "sd.protocollo.invio"

    field_tree_invio_decoration_state = fields.Boolean(
        string="field_tree invio decoration state",
        compute="_compute_field_tree_invio_decoration_state"
    )

    @api.depends("field_tree_invio_decoration_state")
    def _compute_field_tree_invio_decoration_state(self):
        for invio in self:
            tree_invio_decoration_state = ""
            if invio.state in ['received', 'sent']:
                tree_invio_decoration_state = "success"
            elif invio.state in ['exception'] and not invio.invio_successivo_ids:
                tree_invio_decoration_state = "danger"
            elif invio.invio_successivo_ids:
                tree_invio_decoration_state = "muted"
            elif invio.state in ['outgoing']:
                tree_invio_decoration_state = "info"
            invio.field_tree_invio_decoration_state = tree_invio_decoration_state
