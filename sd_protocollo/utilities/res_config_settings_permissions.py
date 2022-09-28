from odoo import models, fields, api


class ResConfigSettingsPermissions(models.TransientModel):
    _inherit = "res.config.settings"

    module_fl_protocollo_segnatura_pdf_invisible = fields.Boolean(
        string="field module_fl_protocollo_segnatura_pdf invisible",
        compute="_compute_module_fl_protocollo_segnatura_pdf_invisible"
    )

    @api.onchange("segnatura_pdf_protocollo_ingresso", "segnatura_pdf_protocollo_uscita")
    def _compute_module_fl_protocollo_segnatura_pdf_invisible(self):
        for rec in self:
            module_fl_protocollo_segnatura_pdf_invisible = True
            if rec._get_active_pdf_fields():
                module_fl_protocollo_segnatura_pdf_invisible = False

            rec.module_fl_protocollo_segnatura_pdf_invisible = module_fl_protocollo_segnatura_pdf_invisible

    def _get_active_pdf_fields(self):
        if self.segnatura_pdf_protocollo_ingresso or self.segnatura_pdf_protocollo_uscita:
            return True
        return False
