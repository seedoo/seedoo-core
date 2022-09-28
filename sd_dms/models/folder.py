# Copyright 2020-2022 Flosslab S.r.l.
# Copyright 2017-2019 MuK IT GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, fields, api, _
from odoo.tools import human_size
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


SELECTION_STATE = [
    ("attiva", "Attiva"),
    ("archiviata", "Archiviata")
]


class Folder(models.Model):
    _name = "sd.dms.folder"
    _description = "Folder"
    _rec_name = "path_name"

    # se si modificano i campi dell'ordinamento di default è necessario aggiornare il relativo indice definito nell'init
    _order = "path_name asc, id asc"

    #_rec_name = "path_name"

    _inherit = ["fl.security", "mail.thread", "sd.dms.thumbnail"]

    _parent_field = "parent_folder_id"
    _parent_model = "sd.dms.folder"

    _parent_store = True
    _parent_name = "parent_folder_id"

    _parent_path_sudo = False
    _parent_path_store = False

    _name_path_context = "dms_directory_show_path"

    _sql_constraints = [
        ('folder_unique',
         'UNIQUE(name,parent_folder_id)',
         'A folder with this name already exists in the directory'),
    ]

    @api.model
    def _get_parent_folder_id_domain(self):
        domain = [('perm_create', '=', True)]

        # se l'utente non ha il gruppo group_sd_dms_administrator allora da interfaccia non può creare cartelle
        # all'interno di una structure folder
        if not self.env.user.has_group("sd_dms.group_sd_dms_administrator"):
            domain.append(('structure_folder', '!=', True))
        return domain

    name = fields.Char(
        string="Name",
        required=True,
        tracking=True
    )

    company_id = fields.Many2one(
        string="Company",
        related="storage_id.company_id"
    )

    state = fields.Selection(
        string="State",
        selection=SELECTION_STATE,
        readonly=True,
        default="attiva",
        tracking=True
    )

    is_root_folder = fields.Boolean(
        string="Is Root Folder",
        default=False,
        tracking=True
    )

    root_storage_id = fields.Many2one(
        string="Root Storage",
        comodel_name="sd.dms.storage",
        tracking=True
    )

    parent_path = fields.Char(
        string="Parent Path",
        tracking=True
    )

    storage_id = fields.Many2one(
        string="Storage",
        comodel_name="sd.dms.storage",
        compute="_compute_storage_id",
        readonly=True,
        store=True
    )

    path_name = fields.Char(
        string="Path Name",
        compute="_compute_path_name",
        readonly=True,
        store=True
    )

    parent_folder_id = fields.Many2one(
        string="Parent Folder",
        comodel_name="sd.dms.folder",
        domain=lambda self: self._get_parent_folder_id_domain(),
        ondelete="cascade",
        auto_join=True,
        index=True,
        tracking=True
    )

    structure_folder = fields.Boolean(
        string="Structure Folder",
        default=False
    )

    child_folder_ids = fields.One2many(
        string="Subfolders",
        comodel_name="sd.dms.folder",
        inverse_name="parent_folder_id"
    )

    document_ids = fields.One2many(
        string="Document",
        comodel_name="sd.dms.document",
        inverse_name="folder_id"
    )

    category_id = fields.Many2one(
        string="Category",
        comodel_name="sd.dms.category",
        tracking=True
    )

    tag_ids = fields.Many2many(
        string="Tags",
        comodel_name="sd.dms.tag",
        relation="sd_dms_folder_tag_rel",
        column1="folder_id",
        column2="tag_id",
    )

    size = fields.Integer(
        string="Size",
        compute="_compute_size",
        readonly=True
    )

    human_size = fields.Char(
        string="Size",
        compute="_compute_human_size"
    )

    count_folders = fields.Integer(
        string="Count Subfolders",
        compute="_compute_count_folders",
        readonly=True
    )

    count_documents = fields.Integer(
        string="Count Documets",
        compute="_compute_count_documents",
        readonly=True

    )

    count_elements = fields.Integer(
        string="Count Elements",
        compute="_compute_count_elements",
        readonly=True
    )

    color = fields.Integer(
        string="Color",
        default=0
    )

    acl_ids = fields.Many2many(
        string="Acl",
        comodel_name="sd.dms.folder.acl",
        relation="sd_dms_folder_acl_rel",
        column1="folder_id",
        column2="acl_id",
        domain=[("create_system", "=", False)]
    )

    system_acl_ids = fields.Many2many(
        string="System Acl",
        comodel_name="sd.dms.folder.acl",
        relation="sd_dms_folder_acl_rel",
        column1="folder_id",
        column2="acl_id",
        domain=[("create_system", "=", True)],
        readonly=True
    )

    inherit_acl_ids = fields.Many2many(
        string="Inherit Acl",
        comodel_name="sd.dms.folder.acl",
        relation="sd_dms_folder_acl_inherit_rel",
        column1="folder_id",
        column2="acl_id",
        readonly=True
    )

    @api.depends("root_storage_id", "is_root_folder", "parent_folder_id")
    def _compute_storage_id(self):
        for rec in self:
            if rec.is_root_folder:
                rec.storage_id = rec.root_storage_id
                rec.parent_folder_id = False
            else:
                rec.storage_id = rec.parent_folder_id.storage_id

    @api.depends("child_folder_ids")
    def _compute_count_folders(self):
        for rec in self:
            rec.count_folders = len(rec.child_folder_ids)

    @api.depends("document_ids")
    def _compute_count_documents(self):
        for rec in self:
            rec.count_documents = len(rec.document_ids)

    @api.depends("document_ids", "child_folder_ids")
    def _compute_count_elements(self):
        for rec in self:
            rec.count_elements = rec.count_folders + rec.count_documents

    def _compute_size(self):
        document_obj = self.env["sd.dms.document"].sudo()
        for record in self:
            size = 0
            if isinstance(record.id, int):
                documents = document_obj.search_read(
                    domain=[("folder_id", "child_of", record.id)],
                    fields=["size"],
                )
                size = sum(rec.get("size", 0) for rec in documents)
            record.size = size

    @api.depends("name", "is_root_folder", "parent_folder_id", "parent_folder_id.path_name")
    def _compute_path_name(self):
        for rec in self:
            if not rec.parent_folder_id and rec.is_root_folder:
                path_name = rec.name
            else:
                path_name = "%s/%s" % (rec.parent_folder_id.path_name, rec.name)
            rec.path_name = path_name

    @api.model
    def get_extension(self):
        return "folder.svg"

    @api.depends("size")
    def _compute_human_size(self):
        for rec in self:
            rec.human_size = human_size(rec.size)

    @api.constrains("inherit_acl", "parent_folder_id")
    def _check_inherit_acl(self):
        for rec in self:
            if rec.inherit_acl and rec.sudo().parent_folder_id.is_root_folder:
                raise ValidationError(
                    _("Folders cannot inherit acl from a root folder!")
                )

    @api.model
    def _delete_structure_folder(self, structure_folder):
        try:
            if structure_folder and not structure_folder.document_ids:
                structure_folder.sudo().unlink()
        except Exception as e:
            _logger.error(e)

    ####################################################################################################################
    # CRUD
    ####################################################################################################################

    def init(self):
        # inserimento dell'indice utilizzato nella ricerca della tree e kanban view: è importante inserire sia il l'id
        # che il campo usato nella property _order per definire l'ordinamento di default usato nel modello: i due campi
        # in questione verranno utilizzati nella query di ricerca di visibilità
        sd_dms_folder_id_path_name_index = "sd_dms_folder_id_path_name_index"
        self.env.cr.execute("""
            SELECT indexname FROM pg_indexes WHERE indexname = '%s'
        """ % sd_dms_folder_id_path_name_index)
        if not self.env.cr.fetchone():
            self.env.cr.execute("""
                CREATE INDEX %s ON sd_dms_folder USING btree (id, path_name)
            """ % sd_dms_folder_id_path_name_index)
        sd_dms_folder_path_name_id_index = "sd_dms_folder_path_name_id_index"
        self.env.cr.execute("""
            SELECT indexname FROM pg_indexes WHERE indexname = '%s'
        """ % sd_dms_folder_path_name_id_index)
        if not self.env.cr.fetchone():
            self.env.cr.execute("""
                CREATE INDEX %s ON sd_dms_folder USING btree (path_name, id)
            """ % sd_dms_folder_path_name_id_index)

    def unlink(self):
        for rec in self:
            if rec.document_ids:
                raise ValidationError(
                    _("The folder '%s' cannot be deleted because it is associated with documents!" % rec.name)
                )
        return super(Folder, self).unlink()

    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        default["name"] = _("Copy of %s") % self.name
        return super(Folder, self).copy(default=default)

    ####################################################################################################################
    # Security
    ####################################################################################################################

    @api.model
    def skip_security(self):
        result = super(Folder, self).skip_security()
        result = result or self.env.user.has_group("sd_dms.group_sd_dms_manager")
        return result