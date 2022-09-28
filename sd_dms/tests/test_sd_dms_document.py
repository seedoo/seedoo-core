from odoo.addons.sd_dms.tests.common import DmsTestCommon
from odoo.exceptions import UserError
from odoo.tests import tagged


@tagged('-standard', 'sd_dms')
class DmsTestDocument(DmsTestCommon):

    @classmethod
    def setUpClass(cls):
        super(DmsTestDocument, cls).setUpClass()
        folder_acl = cls._get_user_acl(cls.folder_acl_obj, cls.user0, create=True, read=True, write=True, delete=True)
        cls.subfolder.acl_ids = [(6, 0, [folder_acl.id])]

        cls.category_id = cls.category_obj.create({
            "name": "Category1",
            "company_id": cls.other_company.id
        })
        cls.document = cls.document_obj.with_user(cls.admin).create(cls.document_data)

    def test_document_mimetype(self):
        self.assertEqual(self.document.mimetype, "image/png")

    def test_document_extension(self):
        self.assertEqual(self.document.extension, "png")

    def test_document_category(self):
        # Test della company del documento, andrà in errore perchè la category che stiamo andando ad associare al documento
        # ha una company diversa da quella del documento
        document = self.document_obj.create(self.document_data)
        with self.assertRaises(UserError):
            document.category_id = self.category_id.id

    def test_document_acl(self):
        folder = self.folder_obj.browse(self.subfolder_id)

        # Creazione senza ACL sulla folder di un documento
        self._raise_assert_create(self.user2, self.document_data, self.document_obj)
        # Creazione con ACL sulla folder di un documento
        self._pass_assert_create(self.user2, self.document_data, self.document_obj, folder, self.folder_acl_obj)

        # Lettura senza ACL sul documento
        self._raise_assert_read(self.user1, self.document_obj, self.document.id)
        # Lettura con ACL sul documento
        self._pass_assert_read(self.user1, self.document, self.document_obj, self.document_acl_obj)

        # Scrittura senza ACL sul documento
        data = {"subject": "acl"}
        self._raise_assert_update(self.user1, data, self.document)
        # Scrittura con ACL sul documento
        self._pass_assert_update(self.user1, data, self.document, self.document_acl_obj)

        # Eliminazione del documento senza ACL
        self._raise_assert_delete(self.user1,self.document)
        # Eliminazione con ACL
        self._pass_assert_delete(self.user1, self.document, self.document_obj, self.document_acl_obj)

    def test_document_inherited_acl(self):
        self._pass_assert_read(self.user0, self.document, self.document_obj)
        self._pass_assert_update(self.user0, {"subject": "acl"}, self.document)
        self._pass_assert_delete(self.user0, self.document, self.document_obj)
