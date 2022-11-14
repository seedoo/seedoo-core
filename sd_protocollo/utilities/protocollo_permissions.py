from odoo import models, fields, api


class ProtocolloPermissions(models.Model):
    _inherit = "sd.protocollo.protocollo"

    button_registra_invisible = fields.Boolean(
        string="button registra invisible",
        compute="compute_buttons_invisible"
    )

    button_annulla_invisible = fields.Boolean(
        string="button annulla invisible",
        compute="compute_buttons_invisible"
    )

    button_assegna_invisible = fields.Boolean(
        string="button assegna invisible",
        compute="compute_buttons_invisible"
    )

    button_aggiungi_assegnatari_invisible = fields.Boolean(
        string="button aggiungi assegnatari invisible",
        compute="compute_buttons_invisible"
    )

    button_elimina_assegnatari_invisible = fields.Boolean(
        string="button modifica assegnatari invisible",
        compute="compute_buttons_invisible"
    )

    button_aggiungi_assegnatari_conoscenza_invisible = fields.Boolean(
        string="button aggiungi assegnatari conoscenza invisible",
        compute="compute_buttons_invisible"
    )

    button_prendi_in_carico_assegnazione_invisible = fields.Boolean(
        string="button prendi in carico assegnazione invisible",
        compute="compute_buttons_invisible"
    )

    button_rifiuta_assegnazione_invisible = fields.Boolean(
        string="button rifiuta assegnazione invisible",
        compute="compute_buttons_invisible"
    )

    button_riassegna_invisible = fields.Boolean(
        string="button riassegna invisible",
        compute="compute_buttons_invisible"
    )

    button_leggi_assegnazione_invisible = fields.Boolean(
        string="button leggi assegnazione invisible",
        compute="compute_buttons_invisible"
    )

    button_completa_lavorazione_stato_invisible = fields.Boolean(
        string="button completa lavorazione invisible",
        compute="compute_buttons_invisible"
    )

    button_rimetti_in_lavorazione_stato_invisible = fields.Boolean(
        string="button rimetti in lavorazione invisible",
        compute="compute_buttons_invisible"
    )

    button_aggiungi_allegati_invisible = fields.Boolean(
        string="button aggiungi allegati invisible",
        compute="compute_buttons_invisible"
    )

    button_modifica_allegati_invisible = fields.Boolean(
        string="button modifica allegati invisible",
        compute="compute_buttons_invisible"
    )

    button_aggiungi_destinatario_invisible = fields.Boolean(
        string="button aggiungi destinatario invisible",
        compute="compute_buttons_invisible"
    )

    button_modifica_destinatario_invisible = fields.Boolean(
        string="button modifica destinatario invisible",
        compute="compute_buttons_invisible"
    )

    button_elimina_destinatario_invisible = fields.Boolean(
        string="button elimina destinatario invisible",
        compute="compute_buttons_invisible"
    )

    button_aggiungi_altro_soggetto_invisible = fields.Boolean(
        string="button aggiungi altro soggetto invisible",
        compute="compute_buttons_invisible"
    )

    button_modifica_altro_soggetto_invisible = fields.Boolean(
        string="button modifica altro soggetto invisible",
        compute="compute_buttons_invisible"
    )

    button_elimina_altro_soggetto_invisible = fields.Boolean(
        string="button elimina altro soggetto invisible",
        compute="compute_buttons_invisible"
    )

    button_aggiungi_mittente_invisible = fields.Boolean(
        string="button agiungi mittente invisible",
        compute="compute_buttons_invisible"
    )

    button_modifica_mittente_invisible = fields.Boolean(
        string="button modifica elimina destinatario invisible",
        compute="compute_buttons_invisible"
    )

    button_elimina_mittente_invisible = fields.Boolean(
        string="button elimina destinatario invisible",
        compute="compute_buttons_invisible"
    )

    button_aggiungi_mittente_interno_invisible = fields.Boolean(
        string="button salva mittente interno",
        compute="compute_mittente_interno_invisible"
    )

    button_elimina_mittente_interno_invisible = fields.Boolean(
        string="button elimina mittente interno",
        compute="compute_mittente_interno_invisible"
    )

    button_etichetta_invisible = fields.Boolean(
        string="button etichetta",
        compute="compute_buttons_invisible"
    )

    button_inserisci_segnatura_pdf_documento_invisible = fields.Boolean(
        string="button inserisci pdf documento",
        compute="compute_buttons_invisible"
    )

    button_invia_invisible = fields.Boolean(
        string="button invia",
        compute="compute_buttons_invisible"
    )

    button_elimina_bozza_invisible = fields.Boolean(
        string="button unlink bozza",
        compute="compute_buttons_invisible"
    )

    page_destinatari_ids_invisible = fields.Boolean(
        string="page destinatari_ids invisible",
        compute="_compute_page_destinatari_ids_invisible"
    )

    @api.depends("tipologia_protocollo")
    def compute_buttons_invisible(self):
        for protocollo in self:
            protocollo.button_registra_invisible = protocollo._compute_button_registra_invisible()
            protocollo.button_annulla_invisible = protocollo._compute_button_annulla_invisible()
            protocollo.button_assegna_invisible = protocollo._compute_button_assegna_invisible()
            protocollo.button_aggiungi_assegnatari_invisible = protocollo._compute_button_aggiungi_assegnatari_invisible()
            protocollo.button_elimina_assegnatari_invisible = protocollo._compute_button_elimina_assegnatari_invisible()
            protocollo.button_aggiungi_assegnatari_conoscenza_invisible = protocollo._compute_button_aggiungi_assegnatari_conoscenza_invisible()
            protocollo.button_prendi_in_carico_assegnazione_invisible = protocollo._compute_prendi_in_carico_assegnazione_invisible()
            protocollo.button_rifiuta_assegnazione_invisible = protocollo._compute_button_rifiuta_assegnazione_invisible()
            protocollo.button_riassegna_invisible = protocollo._compute_button_riassegna_invisible()
            protocollo.button_leggi_assegnazione_invisible = protocollo._compute_button_leggi_assegnazione_invisible()
            protocollo.button_completa_lavorazione_stato_invisible = protocollo._compute_button_completa_lavorazione_stato_invisible()
            protocollo.button_rimetti_in_lavorazione_stato_invisible = protocollo._compute_button_rimetti_in_lavorazione_stato_invisible()
            protocollo.button_aggiungi_allegati_invisible = protocollo._compute_button_aggiungi_allegati_invisible()
            protocollo.button_modifica_allegati_invisible = protocollo._compute_button_modifica_allegati_invisible()
            protocollo.button_aggiungi_destinatario_invisible = protocollo._compute_button_aggiungi_destinatario_invisible()
            protocollo.button_aggiungi_altro_soggetto_invisible = protocollo._compute_button_aggiungi_altro_soggetto_invisible()
            protocollo.button_modifica_altro_soggetto_invisible = protocollo.button_aggiungi_altro_soggetto_invisible
            protocollo.button_elimina_altro_soggetto_invisible = protocollo.button_aggiungi_altro_soggetto_invisible
            protocollo.button_modifica_destinatario_invisible = protocollo.button_aggiungi_destinatario_invisible
            protocollo.button_elimina_destinatario_invisible = protocollo.button_aggiungi_destinatario_invisible
            protocollo.button_aggiungi_mittente_invisible = protocollo._compute_button_aggiungi_mittente_invisible()
            protocollo.button_modifica_mittente_invisible = protocollo._compute_button_modifica_mittente_invisible()
            protocollo.button_elimina_mittente_invisible = protocollo.button_modifica_mittente_invisible
            protocollo.button_etichetta_invisible = protocollo._compute_button_etichetta_invisible()
            protocollo.button_inserisci_segnatura_pdf_documento_invisible = protocollo._compute_button_inserisci_segnatura_pdf_documento_invisible()
            protocollo.button_invia_invisible = protocollo._compute_button_invia_invisible()
            protocollo.button_elimina_bozza_invisible = protocollo._compute_button_elimina_bozza_invisible()

    @api.onchange("tipologia_protocollo", "mittente_interno_id")
    @api.depends("mittente_interno_id")
    def compute_mittente_interno_invisible(self):
        for protocollo in self:
            protocollo.button_aggiungi_mittente_interno_invisible = protocollo._compute_button_aggiungi_mittente_interno_invisible()
            protocollo.button_elimina_mittente_interno_invisible = protocollo._compute_button_elimina_mittente_interno_invisible()

    def _compute_button_registra_invisible(self):
        # - l'utente corrente ha profilo protocollatore
        # - l'utente corrente è il protocollatore
        # - il protocollo è in stato bozza
        if self.env.user.has_group('sd_protocollo.group_sd_protocollo_protocollatore') and \
                self.protocollatore_id.id == self.env.uid and \
                self.state == "bozza":
            return False
        return True

    def _compute_button_annulla_invisible(self):
        # - l'utente corrente ha profilo manager
        # - il protocollo è in stato registrato
        if self.env.user.has_group('sd_protocollo.group_sd_protocollo_manager') and self.state == "registrato":
            return False
        return True

    def _compute_button_assegna_invisible(self):
        # - l'utente corrente ha profilo assegnatario
        # - l'utente corrente è il protocollatore
        # - lo stato del protocollatore è in lavorazione
        # - il protocollo è in stato registrato o annullato
        # - il protocollo non ha assegnazioni per competenza
        if self.env.user.has_group('sd_protocollo.group_sd_protocollo_assegnatario') and \
                    self.protocollatore_id.id == self.env.uid and \
                    self.protocollatore_stato == "lavorazione" and \
                    self.state in ["registrato", "annullato"] and \
                    self.assegnazione_competenza_ids.ids == []:
            return False
        return True

    def _compute_button_aggiungi_assegnatari_invisible(self):
        # caso 1:
        # - il protocollo è in bozza
        # - il protocollo non ha neanche un'assegnazione ed è riservato
        # - l'utente corrente è il protocollatore
        # - lo stato del protocollatore è in lavorazione
        if self.state == "bozza" and \
                self.protocollatore_id.id == self.env.uid and \
                self.protocollatore_stato == "lavorazione":
            return False
        # caso 2:
        # - il protocollo è in stato registrato o annullato
        # - l'utente corrente è il protocollatore
        # - lo stato del protocollatore è in lavorazione
        # - il protocollo non ha assegnazioni per competenza
        if self.state in ["registrato", "annullato"] and \
                self.protocollatore_id.id == self.env.uid and \
                self.protocollatore_stato == "lavorazione" and \
                self.assegnazione_competenza_ids.ids == []:
            return False
        # caso 3:
        # - l'utente corrente ha profilo manager
        # - il protocollo è registrato
        if self.env.user.has_group('sd_protocollo.group_sd_protocollo_manager') and self.state == "registrato":
            return False
        return True

    def _compute_button_elimina_assegnatari_invisible(self):
        # caso 1:
        # - l'utente corrente è il protocollatore
        # - lo stato del protocollatore è in lavorazione
        # - il protocollo è in bozza
        # - il protocollo ha almeno una assegnazione
        if self.protocollatore_id.id == self.env.uid and \
                self.protocollatore_stato == "lavorazione" and \
                self.state == "bozza" and \
                not (self.assegnazione_parent_ids.ids == []):
            return False
        # caso 2:
        # - l'utente corrente ha profilo manager
        # - il protocollo è registrato o annullato
        if self.env.user.has_group('sd_protocollo.group_sd_protocollo_manager') and \
                self.state in ["registrato", "annullato"]:
            return False
        return True

    def _compute_button_aggiungi_assegnatari_conoscenza_invisible(self):
        config_obj = self.env["ir.config_parameter"].sudo()
        # caso base:
        # - il button aggiungi assegnatari deve essere invisible
        # - l'utente corrente ha profilo assegnatario
        # - il protocollo è in stato registrato o annullato
        # - il protocollo ha almeno un'assegnazione per competenza
        # - è abilitata la configurazione per aggiungere gli assegnatari per conoscenza
        caso_base = self.button_aggiungi_assegnatari_invisible and \
                    self.env.user.has_group('sd_protocollo.group_sd_protocollo_assegnatario') and \
                    self.state in ["registrato", "annullato"] and \
                    self.assegnazione_competenza_ids.ids != [] and \
                    bool(config_obj.get_param("sd_protocollo.abilita_aggiungi_assegnatari_cc"))
        if not caso_base:
            return True
        # caso 1:
        # - caso base
        # - l'utente corrente è il protocollatore
        # - lo stato del protocollatore è in lavorazione
        if caso_base and self.protocollatore_id.id == self.env.uid and self.protocollatore_stato == "lavorazione":
            return False
        # caso 2:
        # - caso base
        # - l'utente corrente è un assegnatario per competenza la cui assegnazione è in stato lavorazione
        if caso_base and self.check_state_assegnazione("competenza", "preso_in_carico", self.env.uid):
            return False
        return True

    def _compute_prendi_in_carico_assegnazione_invisible(self):
        # - l'utente corrente ha profilo assegnatario
        # - l'utente corrente è un assegnatario per competenza la cui assegnazione è in stato assegnato
        # - il protocollo è in stato registrato o annullato
        if self.env.user.has_group('sd_protocollo.group_sd_protocollo_assegnatario') and \
                self.check_state_assegnazione("competenza", "assegnato", self.env.uid) and \
                self.state in ["registrato", "annullato"]:
            return False
        return True

    def _compute_button_rifiuta_assegnazione_invisible(self):
        # - l'utente corrente ha profilo assegnatario
        # - l'utente corrente è un assegnatario per competenza la cui assegnazione è in stato assegnato
        # - il protocollo è in stato registrato o annullato
        if self.env.user.has_group('sd_protocollo.group_sd_protocollo_assegnatario') and \
                self.check_state_assegnazione("competenza", "assegnato", self.env.uid) and \
                self.state in ["registrato", "annullato"]:
            return False
        return True

    def _compute_button_riassegna_invisible(self):
        # caso base:
        # - l'utente corrente ha profilo protocollatore
        # - l'utente corrente è assegnatore di un'assegnazione in stato rifiutato
        # - il protocollo è in stato registrato o annullato
        caso_base = self.env.user.has_group('sd_protocollo.group_sd_protocollo_protocollatore') and \
                    len(self.get_assegnazione_assegnatore_ids("competenza", "rifiutato", self.env.uid)) > 0 and \
                    self.state in ["registrato", "annullato"]
        if not caso_base:
            return True
        # caso 1:
        # - caso base
        # - l'utente corrente è il protocollatore
        # - lo stato del protocollatore è in lavorazione
        if caso_base and \
                self.protocollatore_id.id == self.env.uid and \
                self.protocollatore_stato == "lavorazione":
            return False
        # caso 2:
        # - caso base
        # - l'utente corrente è un assegnatario per competenza la cui assegnazione è in stato preso_in_carico
        if caso_base and \
                self.check_state_assegnazione("competenza", "preso_in_carico", self.env.uid):
            return False
        return True

    def _compute_button_leggi_assegnazione_invisible(self):
        # - l'utente corrente ha profilo assegnatario
        # - l'utente corrente ha almeno un'assegnazione da prendere in visione
        # - il protocollo è in stato registrato o annullato
        if self.env.user.has_group('sd_protocollo.group_sd_protocollo_assegnatario') and \
                self.get_assegnazione_da_leggere_ids(self.env.uid) and \
                self.state in ["registrato", "annullato"]:
            return False
        return True

    def _compute_button_completa_lavorazione_stato_invisible(self):
        # caso base:
        # - l'utente corrente ha profilo assegnatario
        # - il protocollo è in stato registrato o annullato
        caso_base = self.env.user.has_group('sd_protocollo.group_sd_protocollo_assegnatario') and \
                    self.state in ["registrato", "annullato"]
        if not caso_base:
            return True
        # caso 1:
        # - caso base
        # - l'utente corrente è il protocollatore
        # - lo stato del protocollatore è in lavorazione
        if caso_base and self.protocollatore_id.id == self.env.uid and self.protocollatore_stato == "lavorazione":
            return False
        # caso 2:
        # - caso base
        # - l'utente corrente è un assegnatario e ha un'assegnazione da portare in lavorazione completata
        if caso_base and len(self.get_assegnazione_da_completare_lavorazione_ids(self.env.uid))>0:
            return False
        return True

    def _compute_button_rimetti_in_lavorazione_stato_invisible(self):
        # caso base:
        # - l'utente corrente ha profilo assegnatario
        # - il protocollo è in stato registrato o annullato
        caso_base = self.env.user.has_group('sd_protocollo.group_sd_protocollo_assegnatario') and \
                    self.state in ["registrato", "annullato"]
        if not caso_base:
            return True
        # caso 1:
        # - caso base
        # - l'utente corrente è il protocollatore
        # - lo stato del protocollatore è in lavorazione_completata
        if caso_base and \
                self.protocollatore_id.id == self.env.uid and \
                self.protocollatore_stato == "lavorazione_completata":
            return False
        # caso 2:
        # - caso base
        # - l'utente corrente è un assegnatario e ha un'assegnazione in lavorazione completata
        if caso_base and len(self.get_assegnazione_da_rimettere_in_lavorazione_ids(self.env.uid)) > 0:
            return False
        return True

    def _compute_button_aggiungi_allegati_invisible(self):
        ir_parameter_obj = self.env["ir.config_parameter"].sudo()
        # caso 1:
        # - il protocollo è in stato bozza
        if self.state == "bozza":
            return False
        # caso 2:
        # - l'utente corrente è il protocollatore
        # - lo stato del protocollatore è in lavorazione
        # - il protocollo è in stato registrato o annullato
        # - è abilitata la configurazione per aggiungere gli allegati dopo che il protocollo è stato registrato
        if self.protocollatore_id.id == self.env.uid and \
                self.protocollatore_stato == "lavorazione" and \
                self.state in ["registrato", "annullato"] and \
                bool(ir_parameter_obj.get_param("sd_protocollo.aggiungi_allegati_post_registrazione")):
            return False
        return True

    def _compute_button_modifica_allegati_invisible(self):
        # - il protocollo è in stato bozza
        if self.state == "bozza":
            return False
        return True

    def _compute_button_aggiungi_destinatario_invisible(self):
        # - il protocollo è in stato bozza
        # - il protocollo è in uscita
        if self.state == "bozza" and self.tipologia_protocollo == "uscita" and self.perm_write:
            return False
        return True

    def _compute_button_aggiungi_altro_soggetto_invisible(self):
        # - l'utente ha i permessi di scrittura
        if self.perm_write:
            return False
        return True

    def _compute_button_aggiungi_mittente_invisible(self):
        # - il protocollo è in stato bozza
        # - il protocollo è in ingresso
        # - il protocollo non ha un mittente
        if self.state == "bozza" and self.tipologia_protocollo == "ingresso" and len(self.mittente_ids) == 0:
            return False
        return True

    def _compute_button_modifica_mittente_invisible(self):
        # - il protocollo è in stato bozza
        # - il protocollo è in ingresso
        if self.state == "bozza" and self.tipologia_protocollo == "ingresso":
            return False
        return True

    def _compute_button_aggiungi_mittente_interno_invisible(self):
        # - il protocollo è in stato bozza
        # - il protocollo è in uscita
        # - il protocollo non ha un mittente interno
        if self.state == "bozza" and self.tipologia_protocollo == "uscita" and not self.mittente_interno_id:
            return False
        return True

    def _compute_button_elimina_mittente_interno_invisible(self):
        # - il protocollo è in stato bozza
        # - il protocollo è in uscita
        # - il protocollo ha un mittente interno
        if self.state == "bozza" and self.tipologia_protocollo == "uscita" and self.mittente_interno_id and self.perm_write:
            return False
        return True

    def _compute_button_etichetta_invisible(self):
        # - il protocollo è stato registrato o annullato
        if self.state in ["registrato", "annullato"]:
            return False
        return True

    def _compute_button_inserisci_segnatura_pdf_documento_invisible(self):
        # caso base:
        # - l'utente corrente ha profilo protocollatore
        # - l'utente corrente è il protocollatore
        # - lo stato del protocollatore è in lavorazione
        # - il protocollo è in stato registrato o annullato
        # - il protocollo contiene un documento pdf sul quale non è stata inserita la segnatura pdf
        caso_base = self.env.user.has_group('sd_protocollo.group_sd_protocollo_protocollatore') and \
                    self.env.uid == self.protocollatore_id.id and \
                    self.protocollatore_stato == "lavorazione" and \
                    self.state in ["registrato", "annullato"] and \
                    self.documento_id and \
                    self.documento_id.mimetype == "application/pdf" and \
                    not self.documento_id.protocollo_segnatura_pdf
        # caso 1:
        # - caso base
        # - gestione parametri di configurazione
        if caso_base and not self._get_config_inserisci_segnatura_pdf():
            return True

        return not caso_base

    def _compute_button_invia_invisible(self):
        # - l'utente corrente ha profilo protocollatore
        # - l'utente corrente è il protocollatore
        # - lo stato del protocollatore è in lavorazione
        # - il protocollo è in stato registrato o annullato
        # - il protocollo è marcato come da inviare
        # - il protocollo non ha ancora degli invii associati
        if self.env.user.has_group('sd_protocollo.group_sd_protocollo_protocollatore') and \
                self.env.uid == self.protocollatore_id.id and \
                self.protocollatore_stato == "lavorazione" and \
                self.state in ["registrato", "annullato"] and \
                self.da_inviare and \
                not self.invio_ids:
            return False
        return True

    def _compute_button_elimina_bozza_invisible(self):
        # - l'utente corrente è il protocollatore
        # - il protocollo è in stato bozza
        if self.env.uid == self.protocollatore_id.id and self.state == "bozza":
            return False
        return True

    @api.depends("tipologia_protocollo")
    def _compute_page_destinatari_ids_invisible(self):
        for protocollo in self:
            page_destinatari_ids_invisible = True
            if protocollo.tipologia_protocollo in ["uscita"]:
                page_destinatari_ids_invisible = False
            protocollo.page_destinatari_ids_invisible = page_destinatari_ids_invisible
