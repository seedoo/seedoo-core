from odoo.addons.sd_dms.tests.common import DmsTestCommon
from odoo.tests import tagged


@tagged('-standard', 'sd_dms')
class DmsTestFolder(DmsTestCommon):

    @classmethod
    def setUpClass(cls):
        super(DmsTestFolder, cls).setUpClass()
        folder_acl = cls._get_user_acl(cls.folder_acl_obj, cls.user2, create=True, read=True, write=True, delete=True)
        cls.subfolder.acl_ids = [(6, 0, [folder_acl.id])]
        folder_vals = {
            "name": "Subfolder/Subfolder1",
            "is_root_folder": False,
            "parent_folder_id": cls.subfolder_id,
            "inherit_acl": True
        }
        cls.subsubfolder1 = cls.folder_obj.create(folder_vals)

    def test_folder_acl(self):
        subfolder = self.folder_obj.browse(self.subfolder_id)

        # Creazione senza ACL sulla cartella padre
        folder_vals = {
            "name": "Subfolder/Subfolder0",
            "is_root_folder": False,
            "parent_folder_id": self.subfolder_id,
            "inherit_acl": False
        }
        self._raise_assert_create(self.user0, folder_vals, self.folder_obj)
        # Creazione con ACL sulla cartella padre
        folder = self._pass_assert_create(self.user0, folder_vals, self.folder_obj, subfolder, self.folder_acl_obj)

        # Lettura cartella senza ACL sulla folder padre
        self._raise_assert_read(self.user1, self.folder_obj, folder.id)
        # Lettura cartella con ACL sulla folder padre
        self._pass_assert_read(self.user1, folder, self.folder_obj, self.folder_acl_obj)

        folder_data = {"name": "Subfolder0ACL"}
        # Scrittura senza ACL sulla cartella
        self._raise_assert_update(self.user1, folder_data, folder)
        # Scrittura con ACL sulla cartella
        self._pass_assert_update(self.user1, folder_data, folder, self.folder_acl_obj)

        # Eliminazione della cartella senza ACL
        self._raise_assert_delete(self.user1, folder)
        # Eliminazione con ACL
        self._pass_assert_delete(self.user1, folder, self.folder_obj, self.folder_acl_obj)

    def test_folder_inherited_acl(self):
        self._pass_assert_read(self.user2, self.subsubfolder1, self.folder_obj)
        self._pass_assert_update(self.user2, {"name": "Subfolder0ACL"}, self.subsubfolder1)
        self._pass_assert_delete(self.user2, self.subsubfolder1, self.folder_obj)
