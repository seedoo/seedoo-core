# Copyright 2020-2022 Flosslab S.r.l.
# Copyright 2017-2019 MuK IT GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, fields, api
from ..models.contact import SELECTION_TYPOLOGY, SELECTION_COMPANY_TYPE
from odoo.addons.fl_partner_pa.models.inherit_res_partner import SELECTION_COMPANY_SUBJECT_TYPE, SELECTION_CONTACT_PA_TYPE
from odoo.addons.fl_partner_pa.models.res_partner_digital_domicile import SELECTION_EMAIL_ADDRESS_TYPE as SELECTION_EMAIL_ADDRESS_TYPE_DIGITAL_DOMICILE
from odoo.addons.fl_partner_pa.models.res_partner_email_address import SELECTION_EMAIL_ADDRESS_TYPE as SELECTION_EMAIL_ADDRESS_TYPE_EMAIL_ADDRESS



class WizardDocumentAddContact(models.TransientModel):
    _name = "sd.dms.wizard.document.add.contact"
    _description = "Wizard Document Add contact"

    partner_id = fields.Many2one(
        string="Contacts",
        comodel_name="res.partner"
    )

    partner_id_updated = fields.Boolean(
        string="Partner updated",
        default=False
    )

    typology = fields.Selection(
        string="Contact typology",
        selection=SELECTION_TYPOLOGY,
        readonly=True
    )

    parent_id = fields.Many2one(
        string="Parent",
        comodel_name="res.partner"
    )

    company_type = fields.Selection(
        string="Category",
        selection=SELECTION_COMPANY_TYPE,
        required=False
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
        string="Parent person name"
    )

    view_company_type = fields.Selection(
        string="Type in view",
        selection=SELECTION_COMPANY_TYPE
    )

    view_company_subject_type = fields.Selection(
        string="Company typology in view",
        selection=SELECTION_COMPANY_SUBJECT_TYPE
    )

    view_contact_pa_type = fields.Selection(
        string="Company PA typology in view",
        selection=SELECTION_CONTACT_PA_TYPE
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
        comodel_name="sd.dms.wizard.document.add.contact.digital.domicile",
        inverse_name="wizard_id"
    )

    email_address_ids = fields.One2many(
        string="Other e-mail PEC addresses",
        comodel_name="sd.dms.wizard.document.add.contact.email.address",
        inverse_name="wizard_id"
    )

    contact_pa_name = fields.Char(
        string="Contact"
    )

    contact_pa_email = fields.Char(
        string="E-mail"
    )

    contact_pa_pec_mail = fields.Char(
        string="Pec Mail"
    )

    name = fields.Char(
        string="Name",
        required=True
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
        relation="sd_dms_wizard_document_add_contact_res_partner_category_rel",
        column1="wizard_id",
        column2="category_id"
    )

    save_partner = fields.Boolean(
        string="Save in contacts",
        help="If checked save data in contacts"
    )

    field_readonly = fields.Boolean(
        string="Field readonly",
        compute="_compute_field_readonly",
        readonly=True
    )

    name_invisible = fields.Boolean(
        string="field name invisible",
        compute="_compute_fields_invisible"
    )

    parent_person_invisible = fields.Boolean(
        string="field parent_person invisible",
        compute="_compute_fields_invisible"
    )

    phone_invisible = fields.Boolean(
        string="field phone invisible",
        compute="_compute_fields_invisible"
    )

    mobile_invisibile = fields.Boolean(
        string="field mobile invisible",
        compute="_compute_fields_invisible"
    )

    title_invisible = fields.Boolean(
        string="field title invisible",
        compute="_compute_fields_invisible"
    )

    street_invisible = fields.Boolean(
        string="field street invisible",
        compute="_compute_fields_invisible"
    )

    fiscalcode_invisible = fields.Boolean(
        string="field fiscalcode invisible",
        compute="_compute_fields_invisible"
    )

    function_invisible = fields.Boolean(
        string="field function invisible",
        compute="_compute_fields_invisible"
    )

    email_invisible = fields.Boolean(
        string="field email invisible",
        compute="_compute_fields_invisible"
    )

    pec_mail_invisible = fields.Boolean(
        string="field email invisible",
        compute="_compute_fields_invisible"
    )

    vat_invisible = fields.Boolean(
        string="field vat invisible",
        compute="_compute_fields_invisible"
    )

    name_amm_invisible = fields.Boolean(
        string="field name_amm invisible",
        compute="_compute_fields_invisible"
    )

    person_or_company_invisible = fields.Boolean(
        string="field person_or_company invisible",
        compute="_compute_fields_invisible"
    )

    amm_invisible = fields.Boolean(
        string="field amm invisible",
        compute="_compute_fields_invisible"
    )

    aoo_invisible = fields.Boolean(
        string="fields aoo invisible",
        compute="_compute_fields_invisible"
    )

    uo_invisible = fields.Boolean(
        string="fields uo invisible",
        compute="_compute_fields_invisible"
    )

    contact_pa_invisible = fields.Boolean(
        string="fields contact pa invisible",
        compute="_compute_fields_invisible"
    )

    category_id_invisible = fields.Boolean(
        string="field category_id invisible",
        compute="_compute_fields_invisible"
    )

    save_partner_invisible = fields.Boolean(
        string="save partner invisible",
        compute="_compute_fields_invisible"
    )

    email_required = fields.Boolean(
        string="field email_required",
        compute="_compute_field_email_required"
    )

    pec_mail_required = fields.Boolean(
        string="field pec_mail_required",
        compute="_compute_field_pec_mail_required"
    )

    name_amm_required = fields.Boolean(
        string="field name_amm_required",
        compute="_compute_fields_required"
    )

    cod_amm_required = fields.Boolean(
        string="field cod_amm_required",
        compute="_compute_fields_required"
    )

    email_amm_required = fields.Boolean(
        string="field email_amm_required",
        compute="_compute_field_email_amm_required"
    )

    pec_mail_amm_required = fields.Boolean(
        string="field pec_mail_amm_required",
        compute="_compute_field_pec_mail_amm_required"
    )

    name_aoo_required = fields.Boolean(
        string="field name_aoo_required",
        compute="_compute_fields_required"
    )

    cod_aoo_required = fields.Boolean(
        string="field cod_aoo_required",
        compute="_compute_fields_required"
    )

    name_ou_required = fields.Boolean(
        string="field name_ou_required",
        compute="_compute_fields_required"
    )

    cod_ou_required = fields.Boolean(
        string="field cod_ou_required",
        compute="_compute_fields_required"
    )

    contact_pa_name_required = fields.Boolean(
        string="field contact_pa_name_required",
        compute="_compute_fields_required"
    )

    contact_pa_email_required = fields.Boolean(
        string="field contact_pa_email_required",
        compute="_compute_field_contact_pa_email_required"
    )

    contact_pa_pec_mail_required = fields.Boolean(
        string="field contact_pa_name_required",
        compute="_compute_field_contact_pa_pec_mail_required"
    )

    zip_id = fields.Many2one(
        comodel_name="res.city.zip",
        string="ZIP Location",
    )

    @api.onchange("zip_id")
    def _compute_zip_id(self):
        for record in self:
            if record.zip_id.id:
                record.zip = record.zip_id.name
                record.country_id = record.zip_id.country_id.id
                record.state_id = record.zip_id.state_id.id
                record.city = record.zip_id.city_id.name

    @api.onchange("zip","country_id","state_id","city")
    def _check_fields_change(self):
        for record in self:
            if record.zip_id.id and (record.zip != record.zip_id.name or \
                record.country_id.id != record.zip_id.country_id.id or  \
                record.state_id.id != record.zip_id.state_id.id or \
                record.city != record.zip_id.city_id.name) :
                record.zip_id = False
                record.zip = False
                record.state_id = False
                record.city = False

    @api.model
    def default_get(self, fields_list):
        result = super(WizardDocumentAddContact, self).default_get(fields_list)
        contact_id = self.env.context.get("contact_id", False)
        if not contact_id:
            result["typology"] = self.env.context.get("contact_type", False)
            result["view_company_type"] = "person"
            return result
        contact = self.env["sd.dms.contact"].browse(contact_id)
        for field in fields_list:
            if field == "digital_domicile_ids":
                digital_domicile_ids = []
                for digital_domicile in contact[field]:
                    values = self.env["sd.dms.contact.digital.domicile"].get_values_partner_contact_digital_domicile(digital_domicile)
                    values["contact_digital_domicile_id"] = digital_domicile.id
                    digital_domicile_ids.append((0, 0, values))
                result[field] = digital_domicile_ids
            elif field == "email_address_ids":
                email_address_ids = []
                for email_address in contact[field]:
                    values = self.env["sd.dms.contact.email.address"].get_values_partner_contact_email_address(email_address)
                    values["contact_email_address_id"] = email_address.id
                    email_address_ids.append((0, 0, values))
                result[field] = email_address_ids
            elif field in contact:
                result[field] = contact[field]
        result["parent_id"] = contact.parent_id.id
        return result

    @api.depends("view_company_type", "view_company_subject_type", "view_contact_pa_type", "partner_id")
    def _compute_fields_invisible(self):
        contact_obj = self.env["sd.dms.contact"]
        for rec in self:
            contact_obj.compute_fields_invisible(rec)
            # il campo save_partner_invisible è stato modificato per essere sempre invisibile: non è più possibile
            # salvare un contatto in rubrica, da ora in avaenti si deve usare il campo many2one partner_id
            rec.save_partner_invisible = True
            # save_partner diventa invisibile se almeno uno dei seguenti casi è falso:
            # - caso 1: l'utente corrente non ha i permessi di salvare contatti
            # - caso 2: il contatto corrente è già associato ad un contatto in rubrica
            # - caso 3: il contatto corrente è un contatto di una pubblica amministrazione
            # caso1 = not self.env.user.has_group("base.group_partner_manager")
            # caso2 = True if rec.partner_id else False
            # caso3 = is_pa
            # if caso1 or caso2 or caso3:
            #     rec.save_partner_invisible = True

    @api.depends("view_company_type", "view_company_subject_type", "name_amm", "cod_amm", "name_aoo", "cod_aoo", "name_ou", "cod_ou",
                 "digital_domicile_ids", "email_address_ids", "contact_pa_name", "contact_pa_email", "contact_pa_pec_mail")
    def _compute_fields_required(self):
        for rec in self:
            rec.name_amm_required = False
            rec.cod_amm_required = False
            rec.name_aoo_required = False
            rec.cod_aoo_required = False
            rec.name_ou_required = False
            rec.cod_ou_required = False
            rec.contact_pa_name_required = False
            if rec.view_company_type == "person" or not rec.view_company_subject_type or rec.view_company_subject_type == "private":
                continue
            is_recipient = rec.typology == "recipient"
            if rec.contact_pa_name or rec.contact_pa_email or rec.contact_pa_pec_mail:
                rec.contact_pa_name_required = True
            if rec.name_ou or rec.cod_ou or rec.email_address_ids:
                rec.name_amm_required = is_recipient
                rec.cod_amm_required = is_recipient
                rec.name_aoo_required = is_recipient
                rec.cod_aoo_required = is_recipient
                rec.name_ou_required = True
                rec.cod_ou_required = is_recipient
            elif rec.name_aoo or rec.cod_aoo or rec.digital_domicile_ids:
                rec.name_amm_required = is_recipient
                rec.cod_amm_required = is_recipient
                rec.name_aoo_required = True
                rec.cod_aoo_required = is_recipient
            else:
                rec.name_amm_required = True
                rec.cod_amm_required = is_recipient

    @api.depends("view_company_type", "view_company_subject_type")
    def _compute_field_email_required(self):
        for rec in self:
            rec.email_required = False

    @api.depends("view_company_type", "view_company_subject_type")
    def _compute_field_pec_mail_required(self):
        for rec in self:
            rec.pec_mail_required = False

    @api.depends("view_company_type", "view_company_subject_type")
    def _compute_field_email_amm_required(self):
        for rec in self:
            rec.email_amm_required = False

    @api.depends("view_company_type", "view_company_subject_type")
    def _compute_field_pec_mail_amm_required(self):
        for rec in self:
            rec.pec_mail_amm_required = False

    @api.depends("view_company_type", "view_company_subject_type")
    def _compute_field_contact_pa_email_required(self):
        for rec in self:
            rec.contact_pa_email_required = False

    @api.depends("view_company_type", "view_company_subject_type")
    def _compute_field_contact_pa_pec_mail_required(self):
        for rec in self:
            rec.contact_pa_pec_mail_required = False

    @api.depends("partner_id")
    def _compute_field_readonly(self):
        for rec in self:
            rec.field_readonly = False if not self.partner_id else True

    @api.onchange("name_amm", "name_aoo", "name_ou")
    def _compute_pa_values(self):
        for rec in self:
            if rec.name_ou:
                rec.name = rec.name_ou
                rec.view_contact_pa_type = "uo"
            elif rec.name_aoo:
                rec.name = rec.name_aoo
                rec.view_contact_pa_type = "aoo"
            elif rec.name_amm:
                rec.name = rec.name_amm
                rec.view_contact_pa_type = False
            else:
                rec.view_contact_pa_type = False

    @api.onchange("email")
    def _onchange_email(self):
        if not self.email:
            return
        result = self.check_email_validity(mail_dict={"email": self.email}, raise_error=False)
        if result:
            self.email = False
        return result

    @api.onchange("pec_mail")
    def _onchange_pec_mail(self):
        if not self.pec_mail:
            return
        result = self.check_email_validity(mail_dict={"pec_email": self.pec_mail}, raise_error=False)
        if result:
            self.pec_mail = False
        return result

    @api.onchange("email_amm")
    def _onchange_email_amm(self):
        if not self.email_amm:
            return
        result = self.check_email_validity(mail_dict={"email": self.email_amm}, raise_error=False)
        if result:
            self.email_amm = False
        return result

    @api.onchange("pec_mail_amm")
    def _onchange_pec_mail_amm(self):
        if not self.pec_mail_amm:
            return
        result = self.check_email_validity(mail_dict={"pec_email": self.pec_mail_amm}, raise_error=False)
        if result:
            self.pec_mail_amm = False
        return result

    @api.onchange("contact_pa_email")
    def _onchange_contact_pa_email(self):
        if not self.contact_pa_email:
            return
        result = self.check_email_validity(mail_dict={"email": self.contact_pa_email}, raise_error=False)
        if result:
            self.contact_pa_email = False
        return result

    @api.onchange("contact_pa_pec_mail")
    def _onchange_contact_pa_pec_mail(self):
        if not self.contact_pa_pec_mail:
            return
        result = self.check_email_validity(mail_dict={"pec_email": self.contact_pa_pec_mail}, raise_error=False)
        if result:
            self.contact_pa_pec_mail = False
        return result

    def check_email_validity(self, mail_dict, raise_error):
        mail_list_not_valid = self.env["res.partner"].check_email_validity(mail_dict, raise_error=raise_error)
        if not mail_list_not_valid:
            return {}
        return {
            "warning": {
                "title": "Warning!",
                "message": self.env["res.partner"]._get_email_validity_message(mail_list_not_valid)
            }
        }

    @api.onchange("partner_id")
    @api.depends("partner_id.has_changed")
    def _onchange_partner_id(self):
        # il campo partner_id_updated serve per evitare di aggiornare i valori del contatto nel primo caricamento:
        # infatti se nel default_get viene settato il partner_id, automaticamente viene generato l'evento di onchange
        # su tale campo, andando a sovrascrivere i valori del primo caricamento e in particolare dei domicili digitali,
        # all'interno dei quali viene memorizzato il riferimento al contatto del domicilio digitale e l'eventuale
        # preferenza su quale utilizzare in fase di invio
        if not self.partner_id_updated:
            self.partner_id_updated = True
            return
        partner = self.partner_id
        if not partner:
            for field in self.env["sd.dms.contact"]._get_partner_contact_field_list():
                self[field] = False
            self.view_company_type = "person"
            self.view_company_subject_type = False
            self.view_contact_pa_type = False
            self.parent_person = False
            self.email_amm = False
            self.pec_mail_amm = False
            self.name_amm = False
            self.name_aoo = False
            self.name_ou = False
            self.digital_domicile_ids = [(6, 0, [])]
            self.email_address_ids = [(6, 0, [])]
            self.contact_pa_name = False
            self.contact_pa_email = False
            self.contact_pa_pec_mail = False
            self.category_id = [(6, 0, [])]
            return
        vals = self.env["sd.dms.contact"].get_values_partner_contact(partner, partner_values=False)
        for field in vals.keys():
            if field in self:
                self[field] = vals[field]
        self.save_partner = False

    def save_contact_action(self):
        documento_id = self.env.context.get("documento_id", False)
        contact_id = self.env.context.get("contact_id", False)
        return self.env["sd.dms.document"].document_save_contact(
            document_id=documento_id,
            contact_id=contact_id,
            vals=self._get_contact_vals(contact_id),
            save=self.save_partner
        )

    def _get_contact_vals(self, contact_id):
        if self.view_company_type == "company" and self.view_company_subject_type in ["pa", "gps"]:
            return self._get_contact_pa_vals(contact_id)
        else:
            return self._get_contact_person_or_company_private_vals(contact_id)

    def _get_contact_person_or_company_private_vals(self, contact_id):
        contact_vals = {
            "partner_id": self.partner_id.id,
            "parent_id": self.parent_id.id,
            "parent_person": self.parent_person,
            "typology": self.typology,
            "company_type": self.view_company_type,
            "company_subject_type": "private" if self.view_company_type=="company" else False,
            "contact_pa_type": False,
            "parent_person_company_type": "company" if self.view_company_type=="person" and self.parent_person else False,
            "parent_person_company_subject_type": "private" if self.view_company_type=="person" and self.parent_person else False,
            "parent_person_contact_pa_type": False,
            "name_amm": False,
            "cod_amm": False,
            "email_amm": False,
            "pec_mail_amm": False,
            "name_aoo": False,
            "cod_aoo": False,
            "name_ou": False,
            "cod_ou": False,
            "digital_domicile_ids": self._get_contact_digital_domicile_ids_val(contact_id, delete_all=True),
            "email_address_ids": self._get_contact_email_address_ids_val(contact_id, delete_all=True),
            "name": self.name,
            "fiscalcode": self.fiscalcode,
            "vat": self.vat,
            "street": self.street,
            "street2": self.street2,
            "zip": self.zip,
            "city": self.city,
            "state_id": self.state_id.id,
            "country_id": self.country_id.id,
            "function": self.function,
            "email": self.email,
            "pec_mail": self.pec_mail,
            "phone": self.phone,
            "fax": self.fax,
            "mobile": self.mobile,
            "website": self.website,
            "title": self.title.id,
            "category_id": [(6, 0, self.category_id.ids)],
            "notes": self.notes,
            "save_partner": self.save_partner
        }
        return contact_vals

    def _get_contact_pa_vals(self, contact_id):
        is_person = True if self.contact_pa_name else False
        delete_all_digital_domicile_ids = not (self.view_contact_pa_type == "aoo") and not (self.view_contact_pa_type == "uo")
        delete_all_email_address_ids = not (self.view_contact_pa_type == "uo")
        contact_vals = {
            "partner_id": self.partner_id.id,
            "parent_id": self.parent_id.id if is_person else False,
            "parent_person": False,
            "typology": self.typology,
            "company_type": "person" if is_person else "company",
            "company_subject_type": False if is_person else self.view_company_subject_type,
            "contact_pa_type": False if is_person else self.view_contact_pa_type,
            "parent_person_company_type": self.view_company_type if is_person else False,
            "parent_person_company_subject_type": self.view_company_subject_type if is_person else False,
            "parent_person_contact_pa_type": self.view_contact_pa_type if is_person else False,
            "name_amm": self.name_amm,
            "cod_amm": self.cod_amm,
            "email_amm": self.email_amm,
            "pec_mail_amm": self.pec_mail_amm,
            "name_aoo": self.name_aoo,
            "cod_aoo": self.cod_aoo,
            "name_ou": self.name_ou,
            "cod_ou": self.cod_ou,
            "digital_domicile_ids": self._get_contact_digital_domicile_ids_val(contact_id, delete_all=delete_all_digital_domicile_ids),
            "email_address_ids": self._get_contact_email_address_ids_val(contact_id, delete_all=delete_all_email_address_ids),
            "name": self.contact_pa_name if is_person else self.name,
            "fiscalcode": False,
            "vat": False,
            "street": False,
            "street2": False,
            "zip": False,
            "city": False,
            "state_id": False,
            "country_id": False,
            "function": False,
            "email": self.contact_pa_email if is_person else False,
            "pec_mail": self.contact_pa_pec_mail if is_person else False,
            "phone": False,
            "fax": False,
            "mobile": False,
            "website": False,
            "title": False,
            "category_id": [(6, 0, self.category_id.ids)],
            "notes": False,
            "save_partner": False
        }
        return contact_vals

    def _get_contact_digital_domicile_ids_val(self, contact_id, delete_all=False):
        digital_domicile_ids = []
        old_digital_domicile_ids = []
        if contact_id:
            old_digital_domicile_ids = self.env["sd.dms.contact.digital.domicile"].search([("contact_id", "=", contact_id)]).ids
        if delete_all:
            for old_digital_domicile_id in old_digital_domicile_ids:
                digital_domicile_ids.append((2, old_digital_domicile_id))
            return digital_domicile_ids
        update_digital_domicile_ids = []
        for digital_domicile in self.digital_domicile_ids:
            self.check_email_validity(
                mail_dict=digital_domicile._get_mail_dict(),
                raise_error=True
            )
            digital_domicile_vals = self.env["sd.dms.contact.digital.domicile"].get_values_partner_contact_digital_domicile(digital_domicile)
            if digital_domicile.contact_digital_domicile_id:
                digital_domicile_ids.append((1, digital_domicile.contact_digital_domicile_id.id, digital_domicile_vals))
                update_digital_domicile_ids.append(digital_domicile.contact_digital_domicile_id.id)
            else:
                digital_domicile_ids.append((0, 0, digital_domicile_vals))
        for old_digital_domicile_id in old_digital_domicile_ids:
            if old_digital_domicile_id not in update_digital_domicile_ids:
                digital_domicile_ids.append((2, old_digital_domicile_id))
        return digital_domicile_ids

    def _get_contact_email_address_ids_val(self, contact_id, delete_all=False):
        email_address_ids = []
        old_email_address_ids = []
        if contact_id:
            old_email_address_ids = self.env["sd.dms.contact.email.address"].search([("contact_id", "=", contact_id)]).ids
        if delete_all:
            for old_email_address_id in old_email_address_ids:
                email_address_ids.append((2, old_email_address_id))
            return email_address_ids
        update_email_address_ids = []
        for email_address in self.email_address_ids:
            self.check_email_validity(
                mail_dict=email_address._get_mail_dict(),
                raise_error=True
            )
            email_address_vals = self.env["sd.dms.contact.email.address"].get_values_partner_contact_email_address(email_address)
            if email_address.contact_email_address_id:
                email_address_ids.append((1, email_address.contact_email_address_id.id, email_address_vals))
                update_email_address_ids.append(email_address.contact_email_address_id.id)
            else:
                email_address_ids.append((0, 0, email_address_vals))
        for old_email_address_id in old_email_address_ids:
            if old_email_address_id not in update_email_address_ids:
                email_address_ids.append((2, old_email_address_id))
        return email_address_ids



class WizardDocumentAddContactDigitalDomicile(models.TransientModel):
    _name = "sd.dms.wizard.document.add.contact.digital.domicile"
    _description = "Wizard document add contact digital domicile"

    wizard_id = fields.Many2one(
        string="Wizard",
        comodel_name="sd.dms.wizard.document.add.contact",
        required=True
    )

    contact_digital_domicile_id = fields.Many2one(
        string="Contact domicile",
        comodel_name="sd.dms.contact.digital.domicile"
    )

    type = fields.Selection(
        string="Type",
        selection=SELECTION_EMAIL_ADDRESS_TYPE_DIGITAL_DOMICILE,
        required=True,
        default="pec_mail"
    )

    email_address = fields.Char(
        string="PEC mail address",
        required=True
    )

    @api.onchange("email_address")
    def _onchange_email_address(self):
        return self.env["sd.dms.wizard.document.add.contact"].check_email_validity(
            mail_dict=self._get_mail_dict(),
            raise_error=False
        )

    def _get_mail_dict(self):
        mail_dict = {}
        if self.email_address:
            mail_dict.update({"pec_mail": self.email_address})
        return mail_dict



class WizardDocumentAddContactEmailAddress(models.TransientModel):
    _name = "sd.dms.wizard.document.add.contact.email.address"
    _description = "Wizard document add contact email address"

    wizard_id = fields.Many2one(
        string="Wizard",
        comodel_name="sd.dms.wizard.document.add.contact",
        required=True
    )

    contact_email_address_id = fields.Many2one(
        string="Contact email address",
        comodel_name="sd.dms.contact.email.address"
    )

    type = fields.Selection(
        string="Type",
        selection=SELECTION_EMAIL_ADDRESS_TYPE_EMAIL_ADDRESS,
        required=True
    )

    email_address = fields.Char(
        string="E-mail address",
        required=True
    )

    @api.onchange("type", "email_address")
    def _onchange_email_address(self):
        return self.env["sd.dms.wizard.document.add.contact"].check_email_validity(
            mail_dict=self._get_mail_dict(),
            raise_error=False
        )

    def _get_mail_dict(self):
        mail_dict = {}
        if self.email_address and self.type:
            mail_dict.update({self.type: self.email_address})
        return mail_dict