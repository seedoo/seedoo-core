import logging
import threading

import werkzeug

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
import base64

_logger = logging.getLogger(__name__)


class ProtocolloActions(models.Model):
    _inherit = "sd.protocollo.protocollo"

    def registra(self):
        self.ensure_one()
        sequence_id = self.registro_id.sequence_id.id
        protocollo_id = self.id
        numero_protocollo = None

        if self.tipologia_registrazione == "normale":
            numero_protocollo = self._get_numero_protocollo_normale(self.env, sequence_id)
        elif self.tipologia_registrazione == "emergenza":
            numero_protocollo = self._get_numero_protocollo_emergenza(self.env, protocollo_id)

        if not numero_protocollo:
            raise ValidationError(_("Errore nel reperimento del numero del protocollo"))

        # se il numero di protocollo è stato recuperato correttamente allora si procede al salvataggio dei dati
        data_registrazione = fields.Datetime.now()
        # l'anno deve essere calcolato con la data di registrazione impostata con il timezone locale
        anno = self._get_local_date(data_registrazione).year
        self.write({
            "numero_protocollo": numero_protocollo,
            "state": "registrato",
            "data_registrazione": data_registrazione,
            "anno": anno,
            "anno_numero_protocollo": "%s%s" % (str(anno), numero_protocollo),
            "protocollatore_name": self.protocollatore_id.name,
            "protocollatore_ufficio_name": self.protocollatore_ufficio_id.name
        })

        self.env.cr.commit()

        errors = self.protocollo_registra_actions()

        try:
            prot = self.sudo().search_count([])
            if prot in [1, 10, 100, 1000] or prot % 1000 == 0:
                self.env["sd.dms.document"].get_instance_configuration("006", prot)
        except Exception:
            return errors

        return errors

    def protocollo_registra_actions(self):
        errors = {}
        try:
            segnatura_pdf_errors = self.inserisci_segnatura_pdf(False)
            if segnatura_pdf_errors:
                errors["segnatura_pdf"] = segnatura_pdf_errors
        except Exception as e:
            _logger.error(e)
            errors["segnatura_pdf"] = "Errore nell'inserimento della segnatura sui PDF"
        try:
            self.aggiorna_acl("registrazione", self.id)
        except Exception as e:
            _logger.error(e)

        try:
            self.rinomina_documenti()
        except Exception as e:
            _logger.error(e)
            errors["rinomina_documenti"] = "Errore nella rinominazione dei documenti"

        try:
            # creazione dello storico della action di registrazione del protocollo
            self.storico_registra()
            # creazione dello storico dei documenti (documento_id e allegato_ids)
            # for documento in self.allegato_ids:
            #     self.storico_documento(documento.filename, "allegato")
            # if self.documento_id:
            #     self.storico_documento(self.documento_id.filename, "documento")
        except Exception as e:
            _logger.error(e)
            errors["storico"] = "Errore nel salvataggio dello storico"

        return errors

    def inserisci_segnatura_pdf(self, raise_exception=True):
        self.ensure_one()

        errors = self.inserisci_segnatura_pdf_documento(raise_exception)
        return errors

    def inserisci_segnatura_pdf_documento(self, raise_exception=True):
        self.ensure_one()
        if not self._get_config_inserisci_segnatura_pdf():
            return
        errors = []

        if not self.documento_id:
            return errors
        self.documento_id.inserisci_segnatura_pdf(raise_exception)
        if not self.documento_id.protocollo_segnatura_pdf and self.documento_id.mimetype == "application/pdf":
            errors.append(_("Errore nella segnatura PDF del documento"))
        return errors

    def _get_config_inserisci_segnatura_pdf(self):
        config_param_obj = self.env["ir.config_parameter"].sudo()
        ingresso_param = bool(config_param_obj.get_param("sd_protocollo.segnatura_pdf_protocollo_ingresso"))
        uscita_param = bool(config_param_obj.get_param("sd_protocollo.segnatura_pdf_protocollo_uscita"))
        if not ingresso_param and self.tipologia_protocollo == "ingresso":
            return False
        if not uscita_param and self.tipologia_protocollo == "uscita":
            return False
        return True

    def _get_numero_protocollo_normale(self, env, sequence_id):
        sequence_obj = env["ir.sequence"]
        protocollo_obj = env["sd.protocollo.protocollo"]
        numero_protocollo = None
        try:
            sequence = sequence_obj.sudo().browse(sequence_id)
            ultimo_protocollo_data_list = protocollo_obj.sudo().search_read([
                ("state", "in", ["registrato", "annullato"]),
                ("registro_id.sequence_id", "=", sequence_id)
            ], ["data_registrazione"], limit=1, order="data_registrazione DESC")
            if ultimo_protocollo_data_list:
                data_corrente = fields.Datetime.now()
                ultima_data_registrazione = ultimo_protocollo_data_list[0]["data_registrazione"]
                if ultima_data_registrazione.year < data_corrente.year:
                    sequence.sudo().write({"number_next": 1})
            numero_protocollo = sequence.next_by_id()
        except Exception as e:
            _logger.error(e)
        return numero_protocollo

    def _get_numero_protocollo_emergenza(self, env, protocollo_id):
        self.ensure_one()
        registro_emergenza_numero_obj = env["sd.protocollo.registro.emergenza.numero"]
        registro_emergenza_obj = env["sd.protocollo.registro.emergenza"]
        protocollo = env["sd.protocollo.protocollo"].browse(protocollo_id)
        numero_protocollo = self._get_numero_protocollo_normale(env, protocollo.registro_id.sequence_id.id)
        try:
            registro_emergenza = registro_emergenza_obj.search(
                self._get_domain_numero_protocollo_emergenza(protocollo))

            registro_emergenza_numero_obj.create({
                "numero_protocollo": numero_protocollo,
                "registro_emergenza_id": registro_emergenza.id,
                "protocollo_id": protocollo_id
            })

            numero_protocolli = registro_emergenza_numero_obj.search_count(
                [("registro_emergenza_id", "=", registro_emergenza.id)])
            if numero_protocolli == registro_emergenza.numero_protocolli:
                registro_emergenza.state = "chiuso"

        except Exception as e:
            _logger.error(e)
        return numero_protocollo

    def _get_domain_numero_protocollo_emergenza(self, protocollo):
        return [("state", "=", "aperto")]

    def annulla(self, causa, responsabile, richiedente, data):
        self.ensure_one()
        if self.state == "annullato":
            raise ValidationError(_("Il protocollo è già stato annullato in precedenza!"))
        elif self.state != "registrato":
            raise ValidationError(_("Il protocollo deve essere in stato registrato per poter essere annullato!"))
        else:
            self.write({"state": "annullato"})
            self.storico_annulla(causa, responsabile, richiedente, data)

    def genera_etichetta(self):
        self.ensure_one()
        if self.button_etichetta_invisible:
            raise ValidationError("Il protocollo deve essere in stato registrato!")
        return {
            "type": "ir.actions.act_url",
            "url": "/protocollo/etichetta/%s" % str(self.id)
        }

    def _check_salva_documento_values(self, vals, field_list):
        errors = []
        for field in field_list:
            if not vals.get(field, False) or (vals.get(field, False) and not vals[field]):
                errors.append(field)
        return errors

    def _add_fields_to_recompute(self):
        return

    def rinomina_documenti(self):
        if self.env["ir.config_parameter"].sudo().get_param("sd_protocollo.rinomina_documento_allegati"):
            documento = self.documento_id
            if documento:
                documento.filename = self.get_filename_documento_protocollo(documento.filename, "Documento")
            for allegato in self.allegato_ids:
                self._get_allegato_filename(allegato)

    def _get_allegato_filename(self, allegato):
        allegato.filename = self.get_filename_documento_protocollo(allegato.filename, "Allegato")

    def salva_mittente_interno(self, mittente):
        self.ensure_one()

        self.write({
            "mittente_interno_id_char": str(mittente.id),
            "mittente_interno_nome": mittente.nome
        })

    def prendi_in_carico_assegnazione(self, assegnazione_id, utente_id):
        self.ensure_one()
        try:
            esito, errore = self._modifica_state_assegnazione("preso_in_carico", assegnazione_id, utente_id)
            if esito:
                self.storico_prendi_in_carico_assegnazione(utente_id)
        except Exception as e:
            return False, str(e)
        return esito, errore

    def rifiuta_assegnazione(self, assegnazione_id, utente_id, motivazione):
        self.ensure_one()
        try:
            esito, errore = self._modifica_state_assegnazione("rifiutato", assegnazione_id, utente_id, motivazione)
            if esito:
                self.rimetti_in_lavorazione_assegnatore(assegnazione_id, utente_id)
                self.storico_rifiuta_assegnazione(utente_id, motivazione)
                self.env.cr.commit()
                self.aggiorna_acl("rifiuto", self.id)
        except Exception as e:
            return False, str(e)
        return esito, errore

    def leggi_assegnazione(self, assegnazione_id, utente_id):
        assegnazione_obj = self.env["sd.protocollo.assegnazione"]
        self.ensure_one()
        try:
            state = "letto_cc"
            if assegnazione_obj.browse(assegnazione_id).tipologia == "competenza":
                state = "letto_co"
            esito, errore = self._modifica_state_assegnazione(state, assegnazione_id, utente_id)
            if esito:
                self.storico_leggi_assegnazione(utente_id)
        except Exception as e:
            return False, str(e)
        return esito, errore

    def completa_lavorazione_protocollatore(self, utente_id, motivazione):
        self.ensure_one()
        self.protocollatore_stato = "lavorazione_completata"
        self.storico_completa_lavorazione(utente_id, motivazione)

    def completa_lavorazione_assegnazione(self, assegnazione_id, utente_id, motivazione):
        self.ensure_one()
        try:
            esito, errore = self._modifica_state_assegnazione("lavorazione_completata", assegnazione_id, utente_id)
            if esito:
                self.storico_completa_lavorazione(utente_id, motivazione)
        except Exception as e:
            return False, str(e)
        return esito, errore

    def rimetti_in_lavorazione_protocollatore(self, utente_id, motivazione):
        self.ensure_one()
        self.protocollatore_stato = "lavorazione"
        self.storico_rimetti_in_lavorazione(utente_id, motivazione)

    def rimetti_in_lavorazione_assegnazione(self, assegnazione_id, utente_id, motivazione):
        self.ensure_one()
        try:
            state = "letto_cc"
            assegnazione = self.env["sd.protocollo.assegnazione"].browse(assegnazione_id)
            if assegnazione.presa_in_carico:
                state = "preso_in_carico"
            elif assegnazione.tipologia == "competenza":
                state = "letto_co"
            esito, errore = self._modifica_state_assegnazione(state, assegnazione_id, utente_id)
            if esito:
                self.storico_rimetti_in_lavorazione(utente_id, motivazione)
        except Exception as e:
            return False, str(e)
        return esito, errore

    def rimetti_in_lavorazione_assegnatore(self, assegnazione_id, utente_id):
        self.ensure_one()
        # metodo viene chiamato per rimettere in lavorazione lo stato dell'assegnatore nel caso in cui un'assegnazione
        # venga rifiutata. Questa procedura è fondamentale altrimenti se l'assegnazione viene rifiutata e l'assegnatore
        # non ha più il protocollo in lavorazione non si accorgerà mai del rifiuto perché il protocollo rifiutato non
        # viene conteggiato nella dashboard. Nel modulo che si occuperà di fare lo smistamento si dovrà estendere questo
        # metodo per considerare il caso in cui l'assegnatore non sia solo il protocollatore ma anche un assegnatario
        # per competenza
        if self.protocollatore_stato == "lavorazione":
            return
        self.protocollatore_stato = "lavorazione"

    def salva_assegnazione_competenza(self, assegnatario_ids, assegnatore_id, assegnatore_ufficio_id,
                                      assegnatario_to_replace_ids=[], delete=True, values={}):
        self.ensure_one()
        assegnazione_obj = self.env["sd.protocollo.assegnazione"]

        assegnazione_obj.verifica_assegnazione_competenza(assegnatario_ids)

        old_assegnazione_list = assegnazione_obj.search_read([
            ("protocollo_id", "=", self.id),
            ("tipologia", "=", "competenza"),
            ("parent_id", "=", False)
        ], ["assegnatario_id"])

        if old_assegnazione_list:
            old_assegnatario_ids = []
            for old_assegnazione in old_assegnazione_list:
                old_assegnatario_ids.append(old_assegnazione["assegnatario_id"][0])

            assegnatario_to_create_ids = assegnazione_obj.get_assegnatario_to_create_ids(
                assegnatario_ids, old_assegnatario_ids, assegnatario_to_replace_ids
            )
            assegnatario_to_unlink_ids = assegnazione_obj.get_assegnatario_to_unlink_ids(
                assegnatario_ids, old_assegnatario_ids, assegnatario_to_replace_ids
            )
        else:
            assegnatario_to_create_ids = assegnatario_ids
            assegnatario_to_unlink_ids = []

        if assegnatario_to_unlink_ids and delete:
            # eliminazione delle vecchie assegnazioni (eventuali figli vengono eliminati a cascata)
            assegnazione_to_unlink = assegnazione_obj.search([
                ("protocollo_id", "=", self.id),
                ("tipologia", "=", "competenza"),
                ("assegnatario_id", "in", assegnatario_to_unlink_ids),
                ("parent_id", "=", False)
            ])
            if assegnazione_to_unlink:
                assegnazione_to_unlink.unlink()

        if assegnatario_to_create_ids:
            # creazione della nuova assegnazione
            assegnazione_obj.crea_assegnazioni(
                self.id, assegnatario_to_create_ids, assegnatore_id, assegnatore_ufficio_id, "competenza", values
            )

        if self.state in ["registrato", "annullato"] and (assegnatario_to_unlink_ids or assegnatario_to_create_ids):
            self.env["sd.protocollo.protocollo"].aggiorna_acl("assegnazione", self.id)

    def salva_assegnazione_conoscenza(self, assegnatario_ids, assegnatore_id, assegnatore_ufficio_id, delete=True,
                                      values={}):
        self.ensure_one()
        assegnazione_obj = self.env["sd.protocollo.assegnazione"]

        old_assegnazione_list = assegnazione_obj.search_read([
            ("protocollo_id", "=", self.id),
            ("tipologia", "=", "conoscenza"),
            ("parent_id", "=", False)
        ], ["assegnatario_id"])

        if old_assegnazione_list:
            old_assegnatario_ids = []
            for old_assegnazione in old_assegnazione_list:
                old_assegnatario_ids.append(old_assegnazione["assegnatario_id"][0])

            assegnatario_to_create_ids = list(set(assegnatario_ids) - set(old_assegnatario_ids))
            assegnatario_to_unlink_ids = list(set(old_assegnatario_ids) - set(assegnatario_ids))
        else:
            assegnatario_to_create_ids = assegnatario_ids
            assegnatario_to_unlink_ids = []

        if assegnatario_to_unlink_ids and delete:
            # eliminazione delle vecchie assegnazioni (eventuali figli vengono eliminati a cascata)
            assegnazione_to_unlink = assegnazione_obj.search([
                ("protocollo_id", "=", self.id),
                ("tipologia", "=", "conoscenza"),
                ("assegnatario_id", "in", assegnatario_to_unlink_ids)
            ])
            if assegnazione_to_unlink:
                assegnazione_to_unlink.unlink()

        if assegnatario_to_create_ids:
            # creazione della nuova assegnazione
            assegnazione_obj.crea_assegnazioni(
                self.id, assegnatario_to_create_ids, assegnatore_id, assegnatore_ufficio_id, "conoscenza", values=values
            )

        if self.state in ["registrato", "annullato"] and \
                ((assegnatario_to_unlink_ids and delete) or assegnatario_to_create_ids):
            self.env["sd.protocollo.protocollo"].aggiorna_acl("assegnazione", self.id)

    def elimina_assegnazione(self, assegnazione_id, motivazione=False):
        self.ensure_one()
        assegnazione_obj = self.env["sd.protocollo.assegnazione"]
        assegnazione = assegnazione_obj.browse(assegnazione_id)
        if motivazione:
            self.storico_elimina_assegnazione(assegnazione.assegnatario_id.id, assegnazione.tipologia, motivazione)
        assegnazione.unlink()
        if self.state in ["registrato", "annullato"]:
            self.aggiorna_acl("assegnazione", self.id)

    def _modifica_state_assegnazione(self, state, assegnazione_id, utente_id, motivazione_rifiuto=None):
        self.ensure_one()
        data = fields.Datetime.now()
        assegnazione_obj = self.env["sd.protocollo.assegnazione"]
        assegnazione = assegnazione_obj.browse(assegnazione_id)
        # si recupera la lista degli stati successivi allo stato dell'assegnazione
        next_state_assegnazione_list = assegnazione_obj.get_next_state_list(assegnazione.state)
        # si controlla se lo stato da modificare è uno stato successivo allo stato attuale dell'assegnazione oppure che
        # lo stato da modificare sia letto_co o letto_cc e lo si debba salvare su un'assegnazione di un ufficio
        caso1 = not (state in next_state_assegnazione_list)
        caso2 = not (state in ["letto_co", "letto_cc"] and assegnazione.assegnatario_tipologia == "ufficio")
        if caso1 and caso2:
            errore = _(
                "Non è più possibile eseguire l'operazione richiesta! L'assegnazione è in stato %s" %
                assegnazione.state
            )
            return False, errore
        vals = {
            "state": state,
            "motivazione_rifiuto": motivazione_rifiuto,
            "data": data
        }
        if state == "preso_in_carico" and assegnazione.tipologia == "competenza":
            vals["presa_in_carico"] = True
            vals["presa_in_carico_attuale"] = True
        # se l'assegnazione è fatta all'utente l'unica operazione da fare è modificare lo stato dell'assegnazione
        if assegnazione.assegnatario_tipologia == "utente":
            assegnazione.write(vals)
            return True, None
        # se l'assegnazione è fatta all'ufficio si deve prima verificare se esiste l'assegnazione relativa all'utente
        ufficio_id = assegnazione.assegnatario_ufficio_id.id
        assegnazione_child = None
        for child in assegnazione.child_ids:
            if child.assegnatario_utente_id.id == utente_id:
                assegnazione_child = child
        # se l'assegnazione all'utente non esiste allora la si deve creare
        if not assegnazione_child:
            # si ricerca l'id dell'assegnatario associato all'utente
            assegnatario_list = self.env["fl.set.voce.organigramma"].search_read([
                ("tipologia", "=", "utente"),
                ("utente_id", "=", utente_id),
                ("parent_id.ufficio_id", "=", ufficio_id),
            ], ["id"])
            if not assegnatario_list:
                errore = _("Non è stato trovato l'assegnatario associato all'utente")
                return False, errore
            assegnatario_id = assegnatario_list[0]["id"]
            assegnazione_child = assegnazione_obj.crea_assegnazione(
                self.id,
                assegnatario_id,
                assegnazione.assegnatore_id.id,
                assegnazione.assegnatore_parent_id.id,
                assegnazione.tipologia,
                assegnazione.id
            )
        # si modifica lo stato per l'assegnazione dell'utente associato all'ufficio
        assegnazione_child.write(vals)
        # si deve modificare anche lo stato dell'assegnazione dell'ufficio se almeno uno dei seguenti casi è verificato:
        # - caso 1: si sta modificando un'assegnazione per competenza di un ufficio con uno stato diverso da
        #           letto_co
        # - caso 2: si sta modificando un'assegnazione per conoscenza di un ufficio, dove lo stato da impostare è
        #           letto_cc e lo stato corrente è lavorazione_completata oppure se lo stato da impostare è
        #           lavorazione_completata si deve verificare che all'interno dell'ufficio non rimane più nessun utente
        #           che debba effettuare la stessa modifica di stato
        caso1 = assegnazione.tipologia == "competenza" and state != "letto_co"
        caso2 = assegnazione.tipologia == "conoscenza" and \
                assegnazione.state == "lavorazione_completata" and \
                state == "letto_cc"
        if not caso2:
            assegnazione_conoscenza_list = assegnazione_obj.search_read([
                ("protocollo_id", "=", self.id),
                ("tipologia", "=", "conoscenza"),
                ("parent_id", "=", assegnazione.id),
                ("state", "in", [state] + next_state_assegnazione_list)
            ], ["assegnatario_utente_id"])
            ufficio_utente_ids = [a["assegnatario_utente_id"][0] for a in assegnazione_conoscenza_list]
            caso2 = len(self.env["res.users"].search_read([
                ("id", "not in", ufficio_utente_ids),
                ("fl_set_set_ids", "=", assegnazione.assegnatario_ufficio_id.id)
            ], ["id"])) == 0
        if caso1 or caso2:
            assegnazione.write(vals)
        return True, None

    def get_assegnazione_assegnatore_ids(self, tipologia_assegnazione, state, utente_id):
        self.ensure_one()
        assegnazione_obj = self.env["sd.protocollo.assegnazione"]
        # si ricercano le assegnazioni fatte dall'utente
        assegnazione_assegnatore_list = assegnazione_obj.search_read([
            ("protocollo_id", "=", self.id),
            ("tipologia", "=", tipologia_assegnazione),
            ("state", "=", state),
            ("assegnatore_id", "=", utente_id),
            ("parent_id", "=", False)
        ], ["id"])
        assegnazione_assegnatore_ids = [a["id"] for a in assegnazione_assegnatore_list]
        return assegnazione_assegnatore_ids

    def get_assegnazione_da_leggere_ids(self, utente_id):
        """
        Le assegnazioni da prendere in visione rientrano in 3 casi:

        - caso 1: assegnazioni per conoscenza fatte direttamente all'utente

        - caso 2: assegnazioni per conoscenza fatte all'ufficio dell'utente ma non ancora prese in visione dall'utente

        - caso 3: (solo se abilita_lettura_assegnazione_competenza è a True) assegnazioni per competenza fatte all'
                  ufficio dell'utente x ma prese in carico o con la lavorazione completata da un altro utente dello
                  stesso ufficio. Le assegnazioni non devono essere ancora prese in visione dall'utente x e non deve
                  aver preso in carico un'altra assegnazione per competenza a lui fatta tramite altro flusso (ad esempio
                  tramite smistamento)

        :param utente_id: id dell'utente di cui recuperare le assegnazioni da leggere
        :return: lista degli id delle assegnazioni da leggere
        """
        assegnazione_obj = self.env["sd.protocollo.assegnazione"]
        # ricerca le assegnazioni del caso 1
        assegnazione_caso1_ids = self._get_assegnazione_utente_ids("conoscenza", "assegnato", utente_id)
        # ricerca le assegnazioni del caso 2
        assegnazione_caso2_ids = []
        utente = self.env["res.users"].browse(utente_id)
        for ufficio_id in utente.fl_set_set_ids.ids:
            assegnazione_caso2_ids += self._get_assegnazione_ufficio_ids("conoscenza", "assegnato", ufficio_id,
                                                                         utente_id)
        assegnazione_utente_letto_cc_list = assegnazione_obj.search_read([
            ("protocollo_id", "=", self.id),
            ("tipologia", "=", "conoscenza"),
            ("state", "in", assegnazione_obj.get_next_state_list("assegnato")),
            ("assegnatario_utente_id", "=", utente_id),
            ("parent_id", "in", assegnazione_caso2_ids)
        ], ["parent_id"])
        for assegnazione_utente_letto_cc in assegnazione_utente_letto_cc_list:
            if assegnazione_utente_letto_cc["parent_id"][0] in assegnazione_caso2_ids:
                assegnazione_caso2_ids.remove(assegnazione_utente_letto_cc["parent_id"][0])
        # ricerca le assegnazioni del caso 3 (solo se abilita_lettura_assegnazione_competenza è a True)
        assegnazione_caso3_ids = []
        config_obj = self.env["ir.config_parameter"].sudo()
        if bool(config_obj.get_param("sd_protocollo.abilita_lettura_assegnazione_competenza")):
            # si recuperano tutti gli uffici associati all'utente corrente che dovranno essere usati nella ricerca delle
            # assegnazioni del caso 3
            ufficio_ids = utente.fl_set_set_ids.ids
            # si ricercano tutte le assegnazioni per competenza associate all'utente corrente in modo da rimuovere il
            # relativo ufficio dalla lista degli uffici da usare nella ricerca. Infatti se esiste già un'assegnazione
            # per competenza associata all'utente con riferimento ad un ufficio (l'utente potrebbe aver già preso
            # visione dell'assegnazione oppure potrebbe aver ricevuto un'assegnazione diretta per smistamento), non ha
            # senso che l'assegnazione dello stesso ufficio sia inserita fra quelle da prendere in visione
            assegnazione_competenza_utente_list = assegnazione_obj.search_read([
                ("protocollo_id", "=", self.id),
                ("tipologia", "=", "competenza"),
                ("assegnatario_utente_id", "=", utente_id)
            ], ["assegnatario_utente_parent_id"])
            for assegnazione_competenza_utente in assegnazione_competenza_utente_list:
                # se l'ufficio associato all'utente relativo all'assegnazione è presente nella
                if assegnazione_competenza_utente["assegnatario_utente_parent_id"][0] in ufficio_ids:
                    ufficio_ids.remove(assegnazione_competenza_utente["assegnatario_utente_parent_id"][0])
            # ricerca la lista delle assegnazioni per competenza con stato preso_in_carico o lavorazione_completata
            # associate ad un ufficio dell'utente
            assegnazione_ufficio_list = assegnazione_obj.search_read([
                ("protocollo_id", "=", self.id),
                ("tipologia", "=", "competenza"),
                ("state", "in", ["preso_in_carico", "lavorazione_completata"]),
                ("assegnatario_ufficio_id", "in", ufficio_ids),
                ("parent_id", "=", False)
            ], ["id"])
            for assegnazione_ufficio in assegnazione_ufficio_list:
                assegnazione_caso3_ids.append(assegnazione_ufficio["id"])
        return assegnazione_caso1_ids + assegnazione_caso2_ids + assegnazione_caso3_ids

    def get_assegnazione_da_completare_lavorazione_ids(self, utente_id):
        assegnazione_obj = self.env["sd.protocollo.assegnazione"]
        # le assegnazione da portare in lavorazione completata rientrano in due casi
        # caso 1: l'utente è un assegnatario per competenza la cui assegnazione è in stato preso_in_carico o letto_co
        # caso 2: l'utente è un assegnatario per conoscenza la cui assegnazione è in stato letto_cc
        assegnazione_competenza_utente_list = assegnazione_obj.search_read([
            ("protocollo_id", "=", self.id),
            ("tipologia", "=", "competenza"),
            ("state", "in", ["preso_in_carico", "letto_co"]),
            ("assegnatario_utente_id", "=", utente_id)
        ], ["id", "parent_id", "state"])
        # iteriamo sulle assegnazioni per competenza in stato lavorazione o letto_co assegnate all'utente. Se
        # l'assegnazione è in stato lavorazione e ha un parent allora si prende il parent come assegnazione da spostare
        # in lavorazione_completata, nei restanti casi si prende l'assegnazione stessa perché lo stato da modificare
        # deve essere solamente il suo e non quello dell'eventuale assegnazione parent
        assegnazione_caso1_ids = []
        for assegnazione_competenza_utente in assegnazione_competenza_utente_list:
            if assegnazione_competenza_utente["state"] == "preso_in_carico" and assegnazione_competenza_utente[
                "parent_id"]:
                assegnazione_caso1_ids.append(assegnazione_competenza_utente["parent_id"][0])
            else:
                assegnazione_caso1_ids.append(assegnazione_competenza_utente["id"])
        assegnazione_conoscenza_utente_list = assegnazione_obj.search_read([
            ("protocollo_id", "=", self.id),
            ("tipologia", "=", "conoscenza"),
            ("state", "=", "letto_cc"),
            ("assegnatario_utente_id", "=", utente_id)
        ], ["id", "parent_id"])
        # iteriamo sulle assegnazioni per conoscenza in stato letto_co assegnate all'utente, se l'assegnazione ha
        # un parent si considera tale id, altrimenti si prende l'id dell'assegnazione stessa
        assegnazione_caso2_ids = []
        for assegnazione_conoscenza_utente in assegnazione_conoscenza_utente_list:
            if assegnazione_conoscenza_utente["parent_id"]:
                assegnazione_caso2_ids.append(assegnazione_conoscenza_utente["parent_id"][0])
            else:
                assegnazione_caso2_ids.append(assegnazione_conoscenza_utente["id"])
        assegnazione_da_completare_lavorazione_ids = assegnazione_caso1_ids + assegnazione_caso2_ids
        return assegnazione_da_completare_lavorazione_ids

    def get_assegnazione_da_rimettere_in_lavorazione_ids(self, utente_id):
        assegnazione_obj = self.env["sd.protocollo.assegnazione"]
        # le assegnazione da rimettere in lavorazione rientrano in due casi
        # caso 1: l'utente è un assegnatario per competenza la cui assegnazione è in stato lavorazione_completata
        # caso 2: l'utente è un assegnatario per conoscenza la cui assegnazione è in stato lavorazione_completata
        assegnazione_competenza_utente_list = assegnazione_obj.search_read([
            ("protocollo_id", "=", self.id),
            ("tipologia", "=", "competenza"),
            ("state", "=", "lavorazione_completata"),
            ("assegnatario_utente_id", "=", utente_id)
        ], ["id", "parent_id", "presa_in_carico"])
        # iteriamo sulle assegnazioni per competenza in stato lavorazione_completata assegnate all'utente. Se
        # l'assegnazione ha il campo_presa_in_carico a True e ha un parent allora si prende il parent come assegnazione
        # da spostare in lavorazione, nei restanti casi si prende l'assegnazione stessa perché lo stato da modificare
        # deve essere solamente il suo e non quello dell'eventuale assegnazione parent
        assegnazione_caso1_ids = []
        for assegnazione_competenza_utente in assegnazione_competenza_utente_list:
            if assegnazione_competenza_utente["presa_in_carico"] and assegnazione_competenza_utente["parent_id"]:
                assegnazione_caso1_ids.append(assegnazione_competenza_utente["parent_id"][0])
            else:
                assegnazione_caso1_ids.append(assegnazione_competenza_utente["id"])
        assegnazione_conoscenza_utente_list = assegnazione_obj.search_read([
            ("protocollo_id", "=", self.id),
            ("tipologia", "=", "conoscenza"),
            ("state", "=", "lavorazione_completata"),
            ("assegnatario_utente_id", "=", utente_id)
        ], ["id", "parent_id"])
        # iteriamo sulle assegnazioni per conoscenza in stato lavorazione_completata assegnate all'utente, se
        # l'assegnazione ha un parent si considera tale id, altrimenti si prende l'id dell'assegnazione stessa
        assegnazione_caso2_ids = []
        for assegnazione_conoscenza_utente in assegnazione_conoscenza_utente_list:
            if assegnazione_conoscenza_utente["parent_id"]:
                assegnazione_caso2_ids.append(assegnazione_conoscenza_utente["parent_id"][0])
            else:
                assegnazione_caso2_ids.append(assegnazione_conoscenza_utente["id"])
        assegnazione_da_completare_lavorazione_ids = assegnazione_caso1_ids + assegnazione_caso2_ids
        return assegnazione_da_completare_lavorazione_ids

    def check_state_assegnazione(self, tipologia_assegnazione, state, utente_id):
        if self._get_assegnazione_utente_ids(tipologia_assegnazione, state, utente_id):
            return True
        # ricerca le assegnazioni per l'ufficio dell'utente corrente
        utente = self.env["res.users"].browse(utente_id)
        for ufficio_id in utente.fl_set_set_ids.ids:
            if self._get_assegnazione_ufficio_ids(tipologia_assegnazione, state, ufficio_id, utente_id):
                return True
        return False

    def get_assegnazione_ids(self, tipologia_assegnazione, state, utente_id):
        # ricerca le assegnazioni per l'utente corrente
        ass_com_ids = self._get_assegnazione_utente_ids(tipologia_assegnazione, state, utente_id)
        # ricerca le assegnazioni per l'ufficio dell'utente corrente
        utente = self.env["res.users"].browse(utente_id)
        for ufficio_id in utente.fl_set_set_ids.ids:
            ass_com_ufficio_ids = self._get_assegnazione_ufficio_ids(tipologia_assegnazione, state, ufficio_id,
                                                                     utente_id)
            ass_com_ids = ass_com_ids + ass_com_ufficio_ids
        return ass_com_ids

    def _get_assegnazione_utente_ids(self, tipologia_assegnazione, state, utente_id):
        self.ensure_one()
        assegnazione_obj = self.env["sd.protocollo.assegnazione"]
        # si ricercano le assegnazioni fatte direttamente sull'utente
        assegnazione_competenza_utente_list = assegnazione_obj.search_read([
            ("protocollo_id", "=", self.id),
            ("tipologia", "=", tipologia_assegnazione),
            ("state", "=", state),
            ("assegnatario_utente_id", "=", utente_id),
            ("parent_id", "=", False)
        ], ["id"])
        assegnazione_competenza_utente_ids = [a["id"] for a in assegnazione_competenza_utente_list]
        return assegnazione_competenza_utente_ids

    def _get_assegnazione_ufficio_ids(self, tipologia_assegnazione, state, ufficio_id, utente_id):
        self.ensure_one()
        assegnazione_obj = self.env["sd.protocollo.assegnazione"]
        # se lo stato è assegnato si ricercano le assegnazioni fatte all'ufficio dell'utente perché le assegnazioni
        # dell'utente potrebbero non esistere
        if state == 'assegnato':
            assegnazione_ufficio_list = assegnazione_obj.search_read([
                ("protocollo_id", "=", self.id),
                ("tipologia", "=", tipologia_assegnazione),
                ("state", "=", state),
                ("assegnatario_ufficio_id", "=", ufficio_id),
                ("parent_id", "=", False)
            ], ["id"])
            assegnazione_ufficio_ids = [a["id"] for a in assegnazione_ufficio_list]
            return assegnazione_ufficio_ids
        # altrimenti si ricercano le assegnazioni per utente il cui parent_id è valorizzato, si itera sulle assegnazioni
        # trovate e si recupera il relativo parent_id
        assegnazione_utente_list = assegnazione_obj.search_read([
            ("protocollo_id", "=", self.id),
            ("tipologia", "=", tipologia_assegnazione),
            ("state", "=", state),
            ("assegnatario_utente_id", "=", utente_id),
            ("assegnatario_utente_parent_id", "=", ufficio_id),
            ("parent_id", "!=", False)
        ], ["id", "parent_id"])
        assegnazione_competenza_ufficio_ids = [a["parent_id"][0] for a in assegnazione_utente_list]
        return assegnazione_competenza_ufficio_ids

    def is_prima_assegnazione(self, modifica_assegnatari=False):
        self.ensure_one()
        # se il protocollo non è registrato è sicuramente la prima assegnazione
        if not self.data_registrazione:
            return True
        # se il protocollo è registrato ma non ha assegnazioni per competenza e la procedura non è stata chiamata da un
        # utente che ha il permesso di modifica assegnatari, allora è una prima assegnazione
        if self.assegnazione_competenza_ids.ids == [] and not modifica_assegnatari:
            return True
        # se nessuno dei precedenti casi è verificato allora è un'assegnazione successiva alla prima
        return False

    def get_assegnatario_disable_dictionary_ids(self, action_tipologia=None, tipologia=None, assegnazione_to_exclude_ids=[]):
        self.ensure_one()
        config_obj = self.env["ir.config_parameter"].sudo()
        assegnatario_disable_dictionary_ids = {
            "competenza": [],
            "conoscenza": []
        }
        stesso_ufficio = bool(config_obj.get_param("sd_protocollo.abilita_assegnazione_stesso_utente_ufficio"))
        if not stesso_ufficio and action_tipologia != "riassegnazione" and self.tipologia_protocollo in ["ingresso",
                                                                                                         "uscita"]:
            assegnatario_disable_ids = self._get_assegnatario_disable_ids(
                self.assegnazione_parent_ids, assegnazione_to_exclude_ids=assegnazione_to_exclude_ids
            )
            assegnatario_disable_dictionary_ids["competenza"] = assegnatario_disable_ids
            assegnatario_disable_dictionary_ids["conoscenza"] = assegnatario_disable_ids
            return assegnatario_disable_dictionary_ids
        if not tipologia or tipologia == "competenza":
            assegnatario_disable_ids = self._get_assegnatario_disable_ids(
                self.assegnazione_competenza_ids, assegnazione_to_exclude_ids=assegnazione_to_exclude_ids
            )
            assegnatario_disable_dictionary_ids["competenza"] = assegnatario_disable_ids
        if not tipologia or tipologia == "conoscenza":
            assegnatario_disable_ids = self._get_assegnatario_disable_ids(
                self.assegnazione_conoscenza_ids, assegnazione_to_exclude_ids=assegnazione_to_exclude_ids
            )
            assegnatario_disable_dictionary_ids["conoscenza"] = assegnatario_disable_ids
        return assegnatario_disable_dictionary_ids

    @api.model
    def _get_assegnatario_disable_ids(self, assegnazione_list, assegnazione_to_exclude_ids=[]):
        assegnatario_disable_ids = []
        for assegnazione in assegnazione_list:
            if assegnazione.id in assegnazione_to_exclude_ids:
                continue
            assegnatario_disable_ids.append(assegnazione.assegnatario_id.id)
            # se l'assegnazione è di tipo ufficio allora anche gli utenti appartenenti non deveno essere selezionabili
            if assegnazione.assegnatario_tipologia == "ufficio":
                for child in assegnazione.assegnatario_id.child_ids:
                    if child.tipologia == "utente":
                        assegnatario_disable_ids.append(child.id)
            # se l'assegnazione è di tipo utente e non appartiene a nessuna assegnazione di tipo ufficio allora anche
            # l'ufficio di appartenenza dell'utente non deve essere selezionabile, mentre gli altri utenti appartenenti
            # all'ufficio possono esserlo
            if assegnazione.assegnatario_tipologia == "utente" and \
                    not assegnazione.parent_id and \
                    assegnazione.assegnatario_id.parent_id:
                assegnatario_disable_ids.append(assegnazione.assegnatario_id.parent_id.id)
        return assegnatario_disable_ids

    def error_get(self, error):
        error_dict = {
            "protocollatore_ufficio_id": "Ufficio del Protocollo",
            "protocollatore_id": "Protocollatore",
            "protocollatore_not_ufficio": "Protocollatore: non è associato a nessun ufficio",
            "mezzo_trasmissione_id": "Mezzo Trasmissione",
            "oggetto": "Oggetto",
            "mittente_interno_id": "Mittente",
            "mittente_ids": "Mittente: i protocolli in ingresso possono avere solo un mittente",
            "mittente_name": "Nome Cognome/Ragione sociale del Mittente",
            "documento_id": "Documento",
            "documento_id_allegati": "Documento (obbligatorio se sono presenti allegati)",
            "data_ricezione": "Data Ricezione",
            "fascicolario_id": "Fascicolario",
            "reserved_not_uffici": "Dipendente Assegnatario per Competenza: i protocollo riservati non possono avere uffici come assegnatari per competenza",
            "reserved_dipendente_assegnatario": "Dipendente Assegnatario per Competenza",
            "conoscenza_found": "Assegnatari per Conoscenza: i protocolli riservati non possono avere assegnatari per conoscenza",
            "mittente_is_office": "Mittente: i protocolli riservati non possono avere uffici come mittenti",
            "ufficio_assegnatario_competenza": "Ufficio Assegnatario per Competenza",
            "dipendente_assegnatario_competenza": "Dipendente Assegnatario per Competenza",
            "assegnatario_competenza": "Assegnatario per Competenza",
            "uffici_assegnatario_conoscenza": "Uffici Assegnatari per Conoscenza",
            "dipendente_assegnatario_conoscenza": "Dipendenti Assegnatari per Conoscenza",
            "documento_document_type": _("The main document doesn't have a document type associated"),
            "allegati_document_type": _(
                "There are attachments (<b>%s</b>) that doesn't have a document type associated"),
            "allegato_document_type": _("The attachment <b>%s</b> doesn't have a document type associated")
        }
        return error_dict.get(error, False)

    @api.model
    def verifica_campi_obbligatori_non_configurati(self):
        self.ensure_one()
        errors_list = []

        common_conditions_list = [
            (self.tipologia_protocollo in ["ingresso", "uscita"]),
            (self.tipologia_protocollo == "ingresso"),
            (self.tipologia_protocollo == "uscita"),
        ]

        conditions_list = [
            (not self.protocollatore_ufficio_id, "protocollatore_ufficio_id"),
            (not self.documento_id_content, "documento_id"),
            (not self.documento_id and self.allegato_ids, "documento_id_allegati"),
            (not self.protocollatore_id, "protocollatore_id"),
            (not self.documento_id_oggetto, "oggetto"),
            (self.tipologia_protocollo != "ingresso" and not self.mittente_interno_id, "mittente_interno_id"),
            (self.protocollatore_id and self.protocollatore_ufficio_id and not self.protocollatore_id.fl_set_set_ids,
             "protocollatore_not_ufficio"),
            (common_conditions_list[0] and not self.mezzo_trasmissione_id, "mezzo_trasmissione_id"),
        ]

        for condition in conditions_list:
            if condition[0]:
                error = _(self.error_get(condition[1]))
                errors_list.append(error and error or None)

        if common_conditions_list[1] and len(self.mittente_ids) > 1:
            errors_list.append(_(self.error_get("mittente_ids")))

        if common_conditions_list[0] and not self.destinatario_ids:
            if not self.mittente_ids and not self.mittente_interno_id:
                send_rec = common_conditions_list[1] and _("Mittente") or _("Destinatari")
                errors_list.append(send_rec)

        if common_conditions_list[1] and self.mezzo_trasmissione_id:
            for mittente in self.mittente_ids:
                if not mittente.name:
                    errors_list.append(_(self.error_get("mittente_name")))
                    break
        if self.tipologia_protocollo == "uscita":
            if not self.destinatario_ids and "Destinatari" not in errors_list:
                errors_list.append(_("Destinatari"))



        return errors_list

    @api.model
    def verifica_campi_obbligatori(self):
        errors = self.verifica_campi_obbligatori_non_configurati()
        document_errors = self.documento_id.verifica_campi_obbligatori()
        if document_errors:
            errors.extend(document_errors)
        config = {}

        ir_config_obj = self.env['ir.config_parameter'].sudo()

        required_fields_list = [
            "required_assegnatari_competenza_uffici",
            "required_assegnatari_competenza_dipendenti", "required_assegnatari_conoscenza_uffici",
            "required_assegnatari_conoscenza_dipendenti", "required_data_ricezione",
            "required_assegnatari_competenza_uffici_senza_doc", "required_assegnatari_competenza_dipendenti_senza_doc",
            "required_assegnatari_conoscenza_uffici_senza_doc", "required_assegnatari_conoscenza_dipendenti_senza_doc",
        ]

        for field in required_fields_list:
            value = ir_config_obj.get_param("sd_protocollo.%s" % field)
            config.update({field: bool(value)})

        competenza_ufficio_found = False
        competenza_dipendente_found = False
        conoscenza_ufficio_found = False
        conoscenza_dipendente_found = False

        for assegnazione in self.assegnazione_ids:
            if assegnazione.tipologia == 'competenza' and assegnazione.assegnatario_tipologia == "ufficio":
                competenza_ufficio_found = True
            if assegnazione.tipologia == 'competenza' and assegnazione.assegnatario_tipologia == "utente":
                competenza_dipendente_found = True
            if assegnazione.tipologia == 'conoscenza' and assegnazione.assegnatario_tipologia == "ufficio":
                conoscenza_ufficio_found = True
            if assegnazione.tipologia == 'conoscenza' and assegnazione.assegnatario_tipologia == "utente":
                conoscenza_dipendente_found = True

        conditions_list = []

        if not self.env.user.has_group("sd_protocollo.group_sd_protocollo_registra_protocollo_senza_assegnazione"):
            if self.documento_id_content:
                conditions_list.extend(
                    [
                        (config["required_assegnatari_competenza_uffici"] and not config[
                            "required_assegnatari_competenza_dipendenti"] and not competenza_ufficio_found,
                         "ufficio_assegnatario_competenza"),

                        (config["required_assegnatari_competenza_dipendenti"] and not config[
                            "required_assegnatari_competenza_uffici"] and not competenza_dipendente_found,
                         "dipendente_assegnatario_competenza"),

                        (config["required_assegnatari_competenza_dipendenti"] and config[
                            "required_assegnatari_competenza_uffici"] and not competenza_ufficio_found and not competenza_dipendente_found,
                         "assegnatario_competenza"),

                        (config["required_assegnatari_conoscenza_uffici"] and not conoscenza_ufficio_found,
                         "uffici_assegnatario_conoscenza"),

                        (config["required_assegnatari_conoscenza_dipendenti"] and not conoscenza_dipendente_found,
                         "dipendente_assegnatario_conoscenza")
                    ]
                )
            else:
                conditions_list.extend(
                    [
                        (config["required_assegnatari_competenza_uffici_senza_doc"] and not config[
                            "required_assegnatari_competenza_dipendenti_senza_doc"] and not competenza_ufficio_found,
                         "ufficio_assegnatario_competenza"),

                        (config["required_assegnatari_competenza_dipendenti_senza_doc"] and not config[
                            "required_assegnatari_competenza_uffici_senza_doc"] and not competenza_dipendente_found,
                         "dipendente_assegnatario_competenza"),

                        (config["required_assegnatari_competenza_dipendenti_senza_doc"] and config[
                            "required_assegnatari_competenza_uffici_senza_doc"] and not competenza_ufficio_found and not competenza_dipendente_found,
                         "assegnatario_competenza"),

                        (config["required_assegnatari_conoscenza_uffici_senza_doc"] and not conoscenza_ufficio_found,
                         "uffici_assegnatario_conoscenza"),

                        (config[
                             "required_assegnatari_conoscenza_dipendenti_senza_doc"] and not conoscenza_dipendente_found,
                         "dipendente_assegnatario_conoscenza")
                    ]
                )

        for condition in conditions_list:
            if condition[0]:
                error = _(self.error_get(condition[1]))
                errors.append(error)

        if config["required_data_ricezione"] and self.tipologia_protocollo == "ingresso" and not self.data_ricezione:
            error = self.error_get("data_ricezione")
            errors.append(error)

        if not self.documento_id.document_type_id:
            error = self.error_get("documento_document_type")
            errors.append(error)

        allegati_document_type_list = []
        for allegato in self.allegato_ids:
            if not allegato.document_type_id:
                allegati_document_type_list.append(allegato.filename)
        if len(allegati_document_type_list) > 1:
            error = self.error_get("allegati_document_type") % ", ".join(allegati_document_type_list)
            errors.append(error)
        elif len(allegati_document_type_list) == 1:
            error = self.error_get("allegato_document_type") % allegati_document_type_list[0]
            errors.append(error)

        if errors:
            return errors

        return False

    def _get_html_campi_obbligatori(self):
        errors = self.verifica_campi_obbligatori()
        if not errors:
            return False
        error_message_start = '<div class="verifica-campi-container"><b><p>'
        error_message_start += _(
            "Valorizzare correttamente i seguenti campi per procedere alla registrazione:") + '</p></b><ul>'
        error_message_end = '</ul></div>'
        error_message = ''
        for error in errors:
            error_message += '<li>' + error + '</li>'
        return error_message_start + error_message + error_message_end

    def protocollo_elimina_bozza_action(self):
        self.ensure_one()
        if self.button_elimina_bozza_invisible:
            return
        protocol_documents = self.env["sd.dms.document"].search([("protocollo_id", "=", self.id)])
        for sd_document in protocol_documents:
            if sd_document.created_by_protocol:
                sd_document.sudo().unlink()
        self.sudo().unlink()
        return self.redirect_menu_protocolli()

    @api.model
    def redirect_menu_protocolli(self):
        action = self.env.ref("sd_protocollo.action_sd_protocollo_protocollo_list").read()[0]
        company_id = self.env.user.company_id.id
        menu_id = self.env.ref("sd_protocollo.menu_sd_protocollo").id
        return {
            "type": "ir.actions.act_url",
            "name": "Protocolli",
            "target": "self",
            "url": "/web#action=%s&model=sd.protocollo.protocollo&view_type=list&cids=%s&menu_id=%s" % (
                action["id"], company_id, menu_id
            )
        }

    def protocollo_lista_allegati_action(self):
        self.ensure_one()
        # il valore default protocollo_id deve essere settato solamente se nel protocollo è possibile aggiungere
        # allegati, in caso contrario non deve essere possibile creare un allegato quindi non settando il campo
        # protocollo_id, essendo readonly, non sarà possibile creare un allegato associato al protocollo. Come ulteriore
        # sicurezza il button create della tree view degli allegati viene nascosto con lo stesso criterio
        context = self._get_context_for_list_allegati()
        domain = [("protocollo_id", "=", self.id)]
        if self.documento_id:
            domain.append(("id", "!=", self.documento_id.id))
        return {
            "name": "Allegati",
            "view_mode": "tree,form",
            "res_model": "sd.dms.document",
            "type": "ir.actions.act_window",
            "domain": domain,
            "search_view_id": [
                self.env.ref("sd_protocollo.view_sd_dms_document_search_protocollo_allegato_list").id,
                "search"
            ],
            "context": context
        }

    def protocollo_form_documento_action(self):
        self.ensure_one()
        return {
            "name": "Documento",
            "type": "ir.actions.act_window",
            "res_model": "sd.dms.document",
            "view_mode": "form",
            "res_id": self.documento_id.id,

        }

    def _get_context_for_list_allegati(self):
        return dict(
            self.env.context,
            registration_type="protocol",
            default_folder_id=self.documento_id_cartella_id.id,
            default_document_type_id=self.documento_id_document_type_id.id,
            default_protocollo_id=self.id if not self.button_aggiungi_allegati_invisible else False,
            default_button_document_add_contact_sender_invisible=True,
            default_button_document_add_contact_recipient_invisible=True,
            create=not self.button_aggiungi_allegati_invisible
        )

    def protocollo_lista_source_action(self):
        self.ensure_one()
        # tale action deve essere estesa nei moduli che si occupano di implementare la parte di gestione di una sorgente
        # relativa al protocollo: mail in ingresso, documento importato ecc
        return

    def protocollo_elimina_mittente_interno_action(self):
        self.ensure_one()
        self.mittente_interno_id = False

    def protocollo_rispondi_action(self):
        self.ensure_one()
        context = dict(self.env.context)
        if self.tipologia_protocollo == "ingresso" and self.state == "registrato" and self.env.user.has_group(
                'sd_protocollo.group_sd_protocollo_crea_protocollo_uscita'):
            values = self.get_reply_values()
            bozza_protocollo = self.create(values)
            context["form_view_initial_mode"] = "edit"
            if self.mittente_ids:
                recipient = self.mittente_ids[0].copy()
            else:
                raise ValidationError(_("Unable to generate a reply with this sender!"))
            for domicilio in self.mittente_ids[0].digital_domicile_ids:
                domicilio_copy = domicilio.copy()
                domicilio_copy.contact_id = recipient.id
            recipient.typology = "recipient"
            bozza_protocollo.documento_id.write({"recipient_ids": [(6, 0, [recipient.id])]})
            return {
                "name": "Protocollo",
                "type": "ir.actions.act_window",
                "res_id": bozza_protocollo.id,
                "view_type": "form",
                "view_mode": "form,tree",
                "res_model": "sd.protocollo.protocollo",
                "target": "current",
                "context": context
            }
        else:
            list_errors = [_("Unable to create a response for the following reasons:")]
            e = 1
            message = "\n"
            if self.tipologia_protocollo == "uscita":
                list_errors.append(str(e) + _(". You cannot reply to an outbound protocol."))
                e += 1
            elif self.tipologia_protocollo == "interno":
                list_errors.append(str(e) + _(". You cannot reply to an internal protocol."))
                e += 1
            if not self.env.user.has_group('sd_protocollo.group_sd_protocollo_crea_protocollo_uscita'):
                list_errors.append(str(e) + _(
                    ". You are not authorized to create an outbound protocol, please contact your system administrator."))
                e += 1
            if self.state != "registrato":
                list_errors.append(str(e) + _(". Protocol must be registered."))
            raise ValidationError(message.join(list_errors))

    def get_reply_values(self):
        values_default = self.get_protocol_default_value()
        values = {
            "company_id": values_default["company_id"],
            "protocollatore_id": self.env.user.id,
            "protocollatore_name": self.env.user.name,
            "protocollatore_ufficio_id": values_default["protocollatore_ufficio"].id,
            "registro_id": values_default["registro_id"],
            "archivio_id": values_default["archivio_id"],
            "mezzo_trasmissione_id": self.mezzo_trasmissione_id.id,
            "tipologia_protocollo": "uscita",
            "documento_id_cartella_id": values_default["folder"].id,
            "documento_id_filename": "Nuovo Documento",
            "is_reply": True
        }
        return values

    def get_full_url(self):
        self.ensure_one()
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        url_params = {
            'id': self.id,
            'view_type': 'form',
            'model': 'protocollo.protocollo',
            'menu_id': self.env.ref('sd_protocollo.menu_sd_protocollo').id,
            'action': self.env.ref('sd_protocollo.action_sd_protocollo_protocollo_list').id,
        }

        params = '/web?#%s' % werkzeug.url_encode(url_params)
        return base_url + params
