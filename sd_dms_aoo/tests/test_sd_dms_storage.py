from odoo.addons.sd_dms.tests.common import DmsTestCommon
from odoo.exceptions import UserError
from odoo.tests import tagged


@tagged('-standard', 'sd_dms')
class DmsTestStorage(DmsTestCommon):

    @classmethod
    def setUpClass(cls):
        super(DmsTestStorage, cls).setUpClass()
        cls.set_obj = cls.env["fl.set.set"]
        cls.aoo_id = cls.set_obj.create({
            "name": "TempAOO",
            "set_type": "aoo",
            "cod_aoo": "temp-aoo",
        })

    def test_company_aoo_id(self):
        self.root_storage.aoo_id = self.aoo_id.id
        with self.assertRaises(UserError):
            self.root_storage.company_id = self.other_company.id
