from odoo import models, fields, api


class Protocollo(models.Model):
    _inherit = "sd.protocollo.protocollo"

    button_fascicola_invisible = fields.Boolean(
        string="button fascicola invisible",
        compute="compute_buttons_invisible"
    )

    @api.depends("tipologia_protocollo")
    def compute_buttons_invisible(self):
        super(Protocollo, self).compute_buttons_invisible()
        for protocollo in self:
            protocollo.button_fascicola_invisible = protocollo._compute_button_fascicola_invisible()

    def _is_fascicolazione_disabled(self):
        self.ensure_one()
        # caso 1:
        # - l'utente corrente ha profilo protocollatore
        # - l'utente corrente è il protocollatore
        if self.env.user.has_group("sd_protocollo.group_sd_protocollo_protocollatore") and \
                self.protocollatore_id.id == self.env.uid:
            return False
        # caso 2:
        # - l'utente corrente ha profilo assegnatario
        # - il protocollo è in stato registrato o annullato
        # - l'utente corrente è un assegnatario per competenza la cui assegnazione è presa in carico o completata
        assegnazione_count = self.env["sd.protocollo.assegnazione"].search_count([
            ("protocollo_id", "=", self.id),
            ("tipologia", "=", "competenza"),
            ("state", "in", ["preso_in_carico", "lavorazione_completata"]),
            ("assegnatario_utente_id", "=", self.env.uid)
        ])
        if self.env.user.has_group("sd_protocollo.group_sd_protocollo_assegnatario") and \
                self.state in ["registrato", "annullato"] and \
                assegnazione_count > 0:
            return False
        return True

    def _compute_button_fascicola_invisible(self):
        # il button di fascicolazione deve essere invisibile se uno dei seguenti casi è verificata
        # caso base:
        # - il numero dei documenti associati al protocollo da classificare e fascicolare è maggiore di zero
        caso_base = self.env["sd.dms.document"].search([
            ("protocollo_id", "=", self.id),
            "|", ("voce_titolario_id", "=", False), ("fascicolo_ids", "=", False)
        ], count=True) > 0
        # caso 1:
        # - caso base
        # - l'utente corrente ha profilo protocollatore
        # - l'utente corrente è il protocollatore
        # - lo stato del protocollatore è in lavorazione
        if caso_base and \
                self.env.user.has_group("sd_protocollo.group_sd_protocollo_protocollatore") and \
                self.protocollatore_id.id == self.env.uid and \
                self.protocollatore_stato == "lavorazione":
            return False
        # caso 2:
        # - caso base
        # - l'utente corrente ha profilo assegnatario
        # - l'utente corrente è un assegnatario per competenza la cui assegnazione è in stato lavorazione
        # - il protocollo è in stato registrato o annullato
        if caso_base and \
                self.env.user.has_group("sd_protocollo.group_sd_protocollo_assegnatario") and \
                self.check_state_assegnazione("competenza", "preso_in_carico", self.env.uid) and \
                self.state in ["registrato", "annullato"]:
            return False
        return True

    def _compute_documento_id_voce_titolario_readonly(self):
        super(Protocollo, self)._compute_documento_id_voce_titolario_readonly()
        for rec in self:
            # caso 5:
            # - il documento corrente ha un fascicolo associato
            if rec.documento_id.fascicolo_ids:
                return True
