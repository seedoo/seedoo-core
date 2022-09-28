from odoo.addons.sd_dms.tests.common import DmsTestCommon
from odoo.tests import tagged


@tagged('-standard', 'sd_dms')
class DmsTestTitolarioCommon(DmsTestCommon):

    @classmethod
    def setUpClass(cls):
        super(DmsTestTitolarioCommon, cls).setUpClass()
        cls.titolario_obj = cls.env["sd.dms.titolario.titolario"]
        cls.voce_titolario_obj = cls.env["sd.dms.titolario.voce.titolario"]

        cls.titolario0_id = cls.titolario_obj.search([("company_id", "=", cls.admin.company_id.id)])
        if not cls.titolario0_id:
            cls.titolario0_id = cls.titolario_obj.create({
                "name": "Titolario0",
                "state": True
            })

        cls.titolario1_id = cls.titolario_obj.create({
            "name": "Titolario1",
            "state": False
        })

        cls.voce_titolario_id = cls.voce_titolario_obj.create({
            "name": "VoceTitolario0",
            "titolario_id": cls.titolario1_id.id,
            "class_type": "titolo",
            "code": 1
        })
