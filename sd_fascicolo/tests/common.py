from odoo.addons.sd_dms.tests.common import DmsTestCommon
from odoo.addons.sd_dms_titolario.tests.common import DmsTestTitolarioCommon
from odoo.tests import tagged


@tagged('-standard', 'sd_dms')
class DmsTestFascicoloCommon(DmsTestTitolarioCommon):

    @classmethod
    def setUpClass(cls):
        super(DmsTestFascicoloCommon, cls).setUpClass()
        cls.fascicolo_obj = cls.env["sd.fascicolo.fascicolo"]
        cls.fascicolo_acl_obj = cls.env["sd.fascicolo.fascicolo.acl"]

        fascicolo_user_group = cls.env.ref("sd_fascicolo.group_sd_fascicolo_user")
        fascicolo_user_group.users = [(4, x) for x in cls.users]
