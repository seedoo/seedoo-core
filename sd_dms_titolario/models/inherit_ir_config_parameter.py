from odoo import models, api


class IrConfigParameters(models.Model):
    _inherit = "ir.config_parameter"

    @api.model
    def ztree_only_child_param(self):
        key = "sd_dms.ztree_widget_config"
        return self.sudo().get_param(key, False)
