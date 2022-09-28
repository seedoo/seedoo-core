from odoo import models, api, _
from odoo.addons.base.models.ir_mail_server import extract_rfc2822_addresses
from odoo.exceptions import ValidationError, UserError

import re


DICT_TYPE_ERROR = {
    "email": "E-mail"
}


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def create(self, vals_dict):
        self.check_create_mail_dict(vals_dict)
        return super(ResPartner, self).create(vals_dict)

    def write(self, vals):
        for rec in self:
            rec.check_create_mail_dict(vals, rec.id)
        return super(ResPartner, self).write(vals)

    @api.onchange("email")
    def check_email(self):
        if self.email:
            message = self.check_create_mail_dict({"email": self.email}, self.id.origin, False)
            if message:
                self.email = False
                return {
                    "warning": {
                        "title": "Attenzione!",
                        "message": message
                    }
                }

    def check_create_mail_dict(self, vals, id=None, raise_error=True):
        mail_dict = self.get_mail_dict(vals)
        message = self.check_uniqueness_mail(mail_dict, "res.partner", id, False, raise_error)
        if message:
            return message
        mail_list = self.check_email_validity(mail_dict, raise_error)
        return self._get_email_validity_message(mail_list)

    @api.model
    def get_mail_dict(self, vals):
        if not vals.get("email", False):
            return {}
        if not self.env["ir.config_parameter"].sudo().get_param("fl_partner_email.validity_mail"):
            return {}
        return {"email": vals.get("email", False)}

    def check_email_validity(self, vals, raise_error=True):
        """ re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,13}|[0-9]{1,3})(\\]?)$", value) re per validare il formato delle email
        re.match("^.*[,; ]+.*$", value) -> re per trovare se sono stati inseriti più indirizzi email, separati dai caratteri [,; ], all'interno di una stessa riga
        re.match("^.*[@]+.*[@]+.*$", value) -> re per trovare gli indirizzi email contenenti due occorrenze del caratter @
        extract_rfc2822_addresses(value) -> re usata dal validatore odoo prima di mandare la mail """
        mail_list = []
        if self.env["ir.config_parameter"].sudo().get_param("fl_partner_email.validity_mail", False):
            for mail in vals:
                if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,13}|[0-9]{1,3})(\\]?)$",
                            vals[mail]) == None or \
                        re.match("^.*[,; ]+.*$", vals[mail]) != None or \
                        re.match("^.*[@]+.*[@]+.*$", vals[mail]) != None or \
                        not extract_rfc2822_addresses(vals[mail]):
                    mail_list.append(vals[mail])
            if mail_list and raise_error:
                raise ValidationError(self._get_email_validity_message(mail_list))
            elif mail_list and not raise_error:
                return mail_list

    @api.model
    def check_uniqueness_mail(self, mail_dict, model_name, check_id=None, parent_id=False, raise_error=True):
        if not mail_dict or not model_name:
            return False
        mail_type_error = []
        for uniqueness_mail_model in self.get_uniqueness_mail_models():
            uniqueness_mail_model_obj = self.env[uniqueness_mail_model]
            for mail_type, value in mail_dict.items():
                domain = uniqueness_mail_model_obj.get_uniqueness_mail_domain(mail_type, value, model_name, check_id, parent_id)
                if uniqueness_mail_model_obj.search_count(domain) == 0:
                    continue
                mail_type_error.append(DICT_TYPE_ERROR[mail_type])
            if not mail_type_error:
                continue
            error = _("There is already another contact with same %s") % ", ".join(mail_type_error)
            if raise_error:
                raise ValidationError(error)
            else:
                return error
        return False

    @api.model
    def get_uniqueness_mail_models(self):
        return ["res.partner"]

    @api.model
    def get_uniqueness_mail_domain(self, mail_type, value, model_name, check_id, parent_id=False):
        domain = [(mail_type, "=", value)]
        if model_name == self._name and check_id:
            domain.append(("id", "!=", check_id))
        return domain

    @api.model
    def _get_email_validity_message(self, mail_list):
        if mail_list:
            string_mail = "\n".join(mail_list)
            return _("Hai inserito %s mail senza validità. \n\n%s" % (len(mail_list), string_mail))