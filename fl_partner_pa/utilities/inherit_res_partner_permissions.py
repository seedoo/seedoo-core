from odoo import models, fields, api

SELECTION_AMM_AND_GPS_FIELD_INVISIBLE_LIST = [
    "title_invisible",
    "street2_invisible"
]

SELECTION_AOO_FIELD_INVISIBLE_LIST = [
    "company_type_invisible",
    "email_invisible",
    "title_invisible",
    "street2_invisible",
    "fiscalcode_invisible",
    "vat_invisible",
    "website_invisible"
]

SELECTION_UO_FIELD_INVISIBLE_LIST = [
    "company_type_invisible",
    "email_invisible",
    "street2_invisible",
    "title_invisible",
    "vat_invisible"
]


class ResPartner(models.Model):
    _inherit = "res.partner"

    name_invisible = fields.Boolean(
        string="field name invisible",
        compute="compute_fields_invisible"
    )

    company_type_invisible = fields.Boolean(
        string="field company_type invisible",
        compute="compute_fields_invisible"
    )

    company_subject_type_invisible = fields.Boolean(
        string="field company_subject_type invisible",
        compute="compute_fields_invisible"
    )

    amministrazione_id_invisible = fields.Boolean(
        string="field amministrazione_id invisible",
        compute="compute_fields_invisible"
    )

    aoo_id_invisible = fields.Boolean(
        string="field aoo_id invisible",
        compute="compute_fields_invisible"
    )

    phone_invisible = fields.Boolean(
        string="field phone invisible",
        compute="compute_fields_invisible"
    )

    mobile_invisible = fields.Boolean(
        string="field mobile invisible",
        compute="compute_fields_invisible"
    )

    title_invisible = fields.Boolean(
        string="field title invisible",
        compute="compute_fields_invisible"
    )

    website_invisible = fields.Boolean(
        string="field website invisible",
        compute="compute_fields_invisible"
    )

    street2_invisible = fields.Boolean(
        string="field street2 invisible",
        compute="compute_fields_invisible"
    )

    fiscalcode_invisible = fields.Boolean(
        string="field fiscalcode invisible",
        compute="compute_fields_invisible"
    )

    vat_invisible = fields.Boolean(
        string="field vat invisible",
        compute="compute_fields_invisible"
    )

    category_id_invisible = fields.Boolean(
        string="field category_id invisible",
        compute="compute_fields_invisible"
    )

    email_invisible = fields.Boolean(
        string="field email invisible",
        compute="compute_fields_invisible"
    )

    lang_invisible = fields.Boolean(
        string="field lang invisible",
        compute="compute_fields_invisible"
    )

    uo_ids_invisible = fields.Boolean(
        string="field uo_ids invisible",
        compute="compute_fields_invisible"
    )

    pa_digital_domicile_ids_invisible = fields.Boolean(
        string="field pa_digital_domicile_ids invisible",
        compute="compute_fields_invisible"
    )

    aoo_digital_domicile_ids_invisible = fields.Boolean(
        string="field aoo_digital_domicile_ids_invisible invisible",
        compute="compute_fields_invisible"
    )

    uo_digital_domicile_ids_invisible = fields.Boolean(
        string="field uo_digital_domicile_ids invisible",
        compute="compute_fields_invisible"
    )

    parent_child_aoo_id_invisible = fields.Boolean(
        string="field parent_child_aoo_id invisible",
        compute="compute_fields_invisible"
    )

    parent_child_uo_id_invisible = fields.Boolean(
        string="field parent_child_uo_id invisible",
        compute="compute_fields_invisible"
    )

    @api.depends("is_amm", "is_gps", "is_aoo", "is_uo", "type", "parent_id")
    def compute_fields_invisible(self):
        for rec in self:
            rec.name_invisible = False
            rec.company_type_invisible = self.env.context.get("default_company_type_invisible", False)
            rec.company_subject_type_invisible = self.env.context.get("default_company_subject_type_invisible", False)
            rec.phone_invisible = False
            rec.mobile_invisible = False
            rec.title_invisible = False
            rec.street2_invisible = False
            rec.fiscalcode_invisible = False
            rec.vat_invisible = False
            rec.category_id_invisible = False
            rec.website_invisible = False
            rec.email_invisible = False
            rec.lang_invisible = False
            rec.amministrazione_id_invisible = True
            rec.aoo_id_invisible = True
            rec.uo_ids_invisible = True
            rec.pa_digital_domicile_ids_invisible = True
            rec.aoo_digital_domicile_ids_invisible = True
            rec.uo_digital_domicile_ids_invisible = True
            rec.parent_child_aoo_id_invisible = True
            rec.parent_child_uo_id_invisible = True
            if rec.is_private_company:
                rec._compute_fields_invisible_for_private_company()
            if rec.is_amm or rec.is_gps:
                rec._compute_fields_invisible_for_amm_and_gps()
            elif rec.is_aoo:
                rec._compute_fields_invisible_for_aoo()
            elif rec.is_uo:
                rec._compute_fields_invisible_for_uo()
            elif rec.type=="contact" and rec.env.context.get("default_parent_id", False):
                default_parent = self.browse(rec.env.context.get("default_parent_id", False))
                if default_parent and (default_parent.is_amm or default_parent.is_gps):
                    rec.parent_child_aoo_id_invisible = False
                    rec.parent_child_uo_id_invisible = False
                elif default_parent and (default_parent.is_aoo):
                    rec.parent_child_uo_id_invisible = False

    def _compute_fields_invisible_for_private_company(self):
        self.uo_ids_invisible = False

    def _compute_fields_invisible_for_amm_and_gps(self):
        for field in SELECTION_AMM_AND_GPS_FIELD_INVISIBLE_LIST:
            self[field] = True
        if self.create_date and self.aoo_ids.ids:
            self.uo_ids_invisible = False
            self.pa_digital_domicile_ids_invisible = False

    def _compute_fields_invisible_for_aoo(self):
        for field in SELECTION_AOO_FIELD_INVISIBLE_LIST:
            self[field] = True
        self.amministrazione_id_invisible = False
        self.aoo_digital_domicile_ids_invisible = False

    def _compute_fields_invisible_for_uo(self):
        for field in SELECTION_UO_FIELD_INVISIBLE_LIST:
            self[field] = True
        if self.create_date and self.aoo_id:
            self.uo_digital_domicile_ids_invisible = False
        if self.amministrazione_id and self.amministrazione_id.is_private_company:
            self.amministrazione_id_invisible = False
        elif self.amministrazione_id and (self.amministrazione_id.is_amm or self.amministrazione_id.is_gps):
            self.aoo_id_invisible = False

    @api.onchange("pec_mail")
    def _compute_fl_pec_mail_invisible(self):
        super(ResPartner, self)._compute_fl_pec_mail_invisible()
        for rec in self:
            if rec.fl_pec_mail_invisible:
                continue
            rec.fl_pec_mail_invisible = rec.is_aoo or rec.is_uo