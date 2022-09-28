# Copyright 2020-2022 Flosslab S.r.l.
# Copyright 2017-2019 MuK IT GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, fields


class Category(models.Model):
    _name = "sd.dms.category"
    _description = "Category"

    name = fields.Char(
        string="Name",
        required=True,
    )

    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        default=lambda self: self.env.company.id
    )

    active = fields.Boolean(
        string="Is Active",
        default=True
    )

    parent_category_id = fields.Many2one(
        string="Parent Category",
        comodel_name="sd.dms.category",
    )

    child_category_ids = fields.One2many(
        string="Child Categories",
        comodel_name="sd.dms.category",
        inverse_name="parent_category_id"
    )

    parent_path = fields.Char(
        string="Parent Path",
        index=True
    )

    folder_ids = fields.One2many(
        string="Folders",
        comodel_name="sd.dms.folder",
        inverse_name="category_id",
        readonly=True
    )

    document_ids = fields.One2many(
        string="Documents",
        comodel_name="sd.dms.document",
        inverse_name="category_id",
        readonly=True
    )

    tag_ids = fields.One2many(
        string='Tags',
        comodel_name='sd.dms.tag',
        inverse_name='category_id'
    )
