from odoo import http
from odoo.addons.sd_protocollo.controllers.dashboard import ProtocolloDashboardController


class ProtocolloDashboardControllerTitolario(ProtocolloDashboardController):

    @http.route("/protocollo/dashboard/list", type="json", auth="user")
    def protocollo_dashboard_list(self, action_name, action_context):
        res = super().protocollo_dashboard_list(action_name, action_context)
        env = http.request.env
        if action_name in ["protocolli_da_classificare"]:
            action = env.ref("sd_protocollo_titolario.action_sd_protocollo_protocollo_list_protocolli_da_classificare").read()[0]
            action.update({
                "display_name": action_context,
                "views": [(action["views"][0][0], "list"), (action["views"][1][0], "form")],
            })
            return action
        return res

    def _prepare_values_for_dashboard(self):
        values = super(ProtocolloDashboardControllerTitolario, self)._prepare_values_for_dashboard()
        self._set_value("protocolli_da_classificare", values, "sd_protocollo.non_classificati_active")
        return values