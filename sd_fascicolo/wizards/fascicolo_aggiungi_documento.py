from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class WizardFascicoloAggiungiDocumento(models.TransientModel):
    _name = "sd.fascicolo.wizard.fascicolo.aggiungi.documento"
    _description = "Wizard fascicolo aggiungi documento"

    documento_ids = fields.Many2many(
        string="Documents",
        comodel_name="sd.dms.document",
        relation="sd_fascicolo_wizard_fascicolo_aggiungi_documento_rel",
        domain=lambda self: self._get_documento_ids_domain()
    )

    @api.model
    def _get_documento_ids_domain(self):
        domain = [
            ('id', 'not in', self.env.context.get('documents_ids', [])),
            ('fascicolo_ids', '=', False), # TODO: GESTIRE DOMAIN IN CASO DI MULTIFASCICOLAZIONE
            ('perm_write', '=', 'True'),
        ]
        fascicolo = self.env["sd.fascicolo.fascicolo"].browse(self.env.context.get("fascicolo_id", False))
        if fascicolo and fascicolo.voce_titolario_id:
            domain.append(("voce_titolario_id", "=", fascicolo.voce_titolario_id.id))
        return domain

    def write_documents(self):
        context = dict(self._context or {})
        fascicolo = self.env["sd.fascicolo.fascicolo"].browse(int(context["fascicolo_id"]))
        fascicolo.fascicolo_aggiungi_documenti(self.documento_ids.ids)