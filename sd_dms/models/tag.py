# Copyright 2020-2022 Flosslab S.r.l.
# Copyright 2017-2019 MuK IT GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, api, fields


class Tag(models.Model):
    _name = "sd.dms.tag"
    _description = "Tag"

    _sql_constraints = [
        ('name_uniq', 'unique (name, category_id)', "Tag name already exists!"),
    ]

    name = fields.Char(
        string='Name',
        required=True,
    )

    category_id = fields.Many2one(
        string='Category',
        comodel_name='sd.dms.category',
        ondelete='set null'
    )

    folder_ids = fields.Many2many(
        string='Folders',
        comodel_name='sd.dms.folder',
        relation='sd_dms_folder_tag_rel',
        column1='tag_id',
        column2='folder_id',
        readonly=True)

    document_ids = fields.Many2many(
        string='Documents',
        comodel_name='sd.dms.document',
        relation='sd_dms_document_tag_rel',
        column1='tag_id',
        column2='document_id',
        readonly=True
    )

    count_folders = fields.Integer(
        compute='_compute_count_folders',
        string="Count Directories"
    )

    count_documents = fields.Integer(
        compute='_compute_count_documents',
        string="Count Files"
    )

    @api.depends('folder_ids')
    def _compute_count_folders(self):
        for rec in self:
            rec.count_folders = len(rec.folder_ids)

    @api.depends('document_ids')
    def _compute_count_documents(self):
        for rec in self:
            rec.count_documents = len(rec.document_ids)
