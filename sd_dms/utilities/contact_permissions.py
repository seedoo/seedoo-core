# Copyright 2020-2022 Flosslab S.r.l.
# Copyright 2017-2019 MuK IT GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, fields, api


class ContactPermissions(models.Model):
    _inherit = "sd.dms.contact"

    button_edit_contact_invisible = fields.Boolean(
        string="button document add contact sender invisible",
        compute="_compute_button_edit_contact_invisible"
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

    def _compute_button_edit_contact_invisible(self):
        for rec in self:
            rec.button_edit_contact_invisible = False
            # il button di modifica contatti è invisibile se almeno uno dei documenti associati è in sola lettura
            documents = self.env["sd.dms.document"].search([
                "|",
                ("recipient_ids", "=", rec.id),
                ("sender_ids", "=", rec.id),
            ])
            for document in documents:
                if document.field_readonly:
                    rec.button_edit_contact_invisible = True
                    break

            documents = self.env["sd.dms.document"].search([
                ("other_subjects_ids", "=", rec.id)
            ])
            for document in documents:
                if not document.perm_write:
                    rec.button_edit_contact_invisible = True
                    break

    def _compute_fields_invisible(self):
        for rec in self:
            self.compute_fields_invisible(rec)

    @api.model
    def compute_fields_invisible(self, rec):
        rec.name_invisible = False
        rec.parent_person_invisible = False
        rec.phone_invisible = False
        rec.mobile_invisibile = False
        rec.title_invisible = False
        rec.street_invisible = False
        rec.function_invisible = False
        rec.fiscalcode_invisible = False
        rec.category_id_invisible = False
        rec.vat_invisible = False
        rec.email_invisible = False
        rec.pec_mail_invisible = False
        rec.name_amm_invisible = False
        rec.person_or_company_invisible = False
        rec.amm_invisible = False
        rec.aoo_invisible = False
        rec.uo_invisible = False
        rec.contact_pa_invisible = False
        # calcolo delle possibili casistiche di contatti
        is_person = rec.view_company_type == "person"
        is_company_private = rec.view_company_type == "company" and rec.view_company_subject_type in ["private"]
        is_pa = rec.view_company_type == "company" and rec.view_company_subject_type in ["pa", "gps"]
        # campi invisibili se si tratta di un contatto di una persona
        if is_person:
            rec.name_amm_invisible = True
            rec.amm_invisible = True
            rec.aoo_invisible = True
            rec.uo_invisible = True
            rec.contact_pa_invisible = True
        # campi invisibili se si tratta di un contatto di una azienda privata
        elif is_company_private:
            rec.parent_person_invisible = True
            rec.title_invisible = True
            rec.function_invisible = True
            rec.name_amm_invisible = True
            rec.amm_invisible = True
            rec.aoo_invisible = True
            rec.uo_invisible = True
            rec.contact_pa_invisible = True
        # campi invisibili se si tratta di un contatto di una pubblica amministrazione (pa, gps, aoo, uo)
        elif is_pa:
            rec.name_invisible = True
            rec.parent_person_invisible = True
            rec.title_invisible = True
            rec.function_invisible = True
            rec.street_invisible = True
            rec.phone_invisible = True
            rec.mobile_invisibile = True
            rec.fiscalcode_invisible = True
            rec.vat_invisible = True
            rec.person_or_company_invisible = True
        else:
            rec.name_invisible = True
            rec.parent_person_invisible = True
            rec.name_amm_invisible = True
            rec.person_or_company_invisible = True
            rec.amm_invisible = True
            rec.aoo_invisible = True
            rec.uo_invisible = True
            rec.contact_pa_invisible = True
            rec.category_id_invisible = True