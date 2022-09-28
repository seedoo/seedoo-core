# Copyright 2020-2022 Flosslab S.r.l.
# Copyright 2017-2019 MuK IT GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, fields, api, _
from odoo.exceptions import AccessError


SELECTION_SAVE_TYPE = [
    ("file", "Filestore"),
    ("database", "Database")
]

class Storage(models.Model):
    _name = "sd.dms.storage"
    _description = "Storage"

    name = fields.Char(
        string="Name",
        required=True
    )

    save_type = fields.Selection(
        selection=SELECTION_SAVE_TYPE,
        string="Save Type",
        default="file",
        required=True,
        help="The save type is used to determine how a file is saved by the system. If you change this setting, you can migrate existing files manually by triggering the action."
    )

    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        default=lambda self: self.env.company.id
    )

    root_folder_ids = fields.One2many(
        string="Root Folders",
        comodel_name="sd.dms.folder",
        inverse_name="root_storage_id",
    )

    folder_ids = fields.One2many(
        string="Folders",
        comodel_name="sd.dms.folder",
        inverse_name="storage_id",
        readonly=True,
    )

    document_ids = fields.One2many(
        string="Documents",
        comodel_name="sd.dms.document",
        inverse_name="storage_id",
        readonly=True
    )

    count_storage_folders = fields.Integer(
        string="Count Directories",
        compute="_compute_count_storage_folders",
    )

    count_storage_documents = fields.Integer(
        string="Count Files",
        compute="_compute_count_storage_documents"
    )

    @api.depends("folder_ids")
    def _compute_count_storage_folders(self):
        for rec in self:
            rec.count_storage_folders = len(rec.folder_ids)

    @api.depends("document_ids")
    def _compute_count_storage_documents(self):
        for rec in self:
            rec.count_storage_documents = len(rec.document_ids)

    def action_storage_migrate(self):
        if not self.env.user.has_group("sd_dms.group_sd_dms_manager"):
            raise AccessError(_("Only managers can execute this action."))
        documents = self.env["sd.dms.document"].with_context(active_test=False).sudo()
        for record in self:
            if record.save_type == "file":
                domain = ["&", ("content_file", "=", False), ("storage_id", "=", record.id)]
            elif record.save_type == "database":
                domain = ["&", ("content_binary", "=", False), ("storage_id", "=", record.id)]
            documents |= documents.search(domain)
        documents.action_migrate()