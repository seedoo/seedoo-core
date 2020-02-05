# coding=utf-8

from openerp import http
from openerp.http import request


class ReportController(http.Controller):
    @http.route(
        route="/seedoo_protocollo/journal/pdf/<docid>",
        type="http",
        auth="user",
        website=True
    )
    def report_routes(self, docid=None):
        journal_obj = request.env["protocollo.journal"]

        journal_id = journal_obj.search([("id", "=", docid)])
        if not journal_id:
            request.not_found("Registro Giornaliero non trovato")

        if journal_id.state != "draft":
            request.not_found("Registro Giornaliero già chiuso.")  # TODO: Recuperare l'attachment già esistente

        pdf_filename = "Registro Giornaliero %s.pdf" % journal_id.date
        pdf_content = journal_id.render_pdf()

        headers = [
            ("Content-Type", "application/pdf"),
            ("Content-Length", len(pdf_content)),
            ("Content-Disposition", "filename=\"%s\"" % pdf_filename),
        ]

        return request.make_response(data=pdf_content, headers=headers)
