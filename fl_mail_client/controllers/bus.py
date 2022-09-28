from odoo.addons.bus.controllers.main import BusController
from odoo.http import request


class FlMailClientBusController(BusController):
    # --------------------------
    # Extends BUS Controller Poll
    # --------------------------
    def _poll(self, dbname, channels, last, options):
        if request.session.uid:
            partner_id = request.env.user.partner_id.id
            if partner_id:
                channels = list(channels)
                channels.append((request.db, "mail.list", request.env.user.partner_id.id))
        return super(FlMailClientBusController, self)._poll(dbname, channels, last, options)
