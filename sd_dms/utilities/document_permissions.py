# Copyright 2020-2022 Flosslab S.r.l.
# Copyright 2017-2019 MuK IT GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, fields, api


class DocumentPermissions(models.Model):
    _inherit = "sd.dms.document"

    field_readonly = fields.Boolean(
        string="field readonly",
        compute="_compute_field_readonly"
    )

    folder_id_readonly = fields.Boolean(
        string="folder_id readonly",
        compute="_compute_folder_id_readonly"
    )

    document_type_id_readonly = fields.Boolean(
        string="field readonly",
        compute="_compute_document_type_id_readonly",
        default=False
    )

    registration_type_invisible = fields.Boolean(
        string="Registration type invisible",
        compute="_compute_registration_type_invisible",
        default=False
    )

    registration_number_readonly = fields.Boolean(
        string="field readonly",
        compute="_compute_registration_number_readonly"
    )

    registration_number_invisible = fields.Boolean(
        string="registration number invisible",
        compute="_compute_registration_number_invisible"
    )

    button_document_add_contact_sender_invisible = fields.Boolean(
        string="button document add contact sender invisible",
        compute="_compute_button_document_add_contact_sender_invisible"
    )

    button_document_add_other_subject_invisible = fields.Boolean(
        string="button document add other subject invisible",
        compute="_compute_button_document_add_other_subject_invisible"
    )

    button_document_add_contact_recipient_invisible = fields.Boolean(
        string="button document add contact recipient invisible",
        compute="_compute_button_document_add_contact_recipient_invisible"
    )

    def _compute_field_readonly(self):
        for rec in self:
            # - current user can modify the document when:
            # - current user has the perm_write permission
            # - document state in draft
            field_readonly = True
            if rec.perm_write and rec.state == "draft":
                field_readonly = False
            rec.field_readonly = field_readonly

    def _compute_folder_id_readonly(self):
        for rec in self:
            rec.folder_id_readonly = not rec.perm_write

    def _compute_document_type_id_readonly(self):
        for rec in self:
            rec.document_type_id_readonly = rec.field_readonly

    @api.onchange('registration_type')
    def _compute_registration_type_invisible(self):
        for rec in self:
            rec.registration_type_invisible = not rec.registration_type or rec.registration_type == "none"

    @api.onchange('document_type_id')
    def _compute_registration_number_readonly(self):
        for rec in self:
            rec.registration_number_readonly = rec.field_readonly

    @api.onchange('registration_type')
    def _compute_registration_number_invisible(self):
        for rec in self:
            rec.registration_number_invisible = True

    def _compute_button_document_add_contact_sender_invisible(self):
        for rec in self:
            # il button di aggiunta contatti per i mittenti è invisibile se almeno uno dei due casi è vero:
            # caso 1: il documento è in sola lettura
            # caso 2: il documento ha già un mittente
            caso1 = rec.field_readonly
            caso2 = len(rec.sender_ids.ids) > 0
            rec.button_document_add_contact_sender_invisible = caso1 or caso2

    def _compute_button_document_add_other_subject_invisible(self):
        for rec in self:
            # il button di aggiunta contatti per i altri soggetti è invisibile se almeno uno dei casi è vero:
            # caso 1: il documento è in sola lettura
            caso1 = rec.perm_write
            rec.button_document_add_other_subject_invisible = not caso1

    def _compute_button_document_add_contact_recipient_invisible(self):
        for rec in self:
            # il button di aggiunta contatti per i destinatari è invisibile se almeno uno dei due casi è vero:
            # caso 1: il documento è in sola lettura
            caso1 = rec.field_readonly
            rec.button_document_add_contact_recipient_invisible = caso1