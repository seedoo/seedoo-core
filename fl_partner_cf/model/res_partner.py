from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def check_fiscalcode(self):
        for partner in self:
            if not partner.fiscalcode:
                # Because it is not mandatory
                continue
            elif partner.company_type == 'person':
                # Person case
                if partner.company_name:
                    # In E-commerce, if there is company_name,
                    # the user might insert VAT in fiscalcode field.
                    # Perform the same check as Company case
                    continue
                if len(partner.fiscalcode) != 16:
                    # Check fiscalcode of a person
                    return False
        return True

    fiscalcode = fields.Char(
        'Fiscal Code', size=16, help="Italian Fiscal Code")

    calculate_fiscalcode = fields.Boolean(
        string="Calculate F.C.",
        readonly=True,
        compute="_compute_calculate_fiscalcode"
    )

    # TODO: Deprecated, use _sql_constraints or @api.constraints
    _constraints = [
        (check_fiscalcode,
         "The fiscal code doesn't seem to be correct.", ["fiscalcode"])
    ]

    def _compute_calculate_fiscalcode(self):
        config_param = self.env['ir.config_parameter'].sudo().get_param('fl_partner_cf.compute_fiscalcode')
        ir_module = self.env['ir.module.module'].sudo().search(
            [('name', '=', 'l10n_it_fiscalcode'), ('state', '=', 'installed')]
        )
        for rec in self:
            calculate_fiscalcode = False
            if config_param and not ir_module:
                calculate_fiscalcode = True
            rec.calculate_fiscalcode = calculate_fiscalcode

    @api.model
    def create(self, values):
        ir_config_parameter = self.env["ir.config_parameter"].sudo()
        res_partner = self.env["res.partner"].sudo()
        if values.get('fiscalcode', False):
            if ir_config_parameter.get_param("fl_partner_cf.fiscalcode_unique"):
                if res_partner.search_count([('fiscalcode', '=', values.get('fiscalcode'))]) > 0:
                    error, values = self.check_unique_fiscalcode(values)
                    if error:
                        raise UserError(error)
        return super().create(values)

    def write(self, values):
        ir_config_parameter = self.env["ir.config_parameter"].sudo()
        if values.get('fiscalcode', False):
            if ir_config_parameter.get_param("fl_partner_cf.fiscalcode_unique"):
                error,values = self.check_unique_fiscalcode(values)
                if error:
                    raise UserError(error)
        return super().write(values)

    def check_unique_fiscalcode(self,values):
        res_partner = self.env["res.partner"].sudo()
        error = False
        if res_partner.search_count([('fiscalcode', '=', values.get('fiscalcode'))]) > 0:
            error = _('You have entered a FiscalCode already used')
            return error,values
        return error,values


