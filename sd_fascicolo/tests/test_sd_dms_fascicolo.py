from datetime import datetime

from odoo.addons.sd_fascicolo.tests.common import DmsTestFascicoloCommon
from odoo.exceptions import UserError
from odoo.tests import tagged, Form


@tagged('-standard', 'sd_dms')
class DmsTestFascicolo(DmsTestFascicoloCommon):

    @classmethod
    def setUpClass(cls):
        super(DmsTestFascicolo, cls).setUpClass()
        cls.config_param = cls.env["ir.config_parameter"].sudo()
        cls.fascicolo = cls.fascicolo_obj.create({
            "nome": "test",
            "oggetto": "test",
            "tipologia": "fascicolo",
            "categoria": "affare",
            "voce_titolario_id": cls.voce_titolario_id.id
        })

    def test_fascicolo_acl(self):
        # Creazione senza ACL di un sottofascicolo all'interno di un fascicolo
        vals = {
            "nome": "TestFascicolo2",
            "oggetto": "test",
            "tipologia": "sottofascicolo",
            "categoria": "affare",
            "parent_id": self.fascicolo.id,
            "voce_titolario_id": self.fascicolo.voce_titolario_id.id
        }
        self._raise_assert_create(self.user2, vals, self.fascicolo_obj)
        # Creazione con ACL di un sottofascicolo all'interno di un fascicolo
        fascicolo = self._pass_assert_create(self.user2, vals, self.fascicolo_obj, self.fascicolo,
                                             self.fascicolo_acl_obj)

        # Lettura senza ACL sul fascicolo
        self._raise_assert_read(self.user1, self.fascicolo_obj, fascicolo.id)
        # Lettura con ACL sul fascicolo
        self._pass_assert_read(self.user1, fascicolo, self.fascicolo_obj, self.fascicolo_acl_obj)

        # Scrittura senza ACL sul fascicolo
        data = {"oggetto": "acl"}
        self._raise_assert_update(self.user1, data, fascicolo)
        # Scrittura con ACL sul fascicolo
        self._pass_assert_update(self.user1, data, fascicolo, self.fascicolo_acl_obj)

        # Eliminazione del fascicolo senza ACL
        self._raise_assert_delete(self.user1, self.fascicolo)
        # Eliminazione con ACL
        self._pass_assert_delete(self.user1, self.fascicolo, self.fascicolo_obj, self.fascicolo_acl_obj)

    def test_correct_name(self):
        # Creazione Fascicolo - Sottofascicolo - Inserto con nomenclatura "classificazine"
        self._nomenclatura_classificazione()

    def _nomenclatura_classificazione(self):
        # Test lato form Form()
        fascicolo_form = Form(self.env["sd.fascicolo.fascicolo"])
        sottofascicolo_form = Form(self.env["sd.fascicolo.fascicolo"])
        inserto_form = Form(self.env["sd.fascicolo.fascicolo"])

        self.config_param.set_param("sd_fascicolo.nomenclatura_fascicolo", "classificazione")
        self.assertEqual(self.config_param.get_param("sd_fascicolo.nomenclatura_fascicolo"), "classificazione")

        # Test compute nome Fascicolo
        with fascicolo_form as f:
            f.oggetto = "prova nome fascicolo"
            f.tipologia = "fascicolo"
            f.categoria = "affare"
            f.voce_titolario_id = self.voce_titolario_id
        self.assertEqual(fascicolo_form.nome, "1.2 - VoceTitolario0 / prova nome fascicolo")

        # Test compute nome Sottofascicolo
        with sottofascicolo_form as f:
            f.oggetto = "prova nome sottofascicolo"
            f.tipologia = "sottofascicolo"
            f.categoria = "affare"
            f.parent_id = self.fascicolo_obj.browse(fascicolo_form.id)
        self.assertEqual(sottofascicolo_form.nome, "1.2.1 - VoceTitolario0 / prova nome fascicolo / prova nome sottofascicolo")

        # Test compute nome Inserto
        with inserto_form as f:
            f.oggetto = "prova nome inserto"
            f.tipologia = "inserto"
            f.categoria = "affare"
            f.parent_id = self.fascicolo_obj.browse(sottofascicolo_form.id)
        self.assertEqual(inserto_form.nome, "1.2.1.1 - VoceTitolario0 / prova nome fascicolo / prova nome sottofascicolo / prova nome inserto")

        # Test modifica oggetto
        with inserto_form as f:
            f.oggetto = "new subject"
        self.assertEqual(inserto_form.nome, "1.2.1.1 - VoceTitolario0 / prova nome fascicolo / prova nome sottofascicolo / new subject")

        # Salvataggio dei vari form indispensabile per popolare il campo child_ids del fascicolo padre.
        fascicolo_form.save()
        sottofascicolo_form.save()
        inserto_form.save()

        # Test modifica voce titolare sul fascicolo padre, che si ripercuoterà in automatico su tutti i child
        new_voce_titolario = self.voce_titolario_obj.create({
            "name": "VoceTitolario1",
            "titolario_id": self.titolario1_id.id,
            "class_type": "titolo",
            "code": 1.1
        })
        with fascicolo_form as f:
            f.voce_titolario_id = new_voce_titolario
        fascicolo_form.save()
        self.assertEqual(self.fascicolo_obj.browse(fascicolo_form.id).nome, "1.1.1 - VoceTitolario1 / prova nome fascicolo")
        self.assertEqual(self.fascicolo_obj.browse(sottofascicolo_form.id).nome, "1.1.1.1 - VoceTitolario1 / prova nome fascicolo / prova nome sottofascicolo")
        self.assertEqual(self.fascicolo_obj.browse(inserto_form.id).nome, "1.1.1.1.1 - VoceTitolario1 / prova nome fascicolo / prova nome sottofascicolo / new subject")

        # Test modifica parent di un inserto
        sottofascicolo2_form = Form(self.env["sd.fascicolo.fascicolo"])
        with sottofascicolo2_form as f:
            f.oggetto = "sottofascicolo2"
            f.tipologia = "sottofascicolo"
            f.categoria = "affare"
            f.parent_id = self.fascicolo_obj.browse(fascicolo_form.id)
        with inserto_form as f:
            f.parent_id = self.fascicolo_obj.browse(sottofascicolo2_form.id)
        self.assertEqual(inserto_form.nome, "1.1.1.2.1 - VoceTitolario1 / prova nome fascicolo / sottofascicolo2 / new subject")

        # Test nomenclatura tramite create(vals), si dovrà inserire un nome fittizio in quanto il nome è required per
        # avere il controllo lato db. Il nome verrà comunque sovrascritto dalla funzione addetta al ricalcolo
        fascicolo = self.fascicolo_obj.create({
            "nome": "nome fittizio",
            "oggetto": "test",
            "tipologia": "fascicolo",
            "categoria": "affare",
            "voce_titolario_id": self.voce_titolario_id.id
        })
        self.assertEqual(fascicolo.nome, "1.2 - VoceTitolario0 / test")

    def test_apertura_fascicolo(self):
        self.fascicolo.apri_fascicolo()
        self.assertEqual(self.fascicolo.state, "aperto")
        self.assertIsInstance(self.fascicolo.data_apertura, datetime)
        self.assertTrue(self.fascicolo.anno)

    def test_chiusura_fascicolo(self):
        self.fascicolo.chiudi_fascicolo()
        self.assertEqual(self.fascicolo.state, "chiuso")
        self.assertIsInstance(self.fascicolo.data_chiusura, datetime)

    def test_fascicolo_aggiunta_rimozione_document(self):
        document_data = self.document_data.copy()
        document_data.update({
            "voce_titolario_id": self.voce_titolario_id.id
        })
        document = self.document_obj.create(document_data)
        document2 = self.document_obj.create(document_data)
        document3 = self.document_obj.create(document_data)

        with self.assertRaises(UserError):
            self.fascicolo.fascicolo_aggiungi_documenti([document.id, document2.id, document3.id])

        # Aggiunta documenti al Fascicolo
        self.fascicolo.apri_fascicolo()
        self.fascicolo.fascicolo_aggiungi_documenti([document.id, document2.id, document3.id])
        self.assertEqual(self.fascicolo.documento_ids_count, 3)

        # Rimozione di un documento dal Fascicolo
        self.fascicolo.fascicolo_disassocia_documenti([document.id])
        self.assertEqual(self.fascicolo.documento_ids_count, 2)
