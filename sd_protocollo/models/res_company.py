from odoo import models, fields, api
from odoo.http import request


class ResCompany(models.Model):
    _inherit = "res.company"

    codice_ipa = fields.Char(
        string="Codice iPA"
    )

    registro_ids = fields.One2many(
        string="Registri",
        comodel_name="sd.protocollo.registro",
        inverse_name="company_id",
        readonly=True
    )

    @api.model
    def get_selected_company_ids(self, count=False):
        # Attenzione, non è possibile richiamare 'request' attraverso un'azione programmata (cron), se richiamato
        # darà un errore RuntimeError("object unbound") della lib werkzeug, per ovviare a questo, nel caso del cron,
        # la default company sarà estrapolata dal context.
        if self.env.context.get("cron_company_id", False):
            return self.env.context.get("cron_company_id")
        cids = request.httprequest.cookies.get('cids', str(self.env.user.company_id.id))
        company_ids = cids.split(",")
        if count:
            return len(company_ids)
        return company_ids