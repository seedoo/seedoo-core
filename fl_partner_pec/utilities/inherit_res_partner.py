from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = "res.partner"

    fl_pec_mail_invisible = fields.Boolean(
        string="pec_mail invisible",
        compute="_compute_fl_pec_mail_invisible"
    )

    fl_pec_mail_required = fields.Boolean(
        string="pec_mail required",
        compute="_compute_fl_pec_mail_required"
    )

    @api.onchange("pec_mail")
    def _compute_fl_pec_mail_invisible(self):
        ir_module_obj = self.env["ir.module.module"].sudo()
        l10n_it_pec = ir_module_obj.search([("name", "=", "l10n_it_pec"), ("state", "=", "installed")])

        for rec in self:
            pec_mail_invisible = False
            if l10n_it_pec:
                pec_mail_invisible = True
            rec.fl_pec_mail_invisible = pec_mail_invisible

    def _compute_fl_pec_mail_required(self):
        for rec in self:
            rec.fl_pec_mail_required = False

