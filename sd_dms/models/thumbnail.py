# Copyright 2020-2022 Flosslab S.r.l.
# Copyright 2017-2019 MuK IT GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64

from odoo import models, fields, api
from odoo.modules.module import get_module_resource


class Thumbnail(models.AbstractModel):
    _name = "sd.dms.thumbnail"
    _description = "Seedoo Thumbnail"

    image_filename = fields.Char(
        string="Image Filename",
        compute="_compute_default_image_1920",
    )

    image_1024 = fields.Image(
        string="Image 1920",
        compute="_compute_default_image_1920",
        attachment=False,
        max_width=1024,
        max_height=1024,
    )

    @api.model
    def _compute_default_image_1920(self):
        for rec in self:
            file = rec.get_extension()
            rec.image_filename = file
            image_path = get_module_resource("sd_dms", "static/src/img/thumbnails", file)
            if not image_path:
                image_path = get_module_resource("sd_dms", "static/src/img/thumbnails", "file_unknown.svg")
            with open(image_path, "rb") as image:
                image = image.read()
            rec.image_1024 = base64.b64encode(image)
