# Copyright 2020-2022 Flosslab S.r.l.
# Copyright 2017-2019 MuK IT GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models
from odoo.tools.translate import _


SELECTION_REGISTRATION_TYPE = [
    ("none", "None"),
]
class DocumentType(models.Model):
    _name = "sd.dms.document.type"
    _description = "Document Type"

    _sql_constraints = [
        (
            "unique",
            "UNIQUE(name)",
            _("Name must be unique!"),
        )
    ]

    name = fields.Char(
        string="Name",
        required=True,
        translate=True
    )

    active = fields.Boolean(
        string="Abilitata",
        required=True,
        default=True
    )

    registration_type = fields.Selection(
        selection=SELECTION_REGISTRATION_TYPE,
        string="Registration type",
        required=True,
        default="none"
    )



