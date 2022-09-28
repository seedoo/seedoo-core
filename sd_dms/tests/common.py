import base64

from odoo import SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.modules import get_module_resource
from odoo.tests.common import SavepointCase
from odoo.tests import tagged
from odoo.tools import mute_logger


@tagged('-standard', 'sd_dms')
class DmsTestCommon(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super(DmsTestCommon, cls).setUpClass()

        cls.company_obj = cls.env["res.company"]
        cls.category_obj = cls.env["sd.dms.category"]
        cls.user_obj = cls.env["res.users"]
        cls.storage_obj = cls.env["sd.dms.storage"]
        cls.document_obj = cls.env["sd.dms.document"]
        cls.folder_obj = cls.env["sd.dms.folder"]
        cls.document_acl_obj = cls.env["sd.dms.document.acl"]
        cls.folder_acl_obj = cls.env["sd.dms.folder.acl"]
        cls.contact_obj = cls.env["sd.dms.contact"]
        dms_user_group = cls.env.ref("sd_dms.group_sd_dms_user")

        cls.admin = cls.user_obj.browse(SUPERUSER_ID)

        cls.other_company = cls.company_obj.create(
            {'name': 'Company B'}
        )

        cls.users = []
        # Creazione utenti e aggiunta role "dms_user" con i quali eseguire i test (user0, user1, user2)
        for i in range(3):
            setattr(cls, "user%d" % i, cls.user_obj.create({
                "name": "dmstestuser%d" % i,
                "login": "dmstestuser%d" % i,
                "email": "dmstestuser%d@example.com" % i
            }))
            cls.users.append(getattr(cls, "user%d" % i).id)
        dms_user_group.users = [(4, x) for x in cls.users]

        cls.root_storage = cls.env.ref("sd_dms.data_sd_dms_storage_filestore")
        cls.root_storage_id = cls.env.ref("sd_dms.data_sd_dms_storage_filestore").id
        cls.root_folder_id = cls.env.ref("sd_dms.data_sd_dms_folder_root").id
        cls.subfolder = cls.folder_obj.create({
            "name": "Subfolder",
            "is_root_folder": False,
            "parent_folder_id": cls.root_folder_id,
            "inherit_acl": False
        })
        cls.subfolder_id = cls.subfolder.id

        image_path = get_module_resource("sd_dms", "static/description", "icon.png")
        with open(image_path, "rb") as image:
            cls.document_content_data = base64.b64encode(image.read())

        cls.document_data = {
            "filename": "test_dms.png",
            "content": cls.document_content_data,
            "subject": "prova",
            "folder_id": cls.subfolder_id,
            "inherit_acl": True,
        }

    @classmethod
    def _get_user_acl(self, obj, user, create=False, read=False, write=False, delete=False):
        return obj.create({
            "module_id": self.env.ref("base.module_sd_dms").id,
            "res_model": "res_users",
            "res_id": user.id,
            "res_name": user.name,
            "perm_create": create,
            "perm_read": read,
            "perm_write": write,
            "perm_delete": delete,
            "create_system": True
        })

    def _get_crud_acl(self, crud_type, user, model_acl, model_instance=False, parent_model_instance=False):
        if not (model_acl != False):
            return
        crud_perm = {
            "create": [True, True, True, True],
            "read": [False, True, False, False],
            "update": [False, True, True, False],
            "delete": [False, True, True, True]
        }
        perm = crud_perm[crud_type]
        if crud_type == "create" and parent_model_instance:
            user_acl = self._get_user_acl(model_acl, user, perm[0], perm[1], perm[2], perm[3])
            parent_model_instance.acl_ids = [(6, 0, [user_acl.id])]
        else:
            user_acl = self._get_user_acl(model_acl, user, perm[0], perm[1], perm[2], perm[3])
            model_instance.acl_ids = [(6, 0, [user_acl.id])]

    ##########################################
    ###             CREATE                 ###
    ##########################################

    def _pass_assert_create(self, user, vals, model, parent_model_instance, model_acl=False):
        """
        TEST Creazione perm_create -> Il test dovrà andare a buon fine in quanto le acl saranno presenti o per la
        creazione di esse oppure perchè ereditate dal padre
        @param user: res.users
        @param data: {} vals da passare per la creazione
        @param model: env["document/folder..etc"]
        @param parent_model_instance: parent su cui aggiungere le acl per permettere la creaione -> res.document, res.folder
        @param model_acl: env["document_acl/folder_acl..etc"]
        """
        self._get_crud_acl("create", user, model_acl, False, parent_model_instance)

        model_instance = model.with_user(user).create(vals)
        self.assertTrue(isinstance(model_instance.id, int))
        return model_instance

    def _raise_assert_create(self, user, data, model):
        """
        TEST Creazione perm_create -> Il test dovrà fallire perchè non sono presenti ACL
        @param user: res.users
        @param data: {} vals da passare per la creazione
        @param model: env["document/folder..etc"]
        """
        with self.assertRaises(UserError):
            model.with_user(user).create(data)

    ##########################################
    ###                READ                ###
    ##########################################

    def _pass_assert_read(self, user, model_instance, model, model_acl=False):
        """
        TEST Lettura perm_read ACL -> Il test dovrà andare a buon fine in quanto le acl saranno presenti o per la
        creazione oppure perchè ereditate dal padre
        @param user: res.users
        @param model_instance: res.document, res.folder, res.storage
        @param model: env["document/folder/storage..etc"]
        @param model_acl: env["document_acl/folder_acl..etc"]
        """
        self._get_crud_acl("read", user, model_acl, model_instance, False)

        obj_id = model.with_user(user).search([("id", "=", model_instance.id)]).id
        self.assertEqual(model_instance.id, obj_id)

    def _raise_assert_read(self, user, model, model_instance_id):
        """
        TEST Lettura perm_read ACL -> Il test dovrà fallire perchè non sono presenti ACL
        @param user: res.users
        @param model: env["document_acl/folder_acl..etc"]
        @param model_instance_id: res.document.id, res.folder.id, res.storage.id
        """
        model_instance = model.with_user(user).search([("id", "=", model_instance_id)]).id
        self.assertFalse(model_instance)

    ##########################################
    ###             UPDATE                 ###
    ##########################################

    def _pass_assert_update(self, user, vals, model_instance, model_acl=False):
        """
        TEST Scritura perm_write ACL -> Il test dovrà andare a buon fine in quanto le acl saranno presenti o per la
        creazione oppure perchè ereditate dal padre
        @param user: res.users
        @param vals: {} valori da passare per la scrittura
        @param model_instance: res.document, res.folder, res.storage..etc
        @param model_acl: env["document_acl/folder_acl..etc"]
        """
        self._get_crud_acl("update", user, model_acl, model_instance, False)

        result = model_instance.with_user(user).write(vals)
        self.assertTrue(result)

    def _raise_assert_update(self, user, vals, model_instance):
        """
        TEST Scritura perm_write ACL -> Il test dovrà fallire perchè non sono presenti ACL
        @param user: res.users
        @param vals: {} valori da passare per la scrittura
        @param model_instance: res.document, res.folder, res.storage..etc
        """
        with self.assertRaises(UserError):
            model_instance.with_user(user).write(vals)

    ##########################################
    ###             DELETE                 ###
    ##########################################

    @mute_logger("odoo.models.unlink")
    def _pass_assert_delete(self, user, model_instance, model, model_acl=False):
        """
        TEST Unlink perm_delete ACL -> Il test dovrà andare a buon fine in quanto le acl saranno presenti o per la
        creazione oppure perchè ereditate dal padre
        @param user: res.users
        @param model_instance: res.document, res.folder, res.storage
        @param model: env["document/folder/storage..etc"]
        @param model_acl: env["document_acl/folder_acl..etc"]
        """
        self._get_crud_acl("delete", user, model_acl, model_instance, False)

        model_instance.with_user(user).unlink()
        # Accesso ad un campo del documento che, essendo stato eliminato, darà il relativo raise dell'errore
        with self.assertRaises(UserError):
            model.browse(model_instance.id).write_date

    def _raise_assert_delete(self, user, model_instance):
        """
        TEST Unlink perm_delete ACL -> Il test dovrà fallire perchè non sono presenti ACL
        @param user: res.users
        @param model_instance: res.document, res.folder, res.storage
        """
        with self.assertRaises(UserError):
            model_instance.with_user(user).unlink()
