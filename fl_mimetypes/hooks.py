import mimetypes


def _check_mimetypes_p7m():
    # Gestione mimetype .p7m non presente
    extension = mimetypes.guess_type("test.p7m")
    if extension and extension[0] == "application/pkcs7-mime":
        return
    mimetypes.add_type('application/pkcs7-mime', '.p7m')