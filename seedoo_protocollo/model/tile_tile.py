
from openerp import api, models


class TileTile(models.Model):

    _inherit = 'tile.tile'

    # Action methods
    @api.multi
    def open_link(self):
        res = super(TileTile, self).open_link()

        if self.action_id:

            res["view_id"] = [x.view_id.id for x in self.action_id.view_ids]
            res["view_mode"] = self.action_id.view_mode if len(res["view_id"]) == 1 else "tree"
        return res
