from odoo.addons.sd_dms_titolario.tests.common import DmsTestTitolarioCommon
from odoo.exceptions import UserError
from odoo.tests import tagged


@tagged('-standard', 'sd_dms')
class DmsTestTitolario(DmsTestTitolarioCommon):

    def test_uniqueness_titolario_for_company(self):
        # Test possibilità di aggiungere un unico titolario attivo per company
        with self.assertRaises(UserError):
            self.titolario1_id.state = True

        self.titolario1_id.company_id = self.other_company.id
        self.titolario1_id.state = True






