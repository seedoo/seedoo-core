from odoo.addons.sd_dms_titolario.tests.common import DmsTestTitolarioCommon
from odoo.exceptions import UserError
from odoo.tests import tagged, Form


@tagged('-standard', 'sd_dms')
class DmsTestDocumento(DmsTestTitolarioCommon):

    def test_company_voce_titolario_id_document(self):
        temp_document = self.document_obj.create(self.document_data)
        self.titolario1_id.company_id = self.other_company.id
        self.titolario1_id.state = True

        #Controllo della company della voce di titolario
        with self.assertRaises(UserError):
            # Verrà triggherato l'onchange lato vista
            with Form(temp_document) as f:
                f.voce_titolario_id = self.voce_titolario_id
