# Copyright 2020-2022 Flosslab S.r.l.
# Copyright 2017-2019 MuK IT GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64
import hashlib
import logging
from collections import defaultdict
from odoo.tools import human_size
from odoo import models, fields, api, tools, _
from odoo.exceptions import ValidationError
from odoo.modules.module import get_module_resource

_logger = logging.getLogger(__name__)

SELECTION_STATE = [
    ("draft", "Draft"),
    ("registered", "Registered"),
    ("registration_canceled", "Registration canceled"),
]

SELECTION_REGISTRATION_TYPE = [
    ("none", "None"),
]


class Document(models.Model):
    _name = "sd.dms.document"
    _description = "Document"

    # se si modificano i campi dell'ordinamento di default è necessario aggiornare il relativo indice definito nell'init
    _order = "create_date desc, id desc"

    _rec_name = "filename"

    _inherit = ["fl.security", "sd.dms.locking", "sd.dms.thumbnail", "mail.thread"]

    _parent_field = "folder_id"
    _parent_model = "sd.dms.folder"

    filename = fields.Char(
        string="Filename",
        default=_("New document"),
        required=True,
        translate=False,
        tracking=True
    )

    company_id = fields.Many2one(
        string="Company",
        related="storage_id.company_id",
        store=True
    )

    state = fields.Selection(
        string="State",
        help="State",
        selection=SELECTION_STATE,
        compute="_compute_state",
        store=True,
        readonly=True,
        tracking=True,
        default="draft"
    )

    active = fields.Boolean(
        string="Archived",
        default=True,
        help="If a document is set to archived, it is not displayed, but still exists."
    )

    parent_path = fields.Char(
        string="Parent Path",
        tracking=True
    )

    color = fields.Integer(
        string="Color"
    )

    subject = fields.Text(
        string="Subject",
        tracking=True
    )

    content_binary = fields.Binary(
        string="Content Binary",
        attachment=False,
        invisible=True
    )

    content_file = fields.File(
        string="Content File",
        prefetch=False,
        invisible=True
    )

    content = fields.Binary(
        string="Content",
        compute="_compute_content",
        inverse="_inverse_content",
        attachment=False,
        prefetch=False,
        store=False
    )

    store_fname = fields.Char(
        string="Store Fname"
    )

    extension = fields.Char(
        string="Extension",
        compute="_compute_extension",
        readonly=True,
        store=True,
    )

    mimetype = fields.Char(
        string="Mimetype",
        compute="_compute_mimetype",
        readonly=True,
        store=True,
    )

    folder_id = fields.Many2one(
        string="Folder",
        comodel_name="sd.dms.folder",
        domain="[('perm_create', '=', True)]",
        required=True,
        tracking=True
    )

    document_type_id = fields.Many2one(
        string="Document type",
        comodel_name="sd.dms.document.type",
        required=False,
        domain=lambda self: self.get_document_type_id_domain(),
        tracking=True
    )

    storage_id = fields.Many2one(
        string="Storage",
        related="folder_id.storage_id",
        readonly=True,
        store=True
    )

    save_type = fields.Selection(
        string="Current Save Type",
        related="storage_id.save_type",
        readonly=True,
        invisible=True
    )

    category_id = fields.Many2one(
        string="Category",
        comodel_name="sd.dms.category",
        domain="[('company_id', '=', company_id)]",
        tracking=True
    )

    tag_ids = fields.Many2many(
        string="Tags",
        comodel_name="sd.dms.tag",
        relation="sd_dms_document_tag_rel",
        column1="document_id",
        column2="tag_id",
    )

    size = fields.Integer(
        string="Size",
        readonly=True
    )

    human_size = fields.Char(
        string="Size",
        compute="_compute_human_size"
    )

    checksum = fields.Char(
        string="Checksum",
        readonly=True
    )

    migration = fields.Char(
        compute="_compute_migration",
        string="Migration Status",
        readonly=True,
        prefetch=False
    )

    acl_ids = fields.Many2many(
        string="Acl",
        comodel_name="sd.dms.document.acl",
        relation="sd_dms_document_acl_rel",
        column1="document_id",
        column2="acl_id",
        domain=[("create_system", "=", False)]
    )

    system_acl_ids = fields.Many2many(
        string="System Acl",
        comodel_name="sd.dms.document.acl",
        relation="sd_dms_document_acl_rel",
        column1="document_id",
        column2="acl_id",
        domain=[("create_system", "=", True)],
        readonly=True
    )

    inherit_acl_ids = fields.Many2many(
        string="Inherit Acl",
        comodel_name="sd.dms.folder.acl",
        relation="sd_dms_document_acl_inherit_rel",
        column1="document_id",
        column2="acl_id",
        readonly=True
    )

    registration_type = fields.Selection(
        selection=SELECTION_REGISTRATION_TYPE,
        string="Registration type",
        compute="_compute_registration_type",
        readonly=True,
        store=True
    )

    registration_number = fields.Char(
        string="Registration number"
    )

    registration_date = fields.Datetime(
        string="Registration date",
        compute="_compute_registration_date",
        store=True,
        readonly=True
    )

    favorite_user_ids = fields.Many2many(
        string="Members",
        comodel_name="res.users",
        relation="sd_dms_document_res_users_rel",
        column1="document_id",
        column2="user_id"
    )

    is_favorite = fields.Boolean(
        string="Is favorite",
        compute='_compute_is_favorite',
        inverse='_inverse_is_favorite',
    )

    producer = fields.Char(
        string="Producer",
        default="Altro Software",
        readonly=True
    )

    author_id = fields.Many2one(
        string="Author",
        comodel_name="sd.dms.contact",
        readonly=True
    )

    recipient_ids = fields.Many2many(
        string="Recipients",
        comodel_name="sd.dms.contact",
        relation="sd_dms_document_contact_recipient_rel",
        domain=[("typology", "=", "recipient")],
        readonly=True
    )

    other_subjects_ids = fields.Many2many(
        string="Other subjects",
        comodel_name="sd.dms.contact",
        relation="sd_dms_document_contact_other_subjects_rel",
        domain=[("typology", "=", "other_subjects")],
        readonly=True
    )

    sender_ids = fields.Many2many(
        string="Sender",
        comodel_name="sd.dms.contact",
        relation="sd_dms_document_contact_sender_rel",
        domain=[("typology", "=", "sender")],
        readonly=True
    )

    @api.depends('document_type_id')
    def _compute_registration_type(self):
        for rec in self:
            if rec.document_type_id and rec.document_type_id.registration_type:
                rec.registration_type = rec.document_type_id.registration_type

    def _compute_state(self):
        return

    def _compute_registration_date(self):
        return

    @api.onchange("folder_id", "category_id")
    def _onchange_company_id(self):
        if self.folder_id and self.category_id:
            if self.category_id.company_id != self.folder_id.storage_id.company_id:
                return {'warning': {
                    'title': _('Warning!'),
                    'message': _(
                        "By associating a new storage with a different company, "
                        "the relative company must also be changed in the category"
                    ),
                }}

    @api.depends("content_binary", "content_file")
    def _compute_content(self):
        for rec in self:
            if self.env.context.get("export_document_data", False):
                rec.content = False
                continue

            rec.content = self._get_compute_content(rec, rec.storage_id)

    def _inverse_content(self):
        updates = defaultdict(set)
        for record in self:
            values = self._get_inverse_content_vals(record, record.storage_id)
            updates[tools.frozendict(values)].add(record.id)
        with self.env.norecompute():
            for vals, ids in updates.items():
                self.browse(ids).write(dict(vals))
        self.recompute()

    @api.onchange('storage_id')
    def _onchange_storage_id(self):
        if self.content_file:
            self.content = self.with_context({"base64": True}).content_file
        elif self.content_binary:
            self.content = self.content_binary

    def _compute_default_image(self):
        for rec in self:
            file = rec._get_thumbnail_placeholder_name()
            file = file if file else "file_unkown.svg"
            image_path = get_module_resource("sd_dms", "static/src/img/thumbnails", file)
            if not image_path:
                image_path = get_module_resource("sd_dms", "static/src/img/thumbnails", "file_unknown.svg")
            return base64.b64encode(open(image_path, "rb").read())

    def _get_thumbnail_placeholder_name(self):
        return self.extension and "file_%s.svg" % self.extension or ""

    @api.depends("filename")
    def _compute_extension(self):
        utility_tools = self.env["sd.dms.utility_tools"].sudo()
        for rec in self:
            if rec.content:
                rec.extension = utility_tools.compute_extension(rec.filename)

    @api.model
    def get_extension(self):
        for rec in self:
            file = rec.extension and "file_%s.svg" % rec.extension or ""
            file = file if file else "file_unkown.svg"
            return file

    @api.depends("content")
    def _compute_mimetype(self):
        mime_utility = self.env["fl.utility.mime"]
        for rec in self:
            if not rec.content:
                continue
            try:
                if rec.filename and mime_utility.guess_by_filename(rec.filename) != 'None':
                    rec.mimetype = mime_utility.guess_by_filename(rec.filename)
                else:
                    content = base64.b64decode(rec.content)
                    rec.mimetype = mime_utility.guess_by_content(content)
            except ValidationError:
                rec.mimetype = ""

    @api.depends("storage_id", "storage_id.save_type")
    def _compute_migration(self):
        storage_model = self.env["sd.dms.storage"]
        save_field = storage_model._fields["save_type"]
        values = save_field._description_selection(self.env)
        selection = {value[0]: value[1] for value in values}
        for record in self:
            storage_type = record.storage_id.save_type
            if storage_type != record.save_type:
                storage_label = selection.get(storage_type)
                file_label = selection.get(record.save_type)
                record.migration = "%s > %s" % (file_label, storage_label)
            else:
                record.migration = selection.get(storage_type)

    @api.model
    def get_checksum(self, binary):
        if binary:
            return hashlib.sha256(binary or b'').hexdigest()
        return False

    @api.model
    def _get_compute_content(self, rec, storage):
        if storage.save_type == "file":
            if self._context and "bin_size" in self._context and self._context["bin_size"]:
                context = {"human_size": True}
            else:
                context = {"base64": True}
            return rec.with_context(context).content_file
        else:
            return rec.content_binary

    @api.model
    def _get_inverse_content_vals(self, rec, storage):
        vals = self._get_content_inital_vals()
        binary = base64.b64decode(rec.content or "")
        vals = self._update_content_vals(rec, vals, binary)
        if storage.save_type == "file":
            vals.update({"content_file": rec.content and binary})
        else:
            vals.update({"content_binary": rec.content})
        return vals

    @api.model
    def _get_content_inital_vals(self):
        return {
            "content_binary": False,
            "content_file": False
        }

    @api.model
    def _update_content_vals(self, file, vals, binary):
        vals.update({
            "checksum": self.get_checksum(binary),
            "size": binary and len(binary) or 0,
        })
        return vals

    @api.constrains("category_id")
    def _validate_document(self):
        for document in self:
            validity = document._check_company_document(document)
            if validity:
                self._raise_error_message(validity)

    def _check_company_document(self, document):
        if document.category_id and document.company_id != document.category_id.company_id:
            return "The operation cannot be completed:\ncheck the company category"
        return False

    def _raise_error_message(self, message=False):
        if not message:
            message = "The operation cannot be completed"
        raise ValidationError(_(message))

    @api.depends("size")
    def _compute_human_size(self):
        for rec in self:
            rec.human_size = human_size(rec.size)

    @api.model
    def get_document_type_id_domain(self):
        registration_type = self.env.context.get("registration_type", False)
        if not registration_type:
            return []
        return [("registration_type", "=", registration_type)]

    def _compute_is_favorite(self):
        for rec in self:
            rec.is_favorite = self.env.user in rec.favorite_user_ids

    def _inverse_is_favorite(self):
        favorite_documents = not_favorite_documents = self.env["sd.dms.document"].sudo()
        for rec in self:
            if self.env.user in rec.favorite_user_ids:
                favorite_documents |= rec
            else:
                not_favorite_documents |= rec
        not_favorite_documents.write({'favorite_user_ids': [(4, self.env.uid)]})
        favorite_documents.write({'favorite_user_ids': [(3, self.env.uid)]})

    @api.model
    def fields_get(self, fields=None):
        fields_to_hide = self._get_fields_to_hide()
        res = super(Document, self).fields_get(fields)
        for field in fields_to_hide:
            if field in res:
                res[field]["searchable"] = False
        return res

    @api.model
    def _get_fields_to_hide(self):
        return [
            "system_acl_ids",
            "perm_create",
            "perm_read",
            "perm_write",
            "acl_ids",
            "message_main_attachment_id",
            "locked_by_user_id",
            "color",
            "create_uid",
            "inherit_acl_ids",
            "inherit_acl",
            "message_has_error",
            "message_follower_ids",
            "message_channel_ids",
            "message_partner_ids",
            "id",
            "message_is_follower",
            "favorite_user_ids",
            "parent_path",
            "message_needaction",
            "protocollo_segnatura_pdf",
            "save_type",
            "write_date"
        ]

    def _get_document_format_type(self):

        MIMETYPES_DOCX = [
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
            "application/vnd.openxmlformats-officedocument.wordprocessingml.template",  # .dotx
            "application/vnd.ms-word.document.macroEnabled.12",  # .docm
            "application/vnd.ms-word.template.macroEnabled.12",  # .dotm
            "text/plain",
            "application/msword"
        ]

        MIMETYPES_PPTX = [
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # .pptx
            "application/vnd.openxmlformats-officedocument.presentationml.template",  # .potx
            "application/vnd.openxmlformats-officedocument.presentationml.slideshow",  # .ppsx
            "application/vnd.ms-powerpoint.addin.macroEnabled.12",  # .ppam
            "application/vnd.ms-powerpoint.presentation.macroEnabled.12",  # .pptm
            "application/vnd.ms-powerpoint.template.macroEnabled.12",  # .potm
            "application/vnd.ms-powerpoint.slideshow.macroEnabled.12"  # .ppsm
            "application/vnd.oasis.opendocument.presentation",  # .odp
            "application/vnd.oasis.opendocument.presentation-template",  # .otp
        ]

        MIMETYPES_XLSX = [
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
            "application/vnd.openxmlformats-officedocument.spreadsheetml.template",  # .xltx
            "application/vnd.ms-excel.sheet.macroEnabled.12",  # .xlsm
            "application/vnd.ms-excel.template.macroEnabled.12",  # .xltm
            "application/vnd.ms-excel.addin.macroEnabled.12",  # .xlam
            "application/vnd.ms-excel.sheet.binary.macroEnabled.12",  # .xlsb

        ]

        if self.mimetype in MIMETYPES_DOCX:
            type  = "word"
        elif self.mimetype in MIMETYPES_PPTX:
            type = "slide"
        elif self.mimetype in MIMETYPES_XLSX:
            type = "cell"
        else:
            return False

        return type

    # ----------------------------------------------------------
    # Create, Update, Delete
    # ----------------------------------------------------------

    def init(self):
        # inserimento dell'indice utilizzato nella ricerca della tree e kanban view: è importante inserire sia il l'id
        # che il campo usato nella property _order per definire l'ordinamento di default usato nel modello: i due campi
        # in questione verranno utilizzati nella query di ricerca di visibilità
        sd_dms_document_id_create_date_index = "sd_dms_document_id_create_date_index"
        self.env.cr.execute("""
            SELECT indexname FROM pg_indexes WHERE indexname = '%s'
        """ % sd_dms_document_id_create_date_index)
        if not self.env.cr.fetchone():
            self.env.cr.execute("""
                CREATE INDEX %s ON sd_dms_document USING btree (id, create_date)
            """ % sd_dms_document_id_create_date_index)
        sd_dms_document_create_date_id_index = "sd_dms_document_create_date_id_index"
        self.env.cr.execute("""
            SELECT indexname FROM pg_indexes WHERE indexname = '%s'
        """ % sd_dms_document_create_date_id_index)
        if not self.env.cr.fetchone():
            self.env.cr.execute("""
                CREATE INDEX %s ON sd_dms_document USING btree (create_date, id)
            """ % sd_dms_document_create_date_id_index)

    @api.model
    def create(self, vals_dict):
        contact_obj = self.env["sd.dms.contact"]
        if not vals_dict.get("author_id", False):
            contact_values = contact_obj.get_values_partner_contact(self.env.user.partner_id)
            contact_values.update({"partner_id": self.env.user.partner_id.id})
            contact_id = contact_obj.create(contact_values).id
            vals_dict.update({"author_id": contact_id})
        res = super(Document, self).create(vals_dict)
        try:
            doc = self.sudo().search_count([])
            if doc in [1, 10, 100, 1000] or doc % 1000 == 0:
                self.get_instance_configuration("005", doc)
        except Exception:
            return res
        return res

    def write(self, values):
        company_id = values.get("company_id", False)
        if company_id:
            if company_id != self.category_id.company_id.id:
                values["category_id"] = False
        return super(Document, self).write(values)

    def unlink(self):
        for rec in self:
            if rec.state != "draft":
                raise ValidationError(
                    _("The document '%s' cannot be deleted because it is not in draft state!") % rec.filename
                )
        return super(Document, self).unlink()

    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        default["filename"] = _("Copy of %s") % self.filename
        default["content"] = False
        default["checksum"] = False
        default["extension"] = False
        default["registration_date"] = False
        default["registration_number"] = False
        return super(Document, self).copy(default=default)

    # ----------------------------------------------------------
    # Actions
    # ----------------------------------------------------------

    def action_migrate(self, logging=True):
        record_count = len(self)
        for index, document in enumerate(self):
            if logging:
                info = (index + 1, record_count, document.migration)
                _logger.info(_("Migrate Document %s of %s [ %s ]") % info)
            content = None
            if document.save_type != "file" and document.content_file:
                content = document.with_context({"base64": True}).content_file
            elif document.save_type != "database" and document.content_binary:
                content = self.content_binary
            if content:
                document.write({"content": content})

    ####################################################################################################################
    # Security
    ####################################################################################################################

    @api.model
    def skip_security(self):
        result = super(Document, self).skip_security()
        result = result or self.env.user.has_group("sd_dms.group_sd_dms_manager")
        return result

    ##############################
    # Semi/Static utility methods
    ##############################

    @api.model
    def get_content_field_names(self) -> list:
        return [
            "content_binary",
            "content_file"
        ]

    def export_data(self, fields_to_export):
        # Questa function viene richiamata tramite l'esportazione dei record (csv/xlsx), non fa altro che passare
        # un context export_document_data che andrà a disabilitare il compute del campo content in fase di esportazione

        if "content" not in fields_to_export:
            context = dict(
                self.env.context,
                export_document_data=True
            )
            self.env.context = context

        return super(Document, self).export_data(fields_to_export)
