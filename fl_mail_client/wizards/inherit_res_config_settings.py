from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    module_fl_mail_client_template = fields.Boolean(
        string="Template e-mail"
    )

    module_fl_mail_client_pec = fields.Boolean(
        string="Certified mail"
    )

    module_fl_mail_client_fetch_flow = fields.Boolean(
        string="Fetch Flow"
    )

    fetch_from_custom_folder = fields.Boolean(
        string="Fetch mails from custom inbox",
        config_parameter="fl_mail_client.fetch_from_custom_folder"
    )

    move_processed_mail = fields.Boolean(
        string="Move fetched mails to custom folder",
        config_parameter="fl_mail_client.move_processed_mail"
    )

    module_fl_mail_client_history = fields.Boolean(
        string="Advanced history management"
    )

    @api.model
    def set_values(self):
        if self.fetch_from_custom_folder or self.move_processed_mail:
            self.module_fl_mail_client_fetch_flow = True
        return super(ResConfigSettings, self).set_values()
