from odoo import http


class ProtocolloDashboardController(http.Controller):

    @http.route("/protocollo/dashboard", type="json", auth="user", website=False)
    def protocollo_dashboard(self):
        values = self._prepare_values_for_dashboard()
        view = http.request.env.ref("sd_protocollo.template_protocollo_dashboard")
        return {
            "html_content": view._render(values)
        }

    @http.route("/protocollo/dashboard/list", type="json", auth="user")
    def protocollo_dashboard_list(self, action_name, action_context):
        env = http.request.env
        if not action_name:
            return {}
        action = env.ref("sd_protocollo.action_sd_protocollo_protocollo_list_%s" % action_name, raise_if_not_found=False)
        if action:
            action = action.read()[0]
            action.update({
                "display_name": action_context,
                "views": [(action["views"][0][0], "list"), (action["views"][1][0], "form")],
            })
        return action

    def _prepare_values_for_dashboard(self):
        values = {"user_id": http.request.env.user}
        self._set_value("protocolli_bozza", values)
        self._set_value("protocolli_assegnati_a_me", values, "sd_protocollo.assegnato_a_me_active")
        self._set_value("protocolli_assegnati_mio_ufficio", values, "sd_protocollo.assegnato_a_mio_ufficio_active")
        self._set_value("protocolli_da_assegnare", values, "sd_protocollo.da_assegnare_active")
        self._set_value("protocolli_da_inviare", values)
        self._set_value("protocolli_assegnati_da_me", values, "sd_protocollo.assegnato_da_me_active")
        self._set_value("protocolli_rifiutati", values)
        self._set_value("protocolli_assegnati_a_me_competenza", values, "sd_protocollo.assegnato_a_me_competenza_active")
        self._set_value("protocolli_assegnati_mio_ufficio_competenza", values, "sd_protocollo.assegnato_a_mio_ufficio_competenza_active")
        self._set_value("protocolli_assegnati_conoscenza", values, "sd_protocollo.assegnato_cc_active")
        self._set_value("protocolli_in_lavorazione", values)
        return values

    def _set_value(self, key, values, config_parameter=False):
        values[key] = False
        config_active = True
        if config_parameter:
            config_obj = http.request.env["ir.config_parameter"].sudo()
            config_active = bool(config_obj.get_param(config_parameter))
        if not config_active:
            return
        protocollo_obj = http.request.env["sd.protocollo.protocollo"]
        filter_field = "filter_%s" % key
        values[key] = protocollo_obj.search([(filter_field, "=", True)], count=True)