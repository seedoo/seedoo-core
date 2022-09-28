from contextlib import contextmanager
from unittest.mock import patch

from odoo import _
from odoo.addons.sd_protocollo.tests.common import ProtocolloTestCommon
from odoo.exceptions import UserError
from odoo.fields import Datetime
from odoo.tests import tagged, Form, users
import json


@tagged('-standard', 'sd_protocollo')
class ProtocolloTestProtocollo(ProtocolloTestCommon):

    @classmethod
    def setUpClass(cls):
        super(ProtocolloTestProtocollo, cls).setUpClass()

        mezzo_trasmissione = cls.env.ref("sd_protocollo.data_sd_protocollo_mezzo_trasmissione_corriere")
        cartella_documento = cls.env.ref("sd_protocollo.data_sd_dms_folder_protocolli")
        document_type = cls.env.ref("sd_dms.data_sd_dms_document_type_electronic_amministrative")

        cls.protocollo_data_uscita = {
            "user_tipologia_protocollo": "uscita",
            "mezzo_trasmissione_id": mezzo_trasmissione,
            "documento_id_content": cls.document_content_data,
            "documento_id_oggetto": "test uscita",
            "documento_id_cartella_id": cartella_documento,
            "documento_id_document_type_id": document_type
        }

        cls.protocollo_data_ingresso = {
            "user_tipologia_protocollo": "ingresso",
            "mezzo_trasmissione_id": mezzo_trasmissione,
            "documento_id_content": cls.document_content_data,
            "documento_id_oggetto": "test ingresso",
            "documento_id_cartella_id": cartella_documento,
            "documento_id_document_type_id": document_type,
            "data_ricezione": Datetime.now()
        }

        cls.com_user1 = cls.res_users_obj.create({
            "name": "ProtocolloUser1",
            "login": "ProtocolloUser1",
            "email": "puser1@example.com"
        })
        cls.con_user2 = cls.res_users_obj.create({
            "name": "ProtocolloUser2",
            "login": "ProtocolloUser2",
            "email": "puser2@example.com"
        })
        cls.con_user3 = cls.res_users_obj.create({
            "name": "ProtocolloUser3",
            "login": "ProtocolloUser3",
            "email": "puser3@example.com"
        })
        cls.con_user4 = cls.res_users_obj.create({
            "name": "ProtocolloUser4",
            "login": "ProtocolloUser4",
            "email": "puser4@example.com"
        })

        cls.set_1 = cls.fl_set_obj.create({
            "name": "ProvaSet1",
            "set_type": "standard",
            "user_ids": [(6, 0, [cls.com_user1.id, cls.con_user2.id])]
        })
        cls.set_2 = cls.fl_set_obj.create({
            "name": "ProvaSet1",
            "set_type": "standard",
            "user_ids": [(6, 0, [cls.con_user3.id, cls.con_user4.id])]
        })
        assegnatario_user_group = cls.env.ref("sd_protocollo.group_sd_protocollo_assegnatario")
        set_user_group = cls.env.ref("fl_set.group_fl_set_user")
        dms_user_group = cls.env.ref("sd_dms.group_sd_dms_user")
        user_list = [(4, cls.com_user1.id), (4, cls.con_user2.id), (4, cls.con_user3.id), (4, cls.con_user4.id)]
        assegnatario_user_group.users = user_list
        set_user_group.users = user_list
        dms_user_group.users = user_list

    @classmethod
    def get_contact_data(self, type):
        return {
            'typology': type,
            'name': 'Test',
            'email': 'test@example.com',
            'company_type': 'person',
            'digital_domicile_ids': [],
            'save_partner': False
        }

    @users("admin")
    def test_protocollo_errori_registrazione_uscita(self):
        protocollo_form = Form(self.env["sd.protocollo.protocollo"])

        # Compilazione dei campi required in vista (tipologia, mezzo_trasmissione, cartella)
        protocollo_form.user_tipologia_protocollo = self.protocollo_data_uscita["user_tipologia_protocollo"]
        protocollo_form.mezzo_trasmissione_id = self.protocollo_data_uscita["mezzo_trasmissione_id"]
        protocollo_form.documento_id_cartella_id = self.protocollo_data_uscita["documento_id_cartella_id"]
        protocollo_form.save()

        # Richiamo della funzione protocollo_registra_action, che restituirà una lista di campi necessari per la
        # registrazione del protocollo in uscita
        protocollo = self.protocollo_obj.browse(protocollo_form.id)
        with self.mock_protocollo_registrazione():
            errors = protocollo.protocollo_registra_action()
        self._check_uscita_registration_errors(errors, "assertTrue")

        # Inserimento della tipologia in quanto lato form non sembra che applichi il default dopo il salvataggio
        protocollo_form.user_tipologia_protocollo = protocollo_form.tipologia_protocollo

        # Compilazione dei campi rimanenti per effettuare la registrazione
        protocollo_form.documento_id_content = self.protocollo_data_uscita["documento_id_content"]
        protocollo_form.documento_id_oggetto = self.protocollo_data_uscita["documento_id_oggetto"]
        protocollo_form.documento_id_document_type_id = self.protocollo_data_uscita["documento_id_document_type_id"]
        protocollo_form.save()

        # Aggiunta del mittente interno "Amministrazione"
        protocollo.salva_mittente_interno(
            self.voce_organingramma_obj.search([])[0]
        )

        # Aggiunta di un destinatario
        protocollo_form.documento_id.document_save_contact(
            protocollo_form.documento_id.id,
            False,
            self.get_contact_data("recipient")
        )

        # Verifica che non siano più presenti campi mancati per effettuare la registrazione in uscita
        with self.mock_protocollo_registrazione():
            errors = protocollo.protocollo_registra_action() or []
        self._check_uscita_registration_errors(errors, "assertFalse")

    def _check_uscita_registration_errors(self, errors, assert_type):
        # Si occupa di verificare l'assert passato (assert_type) in base alla lista passata (errors)
        # equivalente di self.assertFalse o self.assertTrue in base al tipo di assert passato
        assert_function = getattr(self, assert_type)

        assert_function(_("Documento") in errors)
        assert_function(_("Oggetto") in errors)
        assert_function(_("Mittente") in errors)
        assert_function(_("Destinatari") in errors)
        assert_function(_("The main document doesn't have a document type associated") in errors)

    @users("admin")
    def test_protocollo_errori_registrazione_ingresso(self):
        protocollo_form = Form(self.env["sd.protocollo.protocollo"])

        # Compilazione dei campi required in vista (tipologia, mezzo_trasmissione, cartella)
        protocollo_form.user_tipologia_protocollo = self.protocollo_data_ingresso["user_tipologia_protocollo"]
        protocollo_form.mezzo_trasmissione_id = self.protocollo_data_ingresso["mezzo_trasmissione_id"]
        protocollo_form.documento_id_cartella_id = self.protocollo_data_ingresso["documento_id_cartella_id"]
        protocollo_form.save()

        # Richiamo della funzione protocollo_registra_action, che restituirà una lista di campi necessari per la
        # registrazione del protocollo in ingresso
        protocollo = self.protocollo_obj.browse(protocollo_form.id)
        with self.mock_protocollo_registrazione():
            errors = protocollo.protocollo_registra_action()
        self._check_ingresso_registration_errors(errors, "assertTrue")

        # Inserimento della tipologia in quanto lato form non sembra che applichi il default dopo il salvataggio
        protocollo_form.user_tipologia_protocollo = protocollo_form.tipologia_protocollo

        # Compilazione dei campi rimanenti per effettuare la registrazione
        protocollo_form.documento_id_content = self.protocollo_data_ingresso["documento_id_content"]
        protocollo_form.documento_id_oggetto = self.protocollo_data_ingresso["documento_id_oggetto"]
        protocollo_form.documento_id_document_type_id = self.protocollo_data_ingresso["documento_id_document_type_id"]
        protocollo_form.data_ricezione = self.protocollo_data_ingresso["data_ricezione"]
        protocollo_form.save()

        # Aggiunta di un destinatario
        protocollo_form.documento_id.document_save_contact(
            protocollo_form.documento_id.id,
            False,
            self.get_contact_data("sender")
        )

        # Verifica che non siano più presenti campi mancati per effettuare la registrazione in uscita
        with self.mock_protocollo_registrazione():
            errors = protocollo.protocollo_registra_action() or []
        self._check_ingresso_registration_errors(errors, "assertFalse")

    def _check_ingresso_registration_errors(self, errors, assert_type):
        # equivalente di self.assertFalse o self.assertTrue in base al tipo di assert passato
        assert_function = getattr(self, assert_type)

        assert_function(_("Documento") in errors)
        assert_function(_("Oggetto") in errors)
        assert_function(_("Mittente") in errors)
        assert_function(_("Data Ricezione") in errors)
        assert_function(_("The main document doesn't have a document type associated") in errors)

    def _get_draft_protocollo_uscita(self):
        # Compilazione del form in uscita, verrà creato con l'utente dell'env
        protocollo_form = Form(self.env["sd.protocollo.protocollo"])
        with protocollo_form as form:
            form.user_tipologia_protocollo = self.protocollo_data_uscita["user_tipologia_protocollo"]
            form.mezzo_trasmissione_id = self.protocollo_data_uscita["mezzo_trasmissione_id"]
            form.documento_id_cartella_id = self.protocollo_data_uscita["documento_id_cartella_id"]
            form.documento_id_content = self.protocollo_data_uscita["documento_id_content"]
            form.documento_id_oggetto = self.protocollo_data_uscita["documento_id_oggetto"]
            form.documento_id_document_type_id = self.protocollo_data_uscita["documento_id_document_type_id"]
        protocollo = self.protocollo_obj.browse(protocollo_form.id)
        # Aggiunta del mittente interno "Amministrazione"
        protocollo.salva_mittente_interno(
            self.voce_organingramma_obj.search([])[0]
        )
        # Aggiunta di un destinatario
        protocollo_form.documento_id.document_save_contact(
            protocollo_form.documento_id.id,
            False,
            self.get_contact_data("recipient")
        )
        return protocollo

    def _get_protocollo_uscita_registrato(self):
        protocollo = self._get_draft_protocollo_uscita()
        with self.mock_protocollo_registrazione():
            with self.mock_commit_request():
                protocollo.registra()
        return protocollo

    def test_flow0_protocollo_assegnazione(self):
        """
            Test flow aggiunta assegnazioni e presa in carico/lettura
            Administrator -> Protocollatore
            ProtocolloUser1 -> Assegnatario per Competenza
            ProtocolloUser2 -> Assegnatario per Conoscenza
            ProtocolloUser3 -> Assegnatazio per Conoscenza da Ufficio (set_2)
            ProtocolloUser4 -> Assegnatazio per Conoscenza da Ufficio (set_2)
        """
        assegnatore_id = self.res_users_obj.browse(2).id
        assegnatore_ufficio_id = self.fl_set_obj.browse(1).id

        with self.with_user("admin"):
            protocollo = self._get_protocollo_uscita_registrato()

        self.assertEqual(protocollo.state, "registrato")

        # Aggiunta assegnazione per competenza
        organigramma_com_user1_id = self.voce_organingramma_obj.search([("utente_id", "=", self.com_user1.id)],
                                                                       limit=1).id
        protocollo.salva_assegnazione_competenza(
            [organigramma_com_user1_id],
            assegnatore_id,
            assegnatore_ufficio_id
        )

        # Aggiunta assegnatari per conoscenza (con_user2, set_2)
        organigramma_con_user2_id = self.voce_organingramma_obj.search([("utente_id", "=", self.con_user2.id)],
                                                                       limit=1).id
        organigramma_con_set_2_id = self.voce_organingramma_obj.search([("ufficio_id", "=", self.set_2.id)], limit=1).id
        protocollo.salva_assegnazione_conoscenza(
            [organigramma_con_user2_id, organigramma_con_set_2_id],
            assegnatore_id,
            assegnatore_ufficio_id
        )

        # Verifica aggiunta e stato delle assegnazioni
        self.assertTrue(len(protocollo.assegnazione_ids) == 3)
        self.assertEqual(protocollo.assegnazione_competenza_ids[0].state, "assegnato")
        self.assertEqual(protocollo.assegnazione_conoscenza_ids[0].state, "assegnato")
        self.assertEqual(protocollo.assegnazione_conoscenza_ids[1].state, "assegnato")

        # Presa in carico del protocollo da parte dell'assegnatario per competenza (con_user1)
        protocollo.with_user(self.com_user1.id).prendi_in_carico_assegnazione(protocollo.assegnazione_competenza_ids[0].id, self.env.uid)
        self.assertEqual(protocollo.assegnazione_competenza_ids[0].state, "preso_in_carico")

        # Lettura assegnazione da parte di ogni membro dell'ufficio al quale è stato assegnato (set_2)
        protocollo.with_user(self.con_user3.id).protocollo_leggi_assegnazione_action()
        self.assertEqual(protocollo.assegnazione_conoscenza_ids[1].state, "assegnato")
        protocollo.with_user(self.con_user4.id).protocollo_leggi_assegnazione_action()
        self.assertEqual(protocollo.assegnazione_conoscenza_ids[1].state, "letto_cc")

        # Lettura assegnazione da parte dell'assegnazione a utente per conoscenza (con_user2)
        protocollo.with_user(self.con_user2.id).protocollo_leggi_assegnazione_action()
        self.assertEqual(protocollo.assegnazione_conoscenza_ids[0].state, "letto_cc")

    def test_flow1_protocollo_assegnazione(self):
        """
            Test flow aggiunta assegnazione per competenza con rifiuto presa in carico e successiva riassegnazione di
            un set come assegnazione per Competenza con successiva presa in carico di uno user di quel set.

            Administrator -> Protocollatore
            ProtocolloUser1 -> Assegnatario per Competenza -> Rifiuta Assegnazione
            Set2 -> Assegnatario per Competenza
            ProtocolloUser3 -> Prende assegnazione per Competenza
            ProtocolloUser3 -> Completa lavorazione
        """
        assegnatore_id = self.res_users_obj.browse(2).id
        assegnatore_ufficio_id = self.fl_set_obj.browse(1).id

        with self.with_user("admin"):
            protocollo = self._get_protocollo_uscita_registrato()

        # Aggiunta assegnazione per competenza
        organigramma_com_user1_id = self.voce_organingramma_obj.search([("utente_id", "=", self.com_user1.id)],
                                                                       limit=1).id
        protocollo.salva_assegnazione_competenza(
            [organigramma_com_user1_id],
            assegnatore_id,
            assegnatore_ufficio_id
        )
        # Verifica dell'avvenuta creazione dell'assegnazione per competenteza
        self.assertEqual(protocollo.assegnazione_competenza_ids[0].state, "assegnato")

        # Rifiuto dell'assegnazione per competenza
        with self.mock_commit_request():
            protocollo.with_user(self.com_user1.id).rifiuta_assegnazione(protocollo.assegnazione_competenza_ids[0].id, self.com_user1.id, "")
        self.assertEqual(protocollo.assegnazione_competenza_ids[0].state, "rifiutato")

        # Riassegnazione di un'assegnazione per competenza (Ufficio)
        organigramma_con_set_2_id = self.voce_organingramma_obj.search([("ufficio_id", "=", self.set_2.id)], limit=1).id
        protocollo.salva_assegnazione_competenza(
            [organigramma_con_set_2_id],
            assegnatore_id,
            assegnatore_ufficio_id
        )
        self.assertEqual(protocollo.assegnazione_competenza_ids[0].state, "assegnato")

        protocollo.with_user(self.con_user3.id).prendi_in_carico_assegnazione(protocollo.assegnazione_competenza_ids[0].id, self.con_user3.id)
        self.assertEqual(protocollo.assegnazione_competenza_ids[0].state, "preso_in_carico")
        protocollo.with_user(self.con_user3.id).completa_lavorazione_assegnazione(protocollo.assegnazione_competenza_ids[0].id, self.con_user3.id, "")
        self.assertEqual(protocollo.assegnazione_competenza_ids[0].state, "lavorazione_completata")

    # def test_aggiunta_rimozione_acl_in_assegnazione_flow(self):
    #     """
    #         Verifica il corretto aggiornamento delle acl a seconda dell'aggiunta/rimozione delle assegnazioni
    #         ProtocolloUser1 -> Assegnatario per Competenza
    #         ProtocolloUser2 -> Assegnatario per Conoscenza
    #     """
    #     assegnatore_id = self.res_users_obj.browse(2).id
    #     assegnatore_ufficio_id = self.fl_set_obj.browse(1).id
    #
    #     with self.with_user("admin"):
    #         protocollo = self._get_protocollo_uscita_registrato()
    #
    #     # Numero delle ACL presenti dal protocollo, date dal protocollotaore + utenti con visibilità sui protocolli
    #     old_acl_list = self.document_acl_obj.search([("protocollo_id", "=", protocollo.id)]).ids
    #
    #     #Aggiunta assegnatario per competenza
    #     organigramma_com_user1_id = self.voce_organingramma_obj.search(
    #         [("utente_id", "=", self.com_user1.id)], limit=1).id
    #     protocollo.salva_assegnazione_competenza(
    #         [organigramma_com_user1_id],
    #         assegnatore_id,
    #         assegnatore_ufficio_id
    #     )
    #     new_acl_list = self.document_acl_obj.search([("protocollo_id", "=", protocollo.id)]).ids
    #     # Verifica che alle acl del protocollo sia stata aggiunta l'acl dell'assegnatario aggiunto
    #     new_acl = set(old_acl_list).symmetric_difference(set(new_acl_list))
    #
    #     self.assertTrue(len(protocollo.acl_ids.ids) == len(old_acl_list) + 1)

    @users("admin")
    def test_protocollo_registra_action(self):
        # Recupero di un protocollo compilato
        protocollo = self._get_draft_protocollo_uscita()

        # Controllo campi mancanti per la registrazione
        with self.mock_protocollo_registrazione():
            errors = protocollo.protocollo_registra_action()
        self.assertFalse(errors)

        # Controllo delle ricevute
        num_notifiche = self.bus_obj.search_count([])
        protocol_number = str(protocollo.registro_id.sequence_id.number_next_actual).zfill(7)

        # Registrazione del protocollo
        with self.mock_protocollo_registrazione():
            with self.mock_commit_request():
                errore_registrazione = protocollo.registra()

        self.assertFalse(errore_registrazione)
        # Verifica che sia presente una notifica in più e che questa contenga la tipologia "success", che viene inviata
        # quando in fase di registrazione non avvengono errori
        self.assertTrue(num_notifiche == self.bus_obj.search_count([]) - 1)
        ultima_notifica = self.bus_obj.search([], order="id desc", limit=1)
        ultima_notifica_dict = json.loads(ultima_notifica.message)
        self.assertTrue(ultima_notifica_dict["type"] == "success")
        self.assertTrue(protocollo.numero_protocollo == protocol_number)

    @users("admin")
    def test_protocollo_sequence(self):
        registro = self.env["sd.protocollo.registro"].search([("can_used_to_protocol", "=", True)])
        # recupera il prossimo numero che sarà utilizzato dalla sequence
        number = registro.sequence_id.number_next_actual
        # creo 5 protocolli
        for i in range(5):
            protocollo = self._get_draft_protocollo_uscita()
            protocol_number = str(protocollo.registro_id.sequence_id.number_next_actual).zfill(7)
            with self.mock_protocollo_registrazione():
                with self.mock_commit_request():
                    protocollo.registra()
            # verificio che il protocollo sia stato registato con il number next della sequence precedentemente salvato
            self.assertTrue(protocol_number == protocollo.numero_protocollo)
        self.assertTrue(registro.sequence_id.number_next_actual == number + 4)
        next_number = registro.sequence_id._next()
        self.assertTrue(str(number + 5).zfill(7) == next_number)
