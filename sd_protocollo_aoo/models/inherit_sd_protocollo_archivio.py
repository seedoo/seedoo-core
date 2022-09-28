from odoo import models, fields, api


class ProtocolloArchivio(models.Model):
    _inherit = "sd.protocollo.archivio"

    aoo_id = fields.Many2one(
        string="AOO",
        comodel_name="fl.set.set",
        domain="[('company_id', '=', company_id),('set_type', '=', 'aoo')]",
        required=True
    )

    @api.model
    def get_domain_can_used_to_protocol(self):
        domain = super(ProtocolloArchivio, self).get_domain_can_used_to_protocol()
        if not self.env.context.get("aoo_id", False):
            return domain
        domain.append(("aoo_id", "=", self.env.context.get("aoo_id")))
        return domain

    @api.constrains("company_id","corrente", "aoo_id")
    def _validate_archivio(self):
        return super(ProtocolloArchivio, self)._validate_archivio()

    def _check_archivio(self, archivio):
        check_aoo_id = False
        if self.search_count([("corrente", "=", True), ("company_id", "=", archivio.company_id.id),
                              ("aoo_id", "=", archivio.aoo_id.id)]) > 1:
            check_aoo_id = "L'archivio corrente è univoco per Company e per AOO"
        return check_aoo_id
