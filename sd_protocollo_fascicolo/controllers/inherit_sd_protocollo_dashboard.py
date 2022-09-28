from odoo import http
from odoo.addons.sd_protocollo.controllers.dashboard import ProtocolloDashboardController


class ProtocolloFascicoloDashboardController(ProtocolloDashboardController):

    @http.route("/protocollo/dashboard/list", type="json", auth="user")
    def protocollo_dashboard_list(self, action_name, action_context):
        res = super().protocollo_dashboard_list(action_name, action_context)
        env = http.request.env
        if action_name in ["protocolli_da_fascicolare"]:
            action = env.ref("sd_protocollo_fascicolo.action_sd_protocollo_protocollo_list_protocolli_da_fascicolare").read()[0]
            action.update({
                "display_name": action_context,
                "views": [(action["views"][0][0], "list"), (action["views"][1][0], "form")],
            })
            return action
        return res

    def _prepare_values_for_dashboard(self):
        values = super(ProtocolloFascicoloDashboardController, self)._prepare_values_for_dashboard()
        self._set_value("protocolli_da_fascicolare", values, "sd_protocollo.non_fascicolati_active")
        return values