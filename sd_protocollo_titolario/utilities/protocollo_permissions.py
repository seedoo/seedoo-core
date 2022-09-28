from odoo import models, fields, api


class Protocollo(models.Model):
    _inherit = "sd.protocollo.protocollo"

    button_classifica_invisible = fields.Boolean(
        string="button classifica invisible",
        compute="compute_buttons_invisible"
    )

    documento_id_voce_titolario_readonly = fields.Boolean(
        string="documento_id_voce_titolario readonly",
        compute="compute_buttons_invisible"
    )

    documento_id_voce_titolario_required = fields.Boolean(
        string="documento_id_voce_titolario required",
        compute="compute_buttons_invisible"
    )

    @api.depends("tipologia_protocollo")
    def compute_buttons_invisible(self):
        super(Protocollo, self).compute_buttons_invisible()
        for protocollo in self:
            protocollo.button_classifica_invisible = protocollo._compute_button_classifica_invisible()
            protocollo.documento_id_voce_titolario_readonly = protocollo._compute_documento_id_voce_titolario_readonly()
            protocollo.documento_id_voce_titolario_required = protocollo._compute_documento_id_voce_titolario_required()

    def _compute_button_classifica_invisible(self):
        # - l'utente corrente ha profilo protocollatore
        # - l'utente corrente è il protocollatore
        # - lo stato del protocollatore è in lavorazione
        # - il protocollo è in stato registrato o annullato
        # - il documento del protocollo non ha una voce di titolario
        if self.env.user.has_group("sd_protocollo.group_sd_protocollo_protocollatore") and \
                self.protocollatore_id.id == self.env.uid and \
                self.protocollatore_stato == "lavorazione" and \
                self.state in ["registrato", "annullato"] and \
                not self.documento_id.voce_titolario_id:
            return False
        # caso 2:
        # - l'utente corrente ha profilo assegnatario
        # - l'utente corrente è un assegnatario per competenza con stato in lavorazione
        # - il protocollo è in stato registrato o annullato
        # - il documento del protocollo non ha una voce di titolario
        if self.env.user.has_group("sd_protocollo.group_sd_protocollo_assegnatario") and \
                self.check_state_assegnazione("competenza", "preso_in_carico", self.env.uid) and \
                self.state in ["registrato", "annullato"] and \
                not self.documento_id.voce_titolario_id:
            return False
        return True

    def _compute_documento_id_voce_titolario_readonly(self):
        # caso 1:
        # - l'utente corrente ha profilo protocollatore
        # - l'utente corrente è il protocollatore
        # - lo stato del protocollatore è in lavorazione
        # - il protocollo deve avere la tipologia valorizzata (usata solo per una questione di visualizzazione nel form)
        if self.env.user.has_group("sd_protocollo.group_sd_protocollo_protocollatore") and \
                self.protocollatore_id.id == self.env.uid and \
                self.protocollatore_stato == "lavorazione" and \
                self.tipologia_protocollo:
            return False
        # caso 2:
        # - l'utente corrente ha profilo assegnatario
        # - l'utente corrente è un assegnatario per competenza con stato in lavorazione
        # - il protocollo è in stato registrato o annullato
        # - il documento del protocollo non ha una voce di titolario
        if self.env.user.has_group("sd_protocollo.group_sd_protocollo_assegnatario") and \
                self.check_state_assegnazione("competenza", "preso_in_carico", self.env.uid) and \
                self.state in ["registrato", "annullato"] and \
                not self.documento_id.voce_titolario_id:
            return False
        # caso 3:
        # - l'utente corrente ha profilo protocollatore
        # - l'utente corrente è un assegnatario per competenza con stato in lavorazione
        # - il protocollo è in stato registrato o annullato
        # - il documento del protocollo ha una voce di titolario
        # - è abilitata la configurazione per modificare la classificazione per gli assegnatari per competenza
        if self.env.user.has_group("sd_protocollo.group_sd_protocollo_protocollatore") and \
                self.check_state_assegnazione("competenza", "preso_in_carico", self.env.uid) and \
                self.state in ["registrato", "annullato"] and \
                self.documento_id.voce_titolario_id and \
                bool(self.env["ir.config_parameter"].sudo().get_param('sd_protocollo.modifica_classificazione')):
            return False
        # caso 4:
        # - l'utente corrente ha profilo manager
        # - il protocollo è in stato registrato o annullato
        # - il documento del protocollo ha una voce di titolario
        if self.env.user.has_group("sd_protocollo.group_sd_protocollo_manager") and \
                self.state in ["registrato", "annullato"] and \
                self.documento_id.voce_titolario_id:
            return False
        return True

    def _compute_documento_id_voce_titolario_required(self):
        # caso 1
        # il campo classification_required del document_type del documento del protocollo è true
        if self.documento_id_document_type_id and self.documento_id_document_type_id.classification_required:
            return True
        # caso 2:
        # - lo stato del protocollo è in registrato o annullato
        # - la voce di titolario è stata inserita
        if self.state in ["registrato", "annullato"] and \
            self.documento_id_voce_titolario_id:
            return True
        return False
