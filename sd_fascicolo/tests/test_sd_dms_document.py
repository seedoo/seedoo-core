from odoo.addons.sd_fascicolo.tests.common import DmsTestFascicoloCommon
from odoo.tests import tagged


@tagged('-standard', 'sd_dms')
class DmsTestDocument(DmsTestFascicoloCommon):

    @classmethod
    def setUpClass(cls):
        super(DmsTestDocument, cls).setUpClass()
        cls.fascicolo = cls.fascicolo_obj.create({
            "nome": "test",
            "oggetto": "test",
            "tipologia": "fascicolo",
            "categoria": "affare",
            "voce_titolario_id": cls.voce_titolario_id.id
        })

        cls.fascicolo2 = cls.fascicolo_obj.create({
            "nome": "test",
            "oggetto": "test",
            "tipologia": "fascicolo",
            "categoria": "affare",
            "voce_titolario_id": cls.voce_titolario_id.id
        })

    def test_aggiunta_rimozione_fascicolo(self):
        documento = self.document_obj.create(self.document_data)

        # Aggiunta fascicoli da documento
        documento.documento_aggiungi_fascicoli([self.fascicolo.id, self.fascicolo2.id])
        self.assertEqual(len(documento.fascicolo_ids.ids), 2)

        # Rimozione fascicolo tramite context
        documento.with_context({"disassocia_documento_fascicolo_id": self.fascicolo.id}).disassocia_documento()
        self.assertEqual(len(documento.fascicolo_ids.ids), 1)

        # Rimozione fascicoli da documento
        documento.documento_disassocia_fascicoli([self.fascicolo2.id])
        self.assertEqual(len(documento.fascicolo_ids.ids), 0)
