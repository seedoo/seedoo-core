from odoo import http
from odoo.addons.sd_protocollo.controllers.dashboard import ProtocolloDashboardController


class ProtocolloPecDashboardController(ProtocolloDashboardController):

    @http.route("/protocollo/dashboard/list", type="json", auth="user")
    def protocollo_dashboard_list(self, action_name, action_context):
        res = super(ProtocolloPecDashboardController, self).protocollo_dashboard_list(action_name, action_context)
        env = http.request.env
        if action_name in ["mail_da_protocollare_pec"]:
            action = env.ref("sd_protocollo_pec.action_mail_mail_list_mail_da_protocollare_pec").read()[0]
            action.update({
                "display_name": action_context,
                "views": [(action["views"][0][0], "list"), (action["views"][1][0], "form")],
            })
            return action
        return res

    def _prepare_values_for_dashboard(self):
        env = http.request.env
        mail_obj = env["mail.mail"]
        values = super(ProtocolloPecDashboardController, self)._prepare_values_for_dashboard()
        values.update({
            "mail_da_protocollare_pec": mail_obj.search([("filter_mail_da_protocollare_pec", "=", True)], count=True)
        })
        return values
