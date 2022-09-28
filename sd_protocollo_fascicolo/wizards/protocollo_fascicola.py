from odoo import models, fields, api


class WizardGestioneFascicolazione(models.TransientModel):
    _name = "sd.protocollo.wizard.protocollo.fascicola"
    _description = "Wizard Gestione Fascicoli del Protocollo"

    fascicolo_id = fields.Many2one(
        string="Fascicolo",
        comodel_name="sd.fascicolo.fascicolo",
        domain="[('id','in',context.get('domain_fascicolo_ids', []))]",
        required=True
    )

    documento_ids = fields.Many2many(
        string="Documento",
        comodel_name="sd.dms.document",
        relation="sd_protocollo_wizard_protocollo_fascicolo_document_rel",
        column1="wizard_id",
        column2="documento_id",
        readonly=True
    )

    @api.onchange("fascicolo_id")
    def _onchange_fascicolo_id(self):
        self.ensure_one()
        prot_id = self.env.context.get("protocollo_id")
        protocollo = self.env["sd.protocollo.protocollo"].browse(prot_id)
        documento_list = []
        # sono selezionabili solamente i documenti e gli allegati che hanno la stessa voce di titolario del fascicolo
        if protocollo and self.fascicolo_id and self.fascicolo_id.voce_titolario_id.id:
            for allegato in protocollo.allegato_ids:
                if allegato.voce_titolario_id and \
                        allegato.voce_titolario_id.id == self.fascicolo_id.voce_titolario_id.id:
                    documento_list.append(allegato.id)
            if protocollo.documento_id and protocollo.documento_id.voce_titolario_id and \
                    protocollo.documento_id.voce_titolario_id.id == self.fascicolo_id.voce_titolario_id.id:
                documento_list.append(protocollo.documento_id.id)
        self.documento_ids = [(6, 0, documento_list)]

    def action_aggiungi_documento_fascicolo(self):
        prot_id = self.env.context.get("protocollo_id")
        protocollo = self.env["sd.protocollo.protocollo"].browse(prot_id)
        self.fascicolo_id.fascicolo_aggiungi_documenti(self.documento_ids.ids, from_document=False)
        protocollo.storico_aggiungi_fascicolazione(self.fascicolo_id.nome)