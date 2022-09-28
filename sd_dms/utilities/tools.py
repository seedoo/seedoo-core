# Copyright 2020-2022 Flosslab S.r.l.
# Copyright 2017-2019 MuK IT GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import mimetypes
import os

from odoo import models
from odoo.tools.mimetypes import guess_mimetype


class UtilityTools(models.AbstractModel):
    _name = "sd.dms.utility_tools"
    _description = "Seedoo Utility"

    @staticmethod
    def compute_extension(filename=None, mimetype=None, binary=None):
        extension = filename and os.path.splitext(filename)[1][1:].strip().lower()
        if not extension and mimetype:
            extension = mimetypes.guess_extension(mimetype)[1:].strip().lower()
        if not extension and binary:
            mimetype = guess_mimetype(binary, default="")
            extension = mimetypes.guess_extension(mimetype)[1:].strip().lower()
        return extension
