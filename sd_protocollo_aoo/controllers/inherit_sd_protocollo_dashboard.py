from odoo import http
from odoo.addons.sd_protocollo.controllers.dashboard import ProtocolloDashboardController


class ProtocolloAooDashboardController(ProtocolloDashboardController):

    def _prepare_values_for_dashboard(self):
        env = http.request.env
        user = env.user
        values = super(ProtocolloAooDashboardController, self)._prepare_values_for_dashboard()
        active_companies = env["res.company"].get_selected_company_ids()

        user_set_ids = [set for set in user.fl_set_set_ids if str(set.company_id.id) in active_companies]
        aoo_list = {}

        for set in user_set_ids:
            if set.set_type == "aoo":
                if not aoo_list.get(set.name, False):
                    aoo_list.update({set.name: []})

            elif set.set_type == "uo":
                if set.aoo_id:
                    if not aoo_list.get(set.aoo_id.name, False):
                        aoo_list.update({set.aoo_id.name: [set.name]})
                    else:
                        aoo_list[set.aoo_id.name].append(set.name)

        for key in aoo_list.keys():
            aoo_list[key] = ", ".join(aoo_list[key])

        # rendo una tupla il dict per mostrarlo agevolmente nel template
        user_set_ids = [(k, v) for k, v in aoo_list.items()]

        values.update({
            "user_set_list": user_set_ids,
        })
        return values
