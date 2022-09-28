from odoo import models, fields, api


class WizardDocumentoDisassociaFascicolo(models.TransientModel):
    _name = "sd.protocollo.wizard.documento.disassocia.fascicolo"
    _description = "Documento disassocia fascicolo wizard"

    fascicolo_id = fields.Many2one(
        string="Fascicolo",
        comodel_name="sd.fascicolo.fascicolo",
        readonly=True
    )

    protocollo_id = fields.Many2one(
        string="Protocollo",
        comodel_name="sd.protocollo.protocollo",
        readonly=True
    )

    voce_titolario_id = fields.Many2one(
        string="Classificazione",
        comodel_name="sd.dms.titolario.voce.titolario",
        readonly=True
    )

    documento_ids = fields.Many2many(
        string="Documento",
        comodel_name="sd.dms.document",
        relation="sd_protocollo_wizard_documento_disassocia_fascicolo_doc_rel",
        column1="wizard_id",
        column2="documento_id",
        readonly=True
    )

    def action_yes(self):
        self.ensure_one()
        self.protocollo_id.protocollo_documento_disassocia_fascicoli(self.documento_ids, self.fascicolo_id)
