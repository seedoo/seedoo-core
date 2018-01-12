
from openerp import api, models


class TileTile(models.Model):

    _inherit = 'tile.tile'

    # Action methods
    @api.multi
    def open_link(self):
        res = super(TileTile, self).open_link()

        if self.action_id and len(self.action_id.view_ids) == 2:
            res["views"] = [(self.action_id.view_ids[0].view_id.id, 'tree'), (self.action_id.view_ids[1].view_id.id, 'form')]

        return res
