# Copyright 2020-2022 Flosslab S.r.l.
# Copyright 2017-2019 MuK IT GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class Base(models.AbstractModel):

    _inherit = "base"

    def unlink(self):
        for name in self._fields:
            field = self._fields[name]
            if field.type == "file" and field.store:
                for record in self:
                    path = record.with_context({"path": True})[name]
                    if path:
                        field._add_to_checklist(path, self.env.cr.dbname)
        super(Base, self).unlink()
