from odoo import models, fields, _
from odoo.exceptions import ValidationError


class ProtocolloWizardActions(models.Model):
    _inherit = "sd.protocollo.protocollo"

    def protocollo_fascicola_action(self):
        self.ensure_one()
        domain_fascicolo_ids = []
        verified_voce_titolario_ids = []
        document_filename_list = []
        documents = self.env["sd.dms.document"].search([
            ("protocollo_id", "=", self.id),
            ("voce_titolario_id", "!=", False),
            ("fascicolo_ids", "=", False),
        ])
        for document in documents:
            document_filename_list.append(document.filename)
            if document.voce_titolario_id.id in verified_voce_titolario_ids:
                continue
            verified_voce_titolario_ids.append(document.voce_titolario_id.id)
            fascicoli = self.env["sd.fascicolo.fascicolo"].search([
                ("voce_titolario_id", "=", document.voce_titolario_id.id),
                ('perm_write', '=', 'True'),
                ('state', '=', 'aperto')
            ])
            domain_fascicolo_ids += fascicoli.ids
        if domain_fascicolo_ids == []:
            raise_string = "Non ci sono fascicoli, o non hai visibilità dei fascicoli, con cui fasciolare i seguenti documenti: %s" % ", ".join(
                document_filename_list)
            self.env.user._request_notify_message("danger", "Fascicolazione", raise_string, sticky=True)
            return
        context = dict(
            self.env.context,
            protocollo_id=self.id,
            domain_fascicolo_ids=domain_fascicolo_ids
        )
        return {
            "name": context.get("wizard_label", ""),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "sd.protocollo.wizard.protocollo.fascicola",
            "type": "ir.actions.act_window",
            "target": "new",
            "context": context
        }