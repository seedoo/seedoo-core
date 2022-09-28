# Copyright 2020-2022 Flosslab S.r.l.
# Copyright 2017-2019 MuK IT GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, fields, api
from odoo.addons.fl_partner_pa.models.inherit_res_partner import SELECTION_COMPANY_SUBJECT_TYPE, SELECTION_CONTACT_PA_TYPE

SELECTION_TYPOLOGY = [
    ("recipient", "Recipient"),
    ("sender", "Sender"),
    ("other_subjects", "Other subjects"),
]

SELECTION_COMPANY_TYPE = [
    ("person", "Individual"),
    ("company", "Company")
]


class Contact(models.Model):
    _name = "sd.dms.contact"
    _rec_name = "name"

    _description = "Contact"

    typology = fields.Selection(
        string="Typology",
        selection=SELECTION_TYPOLOGY,
        default=SELECTION_TYPOLOGY[0][0]
    )

    parent_id = fields.Many2one(
        string="Parent",
        comodel_name="res.partner"
    )

    partner_image = fields.Image(
        string="Partner Image",
        related="partner_id.image_128"
    )

    company_type = fields.Selection(
        string="Category",
        selection=SELECTION_COMPANY_TYPE,
        default=SELECTION_COMPANY_TYPE[0][0]
    )

    company_subject_type = fields.Selection(
        string="Company typology",
        selection=SELECTION_COMPANY_SUBJECT_TYPE
    )

    contact_pa_type = fields.Selection(
        string="Company PA typology",
        selection=SELECTION_CONTACT_PA_TYPE
    )

    parent_person = fields.Char(
        string="Parent person"
    )

    parent_person_company_type = fields.Selection(
        string="Parent person type",
        selection=SELECTION_COMPANY_TYPE,
        required=False
    )

    parent_person_company_subject_type = fields.Selection(
        string="Parent person company typology",
        selection=SELECTION_COMPANY_SUBJECT_TYPE
    )

    parent_person_contact_pa_type = fields.Selection(
        string="Parent person company PA typology",
        selection=SELECTION_CONTACT_PA_TYPE
    )

    view_company_type = fields.Selection(
        string="Type in view",
        selection=SELECTION_COMPANY_TYPE,
        compute="_compute_view_fields"
    )

    view_company_subject_type = fields.Selection(
        string="Company typology in view",
        selection=SELECTION_COMPANY_SUBJECT_TYPE,
        compute="_compute_view_fields"
    )

    view_contact_pa_type = fields.Selection(
        string="Company PA typology in view",
        selection=SELECTION_CONTACT_PA_TYPE,
        compute="_compute_view_fields"
    )

    name_amm = fields.Char(
        string="IPA name"
    )

    cod_amm = fields.Char(
        string="IPA code"
    )

    email_amm = fields.Char(
        string="E-mail"
    )

    pec_mail_amm = fields.Char(
        string="Pec Mail"
    )

    name_aoo = fields.Char(
        string="Homogeneous Organizational Area"
    )

    cod_aoo = fields.Char(
        string="Unique AOO code"
    )

    name_ou = fields.Char(
        string="Organizational Unit"
    )

    cod_ou = fields.Char(
        string="Unique UO code"
    )

    digital_domicile_ids = fields.One2many(
        string="Digital domiciles",
        inverse_name="contact_id",
        comodel_name="sd.dms.contact.digital.domicile"
    )

    email_address_ids = fields.One2many(
        string="Other e-mail PEC addresses",
        inverse_name="contact_id",
        comodel_name="sd.dms.contact.email.address"
    )

    contact_pa_name = fields.Char(
        string="Contact",
        compute="_compute_view_fields"
    )

    contact_pa_email = fields.Char(
        string="E-mail",
        compute="_compute_view_fields"
    )

    contact_pa_pec_mail = fields.Char(
        string="Pec Mail",
        compute="_compute_view_fields"
    )

    partner_id = fields.Many2one(
        string="Contact",
        comodel_name="res.partner"
    )

    name = fields.Char(
        string="Name"
    )

    fiscalcode = fields.Char(
        string="Fiscalcode"
    )

    vat = fields.Char(
        string="VAT"
    )

    street = fields.Char(
        string="Street",
    )

    street2 = fields.Char(
        string="Street 2",
    )

    zip = fields.Char(
        string="ZIP"
    )

    city = fields.Char(
        string="City"
    )

    state_id = fields.Many2one(
        string="State",
        comodel_name="res.country.state"
    )

    country_id = fields.Many2one(
        string="Country",
        comodel_name="res.country"
    )

    function = fields.Char(
        string="Working Position"
    )

    email = fields.Char(
        string="E-mail"
    )

    pec_mail = fields.Char(
        string="Pec Mail"
    )

    phone = fields.Char(
        string="Phone"
    )

    fax = fields.Char(
        string="Fax"
    )

    mobile = fields.Char(
        string="Mobile"
    )

    website = fields.Char(
        string="Website"
    )

    title = fields.Many2one(
        string="Title",
        comodel_name="res.partner.title"
    )

    notes = fields.Text(
        string="Notes"
    )

    category_id = fields.Many2many(
        string="Tags",
        comodel_name="res.partner.category",
        relation="sd_dms_contact_res_partner_category_rel",
        column1="contact_id",
        column2="category_id"
    )

    save_partner = fields.Boolean(
        string="Save in contacts",
        default=False
    )

    is_private_company = fields.Boolean(
        string="Is a private company",
        compute="_compute_company_values",
        store=True
    )

    is_pa = fields.Boolean(
        string="Is a PA/GPS",
        compute="_compute_company_values",
        store=True
    )

    is_amm = fields.Boolean(
        string="Is a PA",
        compute="_compute_company_values",
        store=True
    )

    is_gps = fields.Boolean(
        string="Is a GPS",
        compute="_compute_company_values",
        store=True
    )

    is_aoo = fields.Boolean(
        string="Is a AOO",
        compute="_compute_company_values",
        store=True
    )

    is_uo = fields.Boolean(
        string="Is a UO",
        compute="_compute_company_values",
        store=True
    )

    parent_pa_name = fields.Char(
        string="Parent PA name",
        compute="_compute_parents_name"
    )

    parent_gps_name = fields.Char(
        string="Parent GPS name",
        compute="_compute_parents_name"
    )

    parent_aoo_name = fields.Char(
        string="Parent AOO name",
        compute="_compute_parents_name"
    )

    parent_uo_name = fields.Char(
        string="Parent UO name",
        compute="_compute_parents_name"
    )

    digital_domicile_ids_html = fields.Char(
        string="Digital domicile list html",
        compute="_compute_digital_domicile_ids_html"
    )

    email_address_ids_html = fields.Char(
        string="Other e-mail PEC addresse list html",
        compute="_compute_email_address_ids_html"
    )

    document_recipient_ids = fields.Many2many(
        string="Document recipients",
        comodel_name="sd.dms.document",
        relation="sd_dms_document_contact_recipient_rel",
        readonly=True
    )

    document_other_subjects_ids = fields.Many2many(
        string="Document other subjects",
        comodel_name="sd.dms.document",
        relation="sd_dms_document_contact_other_subjects_rel",
        readonly=True
    )

    document_sender_ids = fields.Many2many(
        string="Document sender",
        comodel_name="sd.dms.document",
        relation="sd_dms_document_contact_sender_rel",
        readonly=True
    )

    display_name = fields.Char(
        string="Path name",
        compute="_compute_display_name",
        store=True
    )

    @api.depends("company_subject_type", "contact_pa_type", "partner_id", "partner_id.display_name", "parent_id", "parent_id.display_name")
    def _compute_display_name(self):
        for contact in self:
            if contact.partner_id:
                contact.display_name = contact.partner_id.display_name
                return
            if contact.company_type == "person":
                if contact.parent_id:
                   contact.display_name = ",".join([contact.parent_id.display_name, contact.name])
                else:
                    contact.display_name = contact.name
            elif contact.is_private_company:
                if contact.parent_id:
                   contact.display_name = ",".join([contact.parent_id.display_name, contact.name])
                else:
                    contact.display_name = contact.name
            else:
                display_name_list = []
                if contact.parent_pa_name:
                    display_name_list.append(contact.parent_pa_name)
                if contact.parent_gps_name:
                    display_name_list.append(contact.parent_gps_name)
                if contact.parent_aoo_name:
                    display_name_list.append(contact.parent_aoo_name)
                if contact.parent_uo_name:
                    display_name_list.append(contact.parent_uo_name)
                display_name_list.append(contact.name)
                contact.display_name = ",".join(display_name_list)

    @api.depends("company_subject_type", "contact_pa_type")
    def _compute_company_values(self):
        for rec in self:
            rec.is_private_company = rec.company_subject_type=="private"
            rec.is_pa = rec.company_subject_type in ["pa", "gps"]
            rec.is_amm = rec.company_subject_type=="pa" and not rec.contact_pa_type
            rec.is_gps = rec.company_subject_type=="gps" and not rec.contact_pa_type
            rec.is_aoo = rec.company_subject_type in ["pa", "gps"] and rec.contact_pa_type=="aoo"
            rec.is_uo = rec.company_subject_type in ["pa", "gps"] and rec.contact_pa_type=="uo"

    def _compute_parents_name(self):
        for rec in self:
            rec.parent_pa_name = False
            rec.parent_gps_name = False
            rec.parent_aoo_name = False
            rec.parent_uo_name = False
            if rec.is_amm or rec.is_gps or rec.is_private_company:
                continue
            if rec.is_aoo or rec.is_uo:
                if rec.company_subject_type == "pa":
                    rec.parent_pa_name = rec.name_amm
                elif rec.company_subject_type == "gps":
                    rec.parent_gps_name = rec.name_amm
                if rec.is_uo:
                    rec.parent_aoo_name = rec.name_aoo
            elif rec.company_type=="person" and \
                    rec.parent_person_company_type=="company" and \
                    rec.parent_person_company_subject_type in ["pa", "gps"]:
                if rec.parent_person_company_subject_type == "pa":
                    rec.parent_pa_name = rec.name_amm
                elif rec.parent_person_company_subject_type == "gps":
                    rec.parent_gps_name = rec.name_amm
                if rec.parent_person_contact_pa_type == "aoo":
                    rec.parent_aoo_name = rec.name_aoo
                elif rec.parent_person_contact_pa_type == "uo":
                    rec.parent_aoo_name = rec.name_aoo
                    rec.parent_uo_name = rec.name_ou

    def _compute_view_fields(self):
        for rec in self:
            self.compute_view_fields(rec)

    @api.model
    def compute_view_fields(self, rec):
        if rec.company_type == "person" and \
                rec.parent_person_company_type == "company" and \
                rec.parent_person_company_subject_type in ["pa", "gps"]:
            rec.view_company_type = rec.parent_person_company_type
            rec.view_company_subject_type = rec.parent_person_company_subject_type
            rec.view_contact_pa_type = rec.parent_person_contact_pa_type
            rec.contact_pa_name = rec.name
            rec.contact_pa_email = rec.email
            rec.contact_pa_pec_mail = rec.pec_mail
        else:
            rec.view_company_type = rec.company_type
            rec.view_company_subject_type = rec.company_subject_type
            rec.view_contact_pa_type = rec.contact_pa_type
            rec.contact_pa_name = False
            rec.contact_pa_email = False
            rec.contact_pa_pec_mail = False

    def _compute_digital_domicile_ids_html(self):
        for rec in self:
            digital_domicile_name_list = []
            if rec.is_pa or rec.is_gps or rec.is_aoo or rec.is_uo:
                for digital_domicile in rec.digital_domicile_ids:
                    digital_domicile_name_list.append(digital_domicile.display_name)
            rec.digital_domicile_ids_html = ", ".join(digital_domicile_name_list)

    def _compute_email_address_ids_html(self):
        for rec in self:
            email_address_name_list = []
            if rec.is_uo:
                for email_address in rec.email_address_ids:
                    email_address_name_list.append(email_address.display_name)
            rec.email_address_ids_html = ", ".join(email_address_name_list)

    def document_unlink_contact(self):
        self.ensure_one()
        self.unlink()

    def create_partner_from_contact(self):
        res_partner_obj = self.env["res.partner"]
        partner = res_partner_obj.create(self.get_values_partner_contact(self))
        self.partner_id = partner.id
        return partner.id

    @api.model
    def get_values_partner_contact(self, record, partner_values=True):
        field_list = self._get_partner_contact_field_list()
        vals = {}
        if partner_values:
            # Contact -> Partner
            for field in field_list:
                vals.update(
                    {field: self._get_field(record[field])}
                )
            vals.update({
                "display_name": record.name,
                "category_id": [(6, 0, record.category_id.ids)],
            })
        else:
            # Partner -> Contact
            for field in field_list:
                vals.update(
                    {field: self._get_field(record[field])}
                )
            vals["partner_id"] = record.id
            vals["category_id"] = [(6, 0, record.category_id.ids)]
            vals["view_company_type"] = record.company_type
            vals["view_company_subject_type"] = record.company_subject_type
            vals["view_contact_pa_type"] = record.contact_pa_type
            vals["parent_person_company_type"] = False
            vals["parent_person_company_subject_type"] = False
            vals["parent_person_contact_pa_type"] = False
            vals["email_amm"] = False
            vals["pec_mail_amm"] = False
            vals["name_amm"] = False
            vals["name_aoo"] = False
            vals["name_ou"] = False
            vals["contact_pa_name"] = False
            vals["contact_pa_email"] = False
            vals["contact_pa_pec_mail"] = False
            vals["parent_person"] = False
            # se il partner ha come padre un contatto della pa allora il nuovo record diventa il padre
            if record.company_type == "person" and record.parent_id and record.parent_id.is_pa:
                vals["contact_pa_name"] = record.name
                vals["contact_pa_email"] = record.email
                vals["contact_pa_pec_mail"] = record.pec_mail
                record = record.parent_id
                vals["view_company_type"] = record.company_type
                vals["view_company_subject_type"] = record.company_subject_type
                vals["view_contact_pa_type"] = record.contact_pa_type
                vals["parent_person_company_type"] = record.company_type
                vals["parent_person_company_subject_type"] = record.company_subject_type
                vals["parent_person_contact_pa_type"] = record.contact_pa_type
            elif record.company_type == "person" and record.parent_id and record.parent_id.is_private_company:
                vals["parent_person_company_type"] = record.parent_id.company_type
                vals["parent_person_company_subject_type"] = record.parent_id.company_subject_type
                vals["parent_person"] = record.parent_id.name
            # se il partner è una persona o un'azienda privata non dobbiamo valorizzare i campi della pa presenti nel
            # contatto ma non presenti sul partner (name_amm, cod_amm, name_aoo, cod_aoo, name_ou, cod_ou)
            if not record.is_company or record.is_private_company:
                return vals
            digital_domicile_list = []
            email_address_list = []
            if record.is_amm or record.is_gps:
                vals["email_amm"] = record.email
                vals["pec_mail_amm"] = record.pec_mail
                vals["name_amm"] = record.name
                vals["cod_amm"] = record.cod_amm
            if record.is_aoo:
                vals["email_amm"] = record.amministrazione_id.email
                vals["pec_mail_amm"] = record.amministrazione_id.pec_mail
                vals["name_amm"] = record.amministrazione_id.name
                vals["cod_amm"] = record.amministrazione_id.cod_amm
                vals["name_aoo"] = record.name
                vals["cod_aoo"] = record.cod_aoo
                digital_domicile_list = record.aoo_digital_domicile_ids
            if record.is_uo:
                vals["email_amm"] = record.amministrazione_id.email
                vals["pec_mail_amm"] = record.amministrazione_id.pec_mail
                vals["name_amm"] = record.aoo_id.amministrazione_id.name
                vals["cod_amm"] = record.aoo_id.amministrazione_id.cod_amm
                vals["name_aoo"] = record.aoo_id.name
                vals["cod_aoo"] = record.aoo_id.cod_aoo
                vals["name_ou"] = record.name
                vals["cod_ou"] = record.cod_ou
                digital_domicile_list = record.uo_digital_domicile_ids
                email_address_list = record.email_address_ids
            digital_domicile_ids = [(6, 0, [])]
            for digital_domicile in digital_domicile_list:
                digital_domicile_vals = self.env["sd.dms.contact.digital.domicile"].get_values_partner_contact_digital_domicile(digital_domicile)
                digital_domicile_ids.append((0, 0, digital_domicile_vals))
            vals["digital_domicile_ids"] = digital_domicile_ids
            email_address_ids = [(6, 0, [])]
            for email_address in email_address_list:
                email_address_vals = self.env["sd.dms.contact.email.address"].get_values_partner_contact_email_address(email_address)
                email_address_ids.append((0, 0, email_address_vals))
            vals["email_address_ids"] = email_address_ids
        return vals

    @api.model
    def _get_partner_contact_field_list(self):
        field_list = [
            "name",
            "display_name",
            "parent_id",
            "company_type",
            "company_subject_type",
            "contact_pa_type",
            "cod_amm",
            "cod_aoo",
            "cod_ou",
            "website",
            "vat",
            "function",
            "fiscalcode",
            "street",
            "street2",
            "zip",
            "city",
            "state_id",
            "country_id",
            "email",
            "pec_mail",
            "phone",
            "mobile",
            "title"
        ]
        return field_list

    @api.model
    def _get_field(self, field):
        if isinstance(field, models.Model):
            return field.id
        return field
