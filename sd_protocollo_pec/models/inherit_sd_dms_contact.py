from odoo import models, fields, api


class InheritSdDmsContact(models.Model):

    _inherit = "sd.dms.contact"

    email_use_in_sending = fields.Boolean(
        string="Use in sending"
    )

    pec_mail_use_in_sending = fields.Boolean(
        string="Use in sending"
    )

    email_amm_use_in_sending = fields.Boolean(
        string="Use in sending"
    )

    pec_mail_amm_use_in_sending = fields.Boolean(
        string="Use in sending"
    )

    contact_pa_email_use_in_sending = fields.Boolean(
        string="Use in sending",
        compute="_compute_view_fields"
    )

    contact_pa_pec_mail_use_in_sending = fields.Boolean(
        string="Use in sending",
        compute="_compute_view_fields"
    )

    @api.model
    def compute_view_fields(self, rec):
        super(InheritSdDmsContact, self).compute_view_fields(rec)
        if rec.company_type == "person" and \
                rec.parent_person_company_type == "company" and \
                rec.parent_person_company_subject_type in ["pa", "gps"]:
            rec.contact_pa_email_use_in_sending = rec.email_use_in_sending
            rec.contact_pa_pec_mail_use_in_sending = rec.pec_mail_use_in_sending
        else:
            rec.contact_pa_email_use_in_sending = False
            rec.contact_pa_pec_mail_use_in_sending = False


    def get_email_list(self, with_type=False):
        self.ensure_one()
        email_list = []
        email_with_type_list = []
        # domicili digitali, altri indirizzi email possono essere usati solo per i contatti di tipo PA, GPS, AOO, UO
        if self.is_pa or (self.company_type=="person" and self.parent_person_company_subject_type in ["pa", "gps"]):
            for digital_domicile in self.digital_domicile_ids:
                if not digital_domicile.use_in_sending or not digital_domicile.email_address or digital_domicile.email_address in email_list:
                    continue
                email_list.append(digital_domicile.email_address.lower())
                email_with_type_list.append({
                    "email": digital_domicile.email_address.lower(),
                    "type": "digital_domicile"
                })
            for email_address in self.email_address_ids:
                if not email_address.use_in_sending or not email_address.email_address or email_address.email_address in email_list:
                    continue
                email_list.append(email_address.email_address.lower())
                email_with_type_list.append({
                    "email": email_address.email_address.lower(),
                    "type": "email_address"
                })
            if self.contact_pa_email and self.contact_pa_email_use_in_sending and not (self.contact_pa_email in email_list):
                email_list.append(self.contact_pa_email.lower())
                email_with_type_list.append({
                    "email": self.contact_pa_email.lower(),
                    "type": "email"
                })
            if self.contact_pa_pec_mail and self.contact_pa_pec_mail_use_in_sending and not (self.contact_pa_pec_mail in email_list):
                email_list.append(self.contact_pa_pec_mail.lower())
                email_with_type_list.append({
                    "email": self.contact_pa_pec_mail.lower(),
                    "type": "pec_mail"
                })
            if self.email_amm and self.email_amm_use_in_sending and not (self.email_amm in email_list):
                email_list.append(self.email_amm.lower())
                email_with_type_list.append({
                    "email": self.email_amm.lower(),
                    "type": "email"
                })
            if self.pec_mail_amm and self.pec_mail_amm_use_in_sending and not (self.pec_mail_amm in email_list):
                email_list.append(self.pec_mail_amm.lower())
                email_with_type_list.append({
                    "email": self.pec_mail_amm.lower(),
                    "type": "pec_mail"
                })
        else:
            if self.email and self.email_use_in_sending and not (self.email in email_list):
                email_list.append(self.email.lower())
                email_with_type_list.append({
                    "email": self.email.lower(),
                    "type": "email"
                })
            if self.pec_mail and self.pec_mail_use_in_sending and not (self.pec_mail in email_list):
                email_list.append(self.pec_mail.lower())
                email_with_type_list.append({
                    "email": self.pec_mail.lower(),
                    "type": "pec_mail"
                })
        if with_type:
            return email_with_type_list
        else:
            return email_list