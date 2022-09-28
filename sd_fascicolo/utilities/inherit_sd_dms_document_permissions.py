from odoo import models, fields, api


class InheritSdDmsDocumentPermissions(models.Model):
    _inherit = "sd.dms.document"

    button_disassocia_documento_invisible = fields.Boolean(
        string="button disassocia documento invisible",
        compute="_compute_buttons_invisible"
    )

    button_documento_aggiungi_fascicolo_invisible = fields.Boolean(
        string="button documento aggiungi fascicolo invisible",
        compute="_compute_buttons_invisible"
    )

    @api.depends("state")
    def _compute_buttons_invisible(self):
        for rec in self:
            rec.button_disassocia_documento_invisible = rec._compute_button_disassocia_documento_invisible()
            rec.button_documento_aggiungi_fascicolo_invisible = rec._compute_button_documento_aggiungi_fascicolo_invisible()

    def _compute_button_disassocia_documento_invisible(self):
        if "disassocia_documento_fascicolo_id" in self.env.context and self.perm_write:
            return False
        else:
            return True

    def _compute_button_documento_aggiungi_fascicolo_invisible(self):
        # il button fascicola è invisible quando la prima delle seguenti condizioni è verificata
        # l'utente corrente non ha permessi di scrittura
        if not self.perm_write:
            return True
        # il documento non ha una voce di titolario associata
        if not self.voce_titolario_id:
            return True
        # il documento ha già un fascicolo associato
        if self.fascicolo_ids:
            return True
        return False

    def _compute_voce_titolario_id_readonly(self):
        super(InheritSdDmsDocumentPermissions, self)._compute_voce_titolario_id_readonly()
        for rec in self:
            # La voce di titolario del documento sarà readonly se il documento è associato ad un fascicolo
            if not rec.voce_titolario_id_readonly and rec.fascicolo_ids:
                rec.voce_titolario_id_readonly = True