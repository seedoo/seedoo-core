from odoo import models, api, _


class ResPartnerEmailMixin(models.AbstractModel):
    _name = "res.partner.email.mixin"
    _description = "Partner e-mail mixin"
    _partner_id_field = "partner_id"

    @api.model
    def create(self, vals):
        self.check_email_address_dict(
            type=vals.get("type", False),
            email_address=vals.get("email_address", False),
            partner_id=vals.get(self._partner_id_field, False)
        )
        return super(ResPartnerEmailMixin, self).create(vals)

    def write(self, vals):
        for rec in self:
            self.check_email_address_dict(
                type=vals.get("type", rec.type),
                email_address=vals.get("email_address", rec.email_address),
                partner_id=vals.get(self._partner_id_field, rec[self._partner_id_field].id),
                id=rec.id
            )
        return super(ResPartnerEmailMixin, self).write(vals)

    @api.onchange("type", "email_address")
    def onchange_type_email_address(self):
        if not self.type or not self.email_address:
            return False
        message = self.check_email_address_dict(
            type=self.type,
            email_address=self.email_address,
            id=self.id.origin,
            partner_id=self[self._partner_id_field].id.origin if self[self._partner_id_field] else False,
            raise_error=False
        )
        if not message:
            return False
        self.email_address = False
        return {
            "warning": {
                "title": _("Warning!"),
                "message": message
            }
        }

    @api.model
    def check_email_address_dict(self, type, email_address, id=None, partner_id=False, raise_error=True):
        if not type or not email_address:
            return False
        partner_obj = self.env["res.partner"]
        vals = {type: email_address}
        mail_dict = partner_obj.get_mail_dict(vals)
        message = partner_obj.check_uniqueness_mail(mail_dict, self._name, id, partner_id, raise_error)
        if message:
            return message
        mail_list = partner_obj.check_email_validity(mail_dict, raise_error)
        return partner_obj._get_email_validity_message(mail_list)
