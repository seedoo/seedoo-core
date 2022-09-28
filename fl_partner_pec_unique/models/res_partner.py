from odoo import models, api
from odoo.addons.fl_partner_email.models.res_partner import DICT_TYPE_ERROR

DICT_TYPE_ERROR.update({
    "pec_mail": "PEC Mail"
})

class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.onchange("pec_mail")
    def check_pec_mail(self):
        if self.pec_mail:
            message = self.check_create_mail_dict({"pec_mail": self.pec_mail}, self.id.origin, False)
            if message:
                self.pec_mail = False
                return {
                    "warning": {
                        "title": "Attenzione!",
                        "message": message
                    }
                }

    @api.model
    def get_mail_dict(self, vals):
        mail_dict = super(ResPartner, self).get_mail_dict(vals)
        if not vals.get("pec_mail", False):
            return mail_dict
        if not self.env["ir.config_parameter"].sudo().get_param("fl_partner_pec_unique.unique_pec_mail"):
            return mail_dict
        mail_dict["pec_mail"] = vals.get("pec_mail", False)
        return mail_dict