import base64
import datetime
import json
import logging
from typing import Optional, List

import pytz

from odoo import models, api
from odoo.http import Response, content_disposition, request

_logger = logging.getLogger(__name__)


def encode_special_item(obj):
    if isinstance(obj, datetime.datetime):
        if not obj.tzinfo:
            obj = obj.replace(tzinfo=pytz.UTC)
        return obj.isoformat()

    raise TypeError


class ControllerUtility(models.AbstractModel):
    _name = "fl.utility.controller"
    _description = "utilities for HTTP controllers"

    @api.model
    def response_no_body(self):
        return self.prepare_response(status_code=204)

    @api.model
    def response_forbidden(self, response_body: Optional[dict] = None):
        return self.prepare_response(status_code=403, response_body=response_body)

    @api.model
    def response_not_found(self, response_body: Optional[dict] = None):
        return self.prepare_response(status_code=404, response_body=response_body)

    @api.model
    def response_unprocessable_entity(self, response_body: Optional[dict] = None):
        return self.prepare_response(status_code=422, response_body=response_body)

    @api.model
    def response_not_implemented(self, response_body: Optional[dict] = None):
        return self.prepare_response(status_code=501, response_body=response_body)

    @api.model
    def prepare_response(self, status_code: int = 200, response_body: Optional[dict] = None) -> Response:
        if not response_body:
            response_body = {}

        response_headers: List[tuple] = [
            ("Content-Type", "application/json")
        ]

        response_body_raw: bytes = b""

        if status_code != 204:
            try:
                response_string = json.dumps(obj=response_body, default=encode_special_item)
            except TypeError as e:
                _logger.error(e)
                raise e
            response_body_raw = response_string.encode()

        return Response(
            status=status_code,
            response=response_body_raw,
            headers=response_headers
        )

    @api.model
    def attachment(self, ir_attachment_id: int, force_download: bool = False) -> Response:
        ir_attachment_obj = self.env["ir.attachment"].sudo()

        ir_attachment = ir_attachment_obj.search([("id", "=", ir_attachment_id)])
        if not ir_attachment:
            return self.response_not_found()

        image_data: bytes = base64.b64decode(ir_attachment.datas)
        image_filename: str = ir_attachment.name
        image_mimetype: str = ir_attachment.mimetype

        headers: List[tuple] = [
            ("Content-Type", image_mimetype),
            ("Content-Length", len(image_data))
        ]

        if force_download:
            headers.append(
                ("Content-Disposition", content_disposition(image_filename))
            )

        return Response(
            response=image_data,
            headers=headers
        )

    @api.model
    def compute_image_url(self, res_model: str, res_id: int, field_name: str) -> str:
        return self.compute_url(f"/web/image/{res_model}/{res_id}/{field_name}")

    @api.model
    def compute_url(self, url: str) -> str:
        ir_config_parameter_obj = self.env["ir.config_parameter"].sudo()
        base_url: str = ir_config_parameter_obj.get_param("web.base.url")
        return f"{base_url}{url}"
