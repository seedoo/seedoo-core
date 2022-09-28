from odoo import models, fields, api


class InheritSdDmsContactEmailAddress(models.Model):
    _inherit = "sd.dms.contact.email.address"

    use_in_sending = fields.Boolean(
        string="Use in sending",
        default=False
    )

    @api.model
    def get_values_partner_contact_email_address(self, email_address):
        values = super(InheritSdDmsContactEmailAddress, self).get_values_partner_contact_email_address(email_address)
        if "use_in_sending" in email_address:
            values["use_in_sending"] = email_address.use_in_sending
        return values