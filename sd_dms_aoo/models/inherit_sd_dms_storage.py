from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Storage(models.Model):
    _inherit = "sd.dms.storage"

    aoo_id = fields.Many2one(
        string="AOO",
        comodel_name="fl.set.set",
        domain="[('company_id', '=', company_id),('set_type', '=', 'aoo')]"
    )

    @api.onchange("company_id")
    def _default_aoo_id(self):
        aoo_id = False
        if self.env.user.get_aoo_id_readonly():
            aoo_id = self.env.user.fl_set_set_ids[0].aoo_id.id
        self.aoo_id = aoo_id

    @api.constrains("company_id")
    def _validate_company_id(self):
        for rec in self:
            if rec.company_id.id != rec.aoo_id.company_id.id:
                raise ValidationError(
                    "Non è possibile modificare la company in quanto la company della AOO associata è diversa da "
                    "quella inserita "
                )
