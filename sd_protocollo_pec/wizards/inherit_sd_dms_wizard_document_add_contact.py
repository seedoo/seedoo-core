from odoo import models, fields, api


class InheritSdDmsWizardDocumentAddContact(models.TransientModel):
    _inherit = "sd.dms.wizard.document.add.contact"

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
        string="Use in sending"
    )

    contact_pa_pec_mail_use_in_sending = fields.Boolean(
        string="Use in sending"
    )

    use_in_sending_invisible = fields.Boolean(
        string="field use_in_sending_invisible",
        compute="_compute_field_use_in_sending_invisible"
    )

    @api.depends("view_company_type", "view_company_subject_type", "email_use_in_sending")
    def _compute_field_email_required(self):
        for rec in self:
            is_person_or_company = rec.view_company_type == "person" or (rec.view_company_type == "company" and rec.view_company_subject_type == "private")
            rec.email_required = rec.email_use_in_sending if is_person_or_company else False

    @api.depends("view_company_type", "view_company_subject_type", "pec_mail_use_in_sending")
    def _compute_field_pec_mail_required(self):
        for rec in self:
            is_person_or_company = rec.view_company_type == "person" or (rec.view_company_type == "company" and rec.view_company_subject_type == "private")
            rec.pec_mail_required = rec.pec_mail_use_in_sending if is_person_or_company else False

    @api.depends("view_company_type", "view_company_subject_type", "email_amm_use_in_sending")
    def _compute_field_email_amm_required(self):
        for rec in self:
            is_pa = rec.view_company_type == "company" and rec.view_company_subject_type in ["pa", "gps"]
            rec.email_amm_required = rec.email_amm_use_in_sending if is_pa else False

    @api.depends("view_company_type", "view_company_subject_type", "pec_mail_amm_use_in_sending")
    def _compute_field_pec_mail_amm_required(self):
        for rec in self:
            is_pa = rec.view_company_type == "company" and rec.view_company_subject_type in ["pa", "gps"]
            rec.pec_mail_amm_required = rec.pec_mail_amm_use_in_sending if is_pa else False

    @api.depends("view_company_type", "view_company_subject_type", "contact_pa_email_use_in_sending")
    def _compute_field_contact_pa_email_required(self):
        for rec in self:
            is_contact_pa = rec.view_company_type == "company" and rec.view_company_subject_type in ["pa", "gps"] and rec.contact_pa_name
            rec.contact_pa_email_required = rec.contact_pa_email_use_in_sending if is_contact_pa else False

    @api.depends("view_company_type", "view_company_subject_type", "contact_pa_pec_mail_use_in_sending")
    def _compute_field_contact_pa_pec_mail_required(self):
        for rec in self:
            is_contact_pa = rec.view_company_type == "company" and rec.view_company_subject_type in ["pa", "gps"] and rec.contact_pa_name
            rec.contact_pa_pec_mail_required = rec.contact_pa_pec_mail_use_in_sending if is_contact_pa else False

    @api.depends("typology")
    def _compute_field_use_in_sending_invisible(self):
        for rec in self:
            rec.use_in_sending_invisible = False if rec.typology=="recipient" else True

    def _get_contact_person_or_company_private_vals(self, contact_id):
        contact_vals = super(InheritSdDmsWizardDocumentAddContact, self)._get_contact_person_or_company_private_vals(contact_id)
        contact_vals["email_use_in_sending"] = self.email_use_in_sending
        contact_vals["pec_mail_use_in_sending"] = self.pec_mail_use_in_sending
        contact_vals["email_amm_use_in_sending"] = False
        contact_vals["pec_mail_amm_use_in_sending"] = False
        return contact_vals

    def _get_contact_pa_vals(self, contact_id):
        contact_vals = super(InheritSdDmsWizardDocumentAddContact, self)._get_contact_pa_vals(contact_id)
        is_person = contact_vals.get("company_type", "company") == "person"
        contact_vals["email_use_in_sending"] = self.contact_pa_email_use_in_sending if is_person else self.email_use_in_sending
        contact_vals["pec_mail_use_in_sending"] = self.contact_pa_pec_mail_use_in_sending if is_person else self.pec_mail_use_in_sending
        contact_vals["email_amm_use_in_sending"] = self.email_amm_use_in_sending
        contact_vals["pec_mail_amm_use_in_sending"] = self.pec_mail_amm_use_in_sending
        return contact_vals

    @api.onchange("partner_id", "email")
    def _onchange_sending_email(self):
        if not self.email:
            self.email_use_in_sending = False

    @api.onchange("partner_id", "pec_mail")
    def _onchange_sending_pec_mail(self):
        if not self.pec_mail:
            self.pec_mail_use_in_sending = False

    @api.onchange("partner_id", "email_amm")
    def _onchange_sending_email_amm(self):
        if not self.email_amm:
            self.email_amm_use_in_sending = False

    @api.onchange("partner_id", "pec_mail_amm")
    def _onchange_sending_pec_mail_amm(self):
        if not self.pec_mail_amm:
            self.pec_mail_amm_use_in_sending = False

    @api.onchange("partner_id", "contact_pa_email")
    def _onchange_sending_contact_pa_email(self):
        if not self.contact_pa_email:
            self.contact_pa_email_use_in_sending = False

    @api.onchange("partner_id", "contact_pa_pec_mail")
    def _onchange_sending_contact_pa_pec_mail(self):
        if not self.contact_pa_pec_mail:
            self.contact_pa_pec_mail_use_in_sending = False



class InheritSdDmsWizardDocumentAddContactDigitalDomicile(models.TransientModel):
    _inherit = "sd.dms.wizard.document.add.contact.digital.domicile"

    use_in_sending = fields.Boolean(
        string="Use in sending",
        default=False
    )



class InheritSdDmsWizardDocumentAddContactEmailAddress(models.TransientModel):
    _inherit = "sd.dms.wizard.document.add.contact.email.address"

    use_in_sending = fields.Boolean(
        string="Use in sending",
        default=False
    )