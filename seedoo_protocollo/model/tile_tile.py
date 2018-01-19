
from openerp import api, models
from openerp.osv import fields

class TileTile(models.Model):

    _inherit = 'tile.tile'

    # Action methods
    @api.multi
    def open_link(self):
        res = super(TileTile, self).open_link()

        if self.action_id and len(self.action_id.view_ids) == 2:
            res["views"] = [(self.action_id.view_ids[0].view_id.id, 'tree'), (self.action_id.view_ids[1].view_id.id, 'form')]
        return res

    TAG_SELECTION = [
        ('generale', 'Generale'),
        ('ingresso', 'Ingresso'),
        ('uscita', 'Uscita'),
        ('ingresso_assegnazioni', 'Assegnazioni / Ingresso'),
        ('uscita_assegnazioni', 'Assegnazioni / Uscita'),
    ]

    _columns = {
        'sequence_tile': fields.integer('Ordine', required=True),
        'icon_tile': fields.char('Classe icona', required=True),
        'tag_tile': fields.selection(
            TAG_SELECTION,
            'Tag Board',
            help="Indicare il tag",
            select=True,
        ),
    }

    _order = 'sequence_tile'

    _defaults = {
        'icon_tile': 'fa-envelope-o',
        'tag_tile': 'generale',
    }
