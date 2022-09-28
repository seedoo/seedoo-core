# Copyright 2020-2022 Flosslab S.r.l.
# Copyright 2017-2019 MuK IT GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, fields


class IrModelField(models.Model):
    _inherit = "ir.model.fields"

    ttype = fields.Selection(
        selection_add=[("file", "file")],
        ondelete={
            'file': 'cascade',
        })
