from odoo import models, _
from odoo.exceptions import ValidationError


class ProtocolloWizardActions(models.Model):
    _inherit = "sd.protocollo.protocollo"

    def protocollo_carica_documento_action(self):
        self.ensure_one()
        context = dict(
            self.env.context,
            protocollo_id=self.id
        )
        return {
            "name": context.get("wizard_label", ""),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "sd.protocollo.wizard.protocollo.carica.documento",
            "type": "ir.actions.act_window",
            "target": "new",
            "context": context
        }

    def protocollo_registra_action(self):
        self.ensure_one()
        context = dict(
            self.env.context,
            protocollo_id=self.id
        )
        html_errors = self._get_html_campi_obbligatori()
        if html_errors:
            return self.env.user._request_notify_message("danger", "Registrazione Protocollo", html_errors)
        return {
            "name": "Registra Protocollo",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "sd.protocollo.wizard.protocollo.registra",
            "type": "ir.actions.act_window",
            "target": "new",
            "context": context
        }

    def protocollo_annulla_action(self):
        self.ensure_one()
        if not self.button_annulla_invisible:
            context = dict(
                self.env.context,
                protocollo_id=self.id
            )
            return {
                "name": "Annulla Protocollo",
                "view_type": "form",
                "view_mode": "form",
                "res_model": "sd.protocollo.wizard.protocollo.annulla",
                "type": "ir.actions.act_window",
                "target": "new",
                "context": context
            }
        raise_string = "Non disponi delle autorizzazioni necessarie per annullare il protocollo %s. Contatta il " \
                       "Responsabile del protocollo per richiedere l'annullamento." % \
                       self.numero_protocollo
        if self.state in ["bozza", "annullato"]:
            raise_string = "Non è possibile annullare il protocollo: %s\n Il protocollo è in stato %s" % (
                self.numero_protocollo, self.state
            )
        self.env.user._request_notify_message("danger", "Annullamento Protocollo", raise_string, sticky=True)

    def protocollo_aggiungi_contatto_action(self):
        self.ensure_one()
        return self.documento_id.document_add_contact_action()

    def protocollo_aggiungi_mittente_interno_action(self):
        self.ensure_one()
        context = dict(
            self.env.context,
            company_id=self.company_id.id,
            display_field="path_name",
            protocollo_id=self.id
        )
        return {
            "name": context.get("wizard_label", ""),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "sd.protocollo.wizard.protocollo.add.mittente.in",
            "type": "ir.actions.act_window",
            "target": "new",
            "context": context
        }

    def protocollo_assegna_action(self):
        self.ensure_one()
        organigramma_obj = self.env["fl.set.voce.organigramma"]
        prima_assegnazione = self.is_prima_assegnazione(self.env.context.get("modifica_assegnatari", False))
        disable_ids = organigramma_obj.get_disable_ids(prima_assegnazione)
        assegnatario_disable_dictionary_ids = self.get_assegnatario_disable_dictionary_ids()
        assegnatario_competenza_disable_ids = disable_ids + assegnatario_disable_dictionary_ids["competenza"]
        assegnatario_conoscenza_disable_ids = disable_ids + assegnatario_disable_dictionary_ids["conoscenza"]
        context = dict(
            self.env.context,
            protocollo_id=self.id,
            company_id=self.company_id.id,
            assegnatario_competenza_disable_ids=assegnatario_competenza_disable_ids,
            assegnatario_conoscenza_disable_ids=assegnatario_conoscenza_disable_ids,
            stato_iniziale_assegnatari=self.assegnazione_parent_ids.ids,
            display_field="path_name",
            tipologia="aggiunta"
        )
        return {
            "name": context.get("wizard_label", ""),
            "view_type": "form",
            "view_mode": "form,tree",
            "res_model": "sd.protocollo.wizard.protocollo.assegna.step1",
            "type": "ir.actions.act_window",
            "target": "new",
            "context": context
        }

    def protocollo_assegna_conoscenza_action(self):
        self.ensure_one()
        organigramma_obj = self.env["fl.set.voce.organigramma"]
        prima_assegnazione = self.is_prima_assegnazione(self.env.context.get("modifica_assegnatari", False))
        disable_ids = organigramma_obj.get_disable_ids(prima_assegnazione)
        assegnatario_disable_dictionary_ids = self.get_assegnatario_disable_dictionary_ids("conoscenza")
        assegnatario_conoscenza_disable_ids = disable_ids + assegnatario_disable_dictionary_ids["conoscenza"]
        context = dict(
            self.env.context,
            company_id=self.company_id.id,
            protocollo_id=self.id,
            assegnatario_competenza_disable_ids=[],
            assegnatario_conoscenza_disable_ids=assegnatario_conoscenza_disable_ids,
            stato_iniziale_assegnatari=self.assegnazione_parent_ids.ids,
            display_field="path_name",
            tipologia="aggiunta_conoscenza"
        )
        return {
            "name": "Aggiungi Assegnatari Conoscenza",
            "view_type": "form",
            "view_mode": "form,tree",
            "res_model": "sd.protocollo.wizard.protocollo.assegna.step1",
            "type": "ir.actions.act_window",
            "target": "new",
            "context": context
        }

    def protocollo_prendi_in_carico_assegnazione_action(self):
        self.ensure_one()
        assegnazione_competenza_ids = self.get_assegnazione_ids("competenza", "assegnato", self.env.uid)
        if len(assegnazione_competenza_ids) == 0:
            errore = _("L'utente non ha assegnazioni per competenza nel protocollo!")
            raise ValidationError(errore)
        elif len(assegnazione_competenza_ids) > 1:
            errore = _("L'utente ha più di una assegnazione per competenza nel protocollo!")
            raise ValidationError(errore)
        esito, errore = self.prendi_in_carico_assegnazione(assegnazione_competenza_ids[0], self.env.uid)
        if not esito and errore:
            raise ValidationError(errore)

    def protocollo_rifiuta_assegnazione_action(self):
        self.ensure_one()
        assegnazione_competenza_ids = self.get_assegnazione_ids("competenza", "assegnato", self.env.uid)
        if len(assegnazione_competenza_ids) == 0:
            errore = _("L'utente non ha assegnazioni per competenza nel protocollo!")
            raise ValidationError(errore)
        elif len(assegnazione_competenza_ids) > 1:
            errore = _("L'utente ha più di una assegnazione per competenza nel protocollo!")
            raise ValidationError(errore)
        context = dict(
            self.env.context,
            protocollo_id=self.id,
            assegnazione_ids=assegnazione_competenza_ids
        )
        return {
            "name": "Rifiuta Assegnazione",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "sd.protocollo.wizard.protocollo.rifiuta.assegnazione",
            "type": "ir.actions.act_window",
            "target": "new",
            "context": context
        }

    def protocollo_riassegna_action(self):
        self.ensure_one()
        organigramma_obj = self.env["fl.set.voce.organigramma"]
        disable_ids = organigramma_obj.get_disable_ids(False)
        assegnazione_rifiutata_ids = self.get_assegnazione_assegnatore_ids("competenza", "rifiutato", self.env.uid)
        assegnatario_disable_dictionary_ids = self.get_assegnatario_disable_dictionary_ids(
            "competenza",
            assegnazione_to_exclude_ids=assegnazione_rifiutata_ids
        )
        assegnatario_competenza_disable_ids = disable_ids + assegnatario_disable_dictionary_ids["conoscenza"]
        context = dict(
            self.env.context,
            protocollo_id=self.id,
            company_id=self.company_id.id,
            assegnatario_competenza_disable_ids=assegnatario_competenza_disable_ids,
            stato_iniziale_assegnatari=self.assegnazione_parent_ids.ids,
            display_field="path_name"
        )
        return {
            "name": context.get("wizard_label", ""),
            "view_type": "form",
            "view_mode": "form,tree",
            "res_model": "sd.protocollo.wizard.protocollo.riassegna",
            "type": "ir.actions.act_window",
            "target": "new",
            "context": context
        }

    def protocollo_leggi_assegnazione_action(self):
        self.ensure_one()
        assegnazione_da_leggere_ids = self.get_assegnazione_da_leggere_ids(self.env.uid)
        if len(assegnazione_da_leggere_ids) == 0:
            errore = _("L'utente non ha assegnazioni da leggere nel protocollo!")
            raise ValidationError(errore)
        elif len(assegnazione_da_leggere_ids) == 1:
            esito, errore = self.leggi_assegnazione(assegnazione_da_leggere_ids[0], self.env.uid)
            if not esito and errore:
                raise ValidationError(errore)
        else:
            context = dict(
                self.env.context,
                protocollo_id=self.id,
                assegnazione_ids=assegnazione_da_leggere_ids
            )
            return {
                "name": "Lggi",
                "view_type": "form",
                "view_mode": "form,tree",
                "res_model": "sd.protocollo.wizard.protocollo.leggi",
                "type": "ir.actions.act_window",
                "target": "new",
                "context": context
            }

    def protocollo_completa_lavorazione_action(self):
        """
        La action permette di chiudere la lavorazione di un protocollo. Un protocollo può essere in lavorazione nei
        seguenti due casi

        - caso 1: l'utente è il protocollatore e il relativo stato del protocollatore è in lavorazione

        - caso 2: l'utente è un assegnatario per competenza la cui assegnazione è in stato preso_in_carico o letto_co
                  oppure è un assegnatario per conoscenza la cui assegnazione è in stato letto_cc

        Se i protocolli da mettere in lavorazione completata sono più di uno allora la action è stata chiamata dalla
        tree e di conseguenza si potrà chiudere la lavorazione solo se non deve essere inserita una motivazione e
        solamente per quei protocolli che soddisfano il caso 1 o il caso 2 e nel caso soddisfino solo il caso 2 devono
        avere una sola assegnazione. Per tutti i protocolli che non rientrano in tale descrizione dovrà essere lanciata
        la procedura singolarmente in modo da poter visualizzare il wizard.

        :return: None
        """
        protocollo_count = len(self.ids)
        config_obj = self.env["ir.config_parameter"].sudo()
        visualizza_motivazione = bool(config_obj.get_param("sd_protocollo.visualizza_motivazione_completa_lavorazione"))
        error_protocol_list = []
        for protocollo in self:
            is_protocollatore = protocollo.protocollatore_id.id == self.env.uid and \
                                protocollo.protocollatore_stato == "lavorazione"
            assegnazione_ids = protocollo.get_assegnazione_da_completare_lavorazione_ids(self.env.uid)
            if not is_protocollatore and len(assegnazione_ids) == 0:
                if protocollo_count > 1:
                    error_protocol_list.append(protocollo.anno_numero_protocollo)
                    continue
                errore = "L'utente non può completare la lavorazione del protocollo!"
                raise ValidationError(errore)
            if not visualizza_motivazione and is_protocollatore and len(assegnazione_ids) == 0:
                protocollo.completa_lavorazione_protocollatore(self.env.uid, None)
                continue
            if not visualizza_motivazione and not is_protocollatore and len(assegnazione_ids) == 1:
                protocollo.completa_lavorazione_assegnazione(assegnazione_ids[0], self.env.uid, None)
                continue
            if protocollo_count == 1:
                context = dict(
                    self.env.context,
                    protocollo_id=protocollo.id,
                    is_protocollatore=is_protocollatore,
                    assegnazione_ids=assegnazione_ids
                )
                return {
                    "name": "Completa lavorazione",
                    "view_type": "form",
                    "view_mode": "form,tree",
                    "res_model": "sd.protocollo.wizard.protocollo.completa.lavorazione",
                    "type": "ir.actions.act_window",
                    "target": "new",
                    "context": context
                }
        # Imposta lo stato per i protocolli non andati in errore e, se presenti, fa il raise dell'errore con i protocolli
        # in cui non è stato possibile
        self._cr.commit()
        if error_protocol_list:
            raise ValidationError("Nei seguenti protocolli non è stato possibile completare la procedura di completamento della lavorazione:\n%s" % "\n".join(error_protocol_list))

    def protocollo_rimetti_in_lavorazione_action(self):
        self.ensure_one()
        is_protocollatore = self.protocollatore_id.id == self.env.uid and self.protocollatore_stato == "lavorazione_completata"
        assegnazione_ids = self.get_assegnazione_da_rimettere_in_lavorazione_ids(self.env.uid)
        if not is_protocollatore and len(assegnazione_ids) == 0:
            errore = "L'utente non può rimettere in lavorazione il protocollo!"
            raise ValidationError(errore)
        if is_protocollatore and len(assegnazione_ids) == 0:
            return self.rimetti_in_lavorazione_protocollatore(self.env.uid, None)
        if not is_protocollatore and len(assegnazione_ids) == 1:
            return self.rimetti_in_lavorazione_assegnazione(assegnazione_ids[0], self.env.uid, None)
        context = dict(
            self.env.context,
            protocollo_id=self.id,
            is_protocollatore=is_protocollatore,
            assegnazione_ids=assegnazione_ids
        )
        return {
            "name": "Rimetti In Lavorazione",
            "view_type": "form",
            "view_mode": "form,tree",
            "res_model": "sd.protocollo.wizard.protocollo.rimetti.in.lavorazione",
            "type": "ir.actions.act_window",
            "target": "new",
            "context": context
        }

    def protocollo_invia_action(self):
        self.ensure_one()
        invio_obj = self.env["sd.protocollo.invio"]
        if self.mezzo_trasmissione_id:
            invio_obj.crea_invio_analogico(self.id, self.mezzo_trasmissione_id.id, self.destinatario_ids.ids)
            self.env.user._request_notify_message("success", "Invio Analogico", "Invio creato con successo")