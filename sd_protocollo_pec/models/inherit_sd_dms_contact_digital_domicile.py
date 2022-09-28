from odoo import models, fields, api


class InheritSdDmsContactDigitalDomicile(models.Model):
    _inherit = "sd.dms.contact.digital.domicile"

    use_in_sending = fields.Boolean(
        string="Use in sending",
        default=False
    )

    @api.model
    def get_values_partner_contact_digital_domicile(self, digital_domicile):
        values = super(InheritSdDmsContactDigitalDomicile, self).get_values_partner_contact_digital_domicile(digital_domicile)
        if "use_in_sending" in digital_domicile:
            values["use_in_sending"] = digital_domicile.use_in_sending
        return values