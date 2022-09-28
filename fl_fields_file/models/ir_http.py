# Copyright 2020-2022 Flosslab S.r.l.
# Copyright 2017-2019 MuK IT GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class IrHttp(models.AbstractModel):

    _inherit = "ir.http"

    # ----------------------------------------------------------
    # Helper
    # ----------------------------------------------------------

    def _check_streamable(record, field):
        if record._fields[field].type == 'file':
            return True
        return super(IrHttp, self)._check_streamable(record, field)
