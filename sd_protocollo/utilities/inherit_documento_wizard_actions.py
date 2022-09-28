from odoo import models, fields, api, _
from odoo.exceptions import UserError


class DocumentoWizardActions(models.Model):
    _inherit = "sd.dms.document"

    def protocollo_carica_documento_action(self):
        self.ensure_one()
        return self.protocollo_id.protocollo_carica_documento_action()

    def protocollo_crea_bozza_da_documento_action(self):
        document_with_protocol_list = []
        document_without_perm_write_list = []
        for rec in self:
            if rec.registration_type == "protocol":
                if rec.protocollo_id:
                    document_with_protocol_list.append(rec.filename)
                if not rec.perm_write:
                    document_without_perm_write_list.append(rec.filename)
            else:
                self.env.user._request_notify_message(
                    "danger",
                    _("Warning!"),
                    self._get_error()
                )

                return False

        if document_without_perm_write_list:
            error_message = self._get_html_message(document_without_perm_write_list)
            if error_message:
                self.env.user._request_notify_message(
                    "danger",
                    _("You do not have writing permission on the following documents:"),
                    error_message
                )
            return False
        if len(document_with_protocol_list) > 1:
            error_message = self._get_html_message(document_with_protocol_list)
            if error_message:
                self.env.user._request_notify_message("danger",
                                                      _("There are documents already associated with a protocol:"),
                                                      error_message)
            return False
        elif len(document_with_protocol_list) == 1:
            self.env.user._request_notify_message(
                "danger",
                _("Warning!"),
                _("The document is already associated with a protocol")
            )
            return False

        context = dict(
            self.env.context,
            documento_ids=self.ids
        )

        return {
            "name": _("Create draft / Add documents"),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "sd.protocollo.wizard.documento.crea.bozza",
            "type": "ir.actions.act_window",
            "target": "new",
            "context": context
        }

    def _get_error(self):
        if len(self) > 1:
            return _("There are documents that do not have protocol as registration type!")
        else:
            return _("The document do not have protocol as registration type!")

    def _get_html_message(self, message_list):
        if not message_list:
            return ""
        html_message = "<ul>"
        for message in message_list:
            html_message += "<li>%s</li>" % message
        html_message += "</ul>"
        return html_message