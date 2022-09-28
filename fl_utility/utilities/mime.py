import logging
import mimetypes
import os
import sys
from typing import Union

import magic

from odoo import models, api
from odoo.exceptions import ValidationError
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)


class MimeUtility(models.AbstractModel):
    _name = "fl.utility.mime"
    _description = "MIME Types utility"

    @api.model
    def guess_by_filename(self, filename: str = "") -> str:
        if not filename:
            raise ValidationError(_("Invalid filename"))

        file_name = os.path.basename(filename)

        mimetype = mimetypes.guess_type(file_name)
        if not mimetype:
            raise ValidationError(_("Invalid mimetype"))

        return str(mimetype[0])

    @api.model
    def guess_by_content(self, content: Union[str, bytes] = b"") -> str:
        if not content:
            raise ValidationError(_("Empty content"))

        mime = magic.Magic(mime=True)

        try:
            return mime.from_buffer(content)
        except magic.MagicException as e:
            _logger.error(f"Error guessing mimetype: {e.message}")
            raise ValidationError(_("Error guessing mimetype"))
