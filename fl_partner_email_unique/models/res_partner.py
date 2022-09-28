from odoo import models, api

class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def get_mail_dict(self, vals):
        mail_dict = super(ResPartner, self).get_mail_dict(vals)
        if not vals.get("email", False):
            return mail_dict
        if not self.env["ir.config_parameter"].sudo().get_param("fl_partner_email_unique.unique_mail"):
            return mail_dict
        mail_dict["email"] = vals.get("email", False)
        return mail_dict