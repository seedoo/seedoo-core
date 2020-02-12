from openerp import models, fields


class IrCron(models.Model):
    _inherit = "ir.cron"

    seedoo_visible = fields.Boolean(
        string="Visibile su Seedoo",
        help="Abilita la visualizzazione di questo cron nella configurazione dei cron del menu di Protocollo",
        required=True,
        default=False
    )
