from odoo import models, fields


class Protocollo(models.Model):
    _inherit = "sd.protocollo.protocollo"

    fascicolo_acl_ids = fields.One2many(
        string="Dossier Acl inherited",
        related="documento_id.fascicolo_acl_ids",
        readonly=True
    )

    fascicolo_ids = fields.Many2many(
        string="Fascicoli",
        comodel_name="sd.fascicolo.fascicolo",
        compute="_compute_fascicolo_ids"
    )

    fascicolo_ids_count = fields.Integer(
        string="# Fascicoli",
        compute="_compute_fascicolo_ids_count",
    )

    def _compute_fascicolo_ids(self):
        for protocollo in self:
            fascicolo_ids = []
            for fascicolo in protocollo.documento_id.fascicolo_ids:
                if fascicolo.perm_read:
                    fascicolo_ids.append(fascicolo.id)
            for allegato in protocollo.allegato_ids:
                for fascicolo in allegato.fascicolo_ids:
                    if fascicolo.perm_read:
                        fascicolo_ids.append(fascicolo.id)
            protocollo.fascicolo_ids = [[6, 0, fascicolo_ids]]

    def _compute_fascicolo_ids_count(self):
        for protocollo in self:
            protocollo.fascicolo_ids_count = len(protocollo.fascicolo_ids.ids)