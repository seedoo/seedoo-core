from odoo import models, fields, api

SELECTION_PROTOCOLLO_VISIBILITY = [
    ("xs", "XS"),
    ("s", "S"),
    ("m", "M"),
    ("l", "L"),
    ("xl", "XL")
]


class DocumentAcl(models.Model):

    _name = "sd.dms.document.acl"
    _description = "Document Acl"
    _inherit = ["sd.dms.document.acl"]


    protocollo_id = fields.Many2one(
        string="Protocollo",
        comodel_name="sd.protocollo.protocollo",
        required=False,
        ondelete="cascade"
    )

    protocollo_visibility = fields.Selection(
        string="Protocollo Visibility",
        selection=SELECTION_PROTOCOLLO_VISIBILITY,
        required=False,
    )


    _sql_constraints = [
        (
            "unique_protocollo_acl",
            "unique(protocollo_id, res_model, res_id, create_system)",
            "Ci può essere solo una acl per ogni protocollo e risorsa"
        )
    ]


    @api.model
    def create(self, values):
        protocollo_id = values.get("protocollo_id", False)
        if not protocollo_id:
            return super(DocumentAcl, self).create(values)
        values["module_id"] = self.env.ref("base.module_sd_protocollo").id
        document_list = self.env["sd.dms.document"].sudo().search_read([
            ("protocollo_id", "=", protocollo_id)
        ], ["id"])
        document_ids = []
        for document in document_list:
            document_ids.append(document["id"])
        values["document_ids"] = [(6, 0, document_ids)]
        return super(DocumentAcl, self).create(values)

    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        default["module_id"] = self.get_default_module_id().id
        default["protocollo_id"] = False
        return super(DocumentAcl, self).copy(default=default)