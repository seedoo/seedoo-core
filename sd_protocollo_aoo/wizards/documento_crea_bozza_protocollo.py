from odoo import models, _, api
from odoo.exceptions import UserError


class DocumentoWizardCreaBozzaProtocollo(models.TransientModel):
    _inherit = "sd.protocollo.wizard.documento.crea.bozza"

    def _get_values_protocollo(self, main_document_id, allegati_list):
        values = super(DocumentoWizardCreaBozzaProtocollo, self)._get_values_protocollo(main_document_id, allegati_list)
        aoo_id = self.protocollatore_ufficio_id.aoo_id.id
        if not aoo_id:
            raise UserError(_("You have to configure the AOO associated with the selected office"))
        values.update({
            "aoo_id": aoo_id
        })
        return values

    @api.onchange("protocollatore_ufficio_id")
    def onchange_protocollatore_ufficio_id(self):
        aoo_id = self.protocollatore_ufficio_id.aoo_id.id
        context = dict(
            self.env.context,
            aoo_id=aoo_id
        )
        self = self.with_context(context)
        super(DocumentoWizardCreaBozzaProtocollo, self).onchange_protocollatore_ufficio_id()
