# coding=utf-8

from odoo import http
from odoo.http import request


class ReportController(http.Controller):
    @http.route(
        route="/seedoo_protocollo/registro_giornaliero/pdf/<docid>",
        type="http",
        auth="user",
        website=True
    )
    def report_routes(self, docid=None):
        registro_giornaliero_obj = request.env["sd.protocollo.registro.giornaliero"]
        docid = int(docid)
        registro_giornaliero = registro_giornaliero_obj.browse(docid)
        if not registro_giornaliero:
            request.not_found("Registro Giornaliero non trovato")

        if registro_giornaliero.state != "aperto":
            request.not_found("Registro Giornaliero già chiuso.")  # TODO: Recuperare l'attachment già esistente

        pdf_filename = "%s.pdf" % registro_giornaliero.nome
        pdf_content = registro_giornaliero_obj.render_pdf(docid)

        headers = [
            ("Content-Type", "application/pdf"),
            ("Content-Length", len(pdf_content)),
            ("Content-Disposition", "filename=\"%s\"" % pdf_filename),
        ]

        return request.make_response(data=pdf_content, headers=headers)
