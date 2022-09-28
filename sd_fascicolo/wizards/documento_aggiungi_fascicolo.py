from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class WizardDocumentoAggiungiFascicolo(models.TransientModel):
    _name = "sd.fascicolo.wizard.documento.aggiungi.fascicolo"
    _description = "Fascicolo wizard documento aggiungi fascicolo"

    fascicolo_id = fields.Many2one(
        string="Dossier",
        comodel_name="sd.fascicolo.fascicolo",
        domain=lambda self: self._get_fascicolo_ids_domain()
    )

    # TODO: quando si farà la multifascicolazione allora si dovrà usare il campo many2many commentato di seguito
    # fascicolo_ids = fields.Many2many(
    #     string="Dossiers",
    #     comodel_name="sd.fascicolo.fascicolo",
    #     relation="sd_fascicolo_wizard_documento_aggiungi_fascicolo_rel",
    #     domain=lambda self: self._get_fascicolo_ids_domain()
    # )

    @api.model
    def _get_fascicolo_ids_domain(self):
        domain = [
            ('id', 'not in', self.env.context.get('dossiers_ids', [])),
            ('perm_write', '=', 'True'),
            ('state', '=', 'aperto')
        ]
        document = self.env["sd.dms.document"].browse(self.env.context.get("document_id", False))
        if document and document.voce_titolario_id:
            domain.append(("voce_titolario_id", "=", document.voce_titolario_id.id))
        return domain

    def write_dossiers(self):
        context = dict(self._context or {})
        document = self.env["sd.dms.document"].browse(int(context["document_id"]))
        document.documento_aggiungi_fascicoli([self.fascicolo_id.id])