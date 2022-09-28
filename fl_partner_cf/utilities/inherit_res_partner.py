from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = "res.partner"

    fl_fiscalcode_invisible = fields.Boolean(
        string="fiscalcode invisible",
        compute="_compute_fiscalcode_invisible"
    )

    @api.onchange("fiscalcode")
    def _compute_fiscalcode_invisible(self):
        ir_module_obj = self.env["ir.module.module"].sudo()
        l10n_it_fiscalcode = ir_module_obj.search([("name", "=", "l10n_it_fiscalcode"), ("state", "=", "installed")])

        for rec in self:
            fiscalcode_invisible = False
            if l10n_it_fiscalcode:
                fiscalcode_invisible = True
            rec.fl_fiscalcode_invisible = fiscalcode_invisible

