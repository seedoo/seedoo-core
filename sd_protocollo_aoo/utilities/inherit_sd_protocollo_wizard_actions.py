from odoo import models

class ProtocolloWizardActions(models.Model):
    _inherit = "sd.protocollo.protocollo"

    def protocollo_aggiungi_mittente_interno_action(self):
        context = dict(
            self.env.context,
            aoo_id=self.aoo_id.id
        )
        return super(ProtocolloWizardActions, self.with_context(context)).protocollo_aggiungi_mittente_interno_action()

    def protocollo_assegna_action(self):
        context = dict(
            self.env.context,
            aoo_id=self.aoo_id.id
        )
        return super(ProtocolloWizardActions, self.with_context(context)).protocollo_assegna_action()

    def protocollo_assegna_conoscenza_action(self):
        context = dict(
            self.env.context,
            aoo_id=self.aoo_id.id
        )
        return super(ProtocolloWizardActions, self.with_context(context)).protocollo_assegna_conoscenza_action()

    def protocollo_riassegna_action(self):
        context = dict(
            self.env.context,
            aoo_id=self.aoo_id.id
        )
        return super(ProtocolloWizardActions, self.with_context(context)).protocollo_riassegna_action()