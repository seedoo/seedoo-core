import base64
import binascii
from typing import Union

from odoo import models, api


class Base64Utility(models.AbstractModel):
    _name = "fl.utility.base64"
    _description = "Base64 utility"

    @api.model
    def is_valid_base64(self, content: Union[str, bytes] = b"") -> bool:
        if len(content) == 0:
            return True  # Empty string has to be considered as a valid base64

        input_value: bytes

        if isinstance(content, bytes):
            input_value = content
        else:
            input_value = content.encode()

        try:
            decoded: bytes = base64.b64decode(input_value, validate=True)
            re_encoded: bytes = base64.b64encode(decoded)
        except binascii.Error:
            return False

        return bool(re_encoded == input_value)

    @api.model
    def encode(self, content: Union[str, bytes] = b"") -> str:
        if isinstance(content, str):
            content = content.encode()
        return base64.urlsafe_b64encode(content).decode()

    @api.model
    def decode(self, content: Union[str, bytes] = b"") -> str:
        if isinstance(content, str):
            content = content.encode()
        return base64.b64decode(content).decode()
