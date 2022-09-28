from odoo import models, fields, api


class InvioPermissions(models.Model):
    _inherit = "sd.protocollo.invio"

    button_reinvia_mail_invisible = fields.Boolean(
        string="button reinvia mail invisible",
        compute="_compute_button_reinvia_mail_invisible"
    )

    button_reset_mail_invisible = fields.Boolean(
        string="button reset mail invisible",
        compute="_compute_button_reset_mail_invisible"
    )

    def _compute_button_reinvia_mail_invisible(self):
        # il button reinvia mail serve a generare una nuova copia dell'invio ed è visibile nelle seguenti condizioni:
        # - l'utente corrente ha profilo protocollatore
        # - l'utente corrente è il protocollatore
        # - lo stato del protocollatore è in lavorazione
        # - il protocollo è registrato o annullato
        # - l'invio è marcato come da_reinviare
        for invio in self:
            protocollo = invio.protocollo_id
            if self.env.user.has_group('sd_protocollo.group_sd_protocollo_protocollatore') and \
                    self.env.uid == protocollo.protocollatore_id.id and \
                    protocollo.protocollatore_stato == "lavorazione" and \
                    protocollo.state in ["registrato", "annullato"] and \
                    invio.da_reinviare:
                invio.button_reinvia_mail_invisible = False
            else:
                invio.button_reinvia_mail_invisible = True


    def _compute_button_reset_mail_invisible(self):
        # il button reset mail serve a rimettere in stato outgoing la relativa mail dell'invio per gestire i casi in
        # cui la mail non è stata inviata per via di un errore in fase di invio, è visible nelle seguenti condizioni:
        # - l'utente corrente ha profilo protocollatore
        # - l'utente corrente è il protocollatore
        # - lo stato del protocollatore è in lavorazione
        # - il protocollo è registrato o annullato
        # - l'invio è marcato come da_resettare
        for invio in self:
            protocollo = invio.protocollo_id
            if self.env.user.has_group('sd_protocollo.group_sd_protocollo_protocollatore') and \
                    self.env.uid == protocollo.protocollatore_id.id and \
                    protocollo.protocollatore_stato == "lavorazione" and \
                    protocollo.state in ["registrato", "annullato"] and \
                    invio.da_resettare:
                invio.button_reset_mail_invisible = False
            else:
                invio.button_reset_mail_invisible = True

    @api.depends("field_tree_invio_decoration_state")
    def _compute_field_tree_invio_decoration_state(self):
        super(InvioPermissions, self)._compute_field_tree_invio_decoration_state()
        for invio in self:
            if invio.mezzo_trasmissione_integrazione == "pec" and invio.state in ['received']:
                tree_invio_decoration_state = "success"
                invio.field_tree_invio_decoration_state = tree_invio_decoration_state
