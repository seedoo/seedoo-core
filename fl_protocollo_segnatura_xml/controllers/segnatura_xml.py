from odoo import http
from odoo.http import request


class SegnaturaXmlController(http.Controller):
    @http.route(route="/protocollo/segnatura_xml/<int:protocollo_id>", type="http", auth="user")
    def scarica_segnatura_xml(self, protocollo_id):
        protocollo_obj = request.env["sd.protocollo.protocollo"]
        protocollo = protocollo_obj.browse(protocollo_id)

        if protocollo.segnatura_xml:
            return request.make_response(
                data=protocollo.segnatura_xml,
                headers=[
                    ("Content-Type", "application/xml"),
                    ("Content-Disposition", "attachment; filename=%s" % "segnatura.xml")
                ]
            )

        return request.make_response("Segnatura.xml non disponibile per il download")
