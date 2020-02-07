from openerp import models, fields


class IrCron(models.Model):
    _inherit = "ir.cron"

    seedoo_visible = fields.Boolean(
        string="Cron Seedoo",
        required=True,
        default=False
    )
