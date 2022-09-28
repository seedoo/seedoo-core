import base64
import io

import qrcode.image.svg
from qrcode import QRCode

from odoo import models


class QRUtility(models.AbstractModel):
    _name = "fl.utility.qr"
    _description = "Utility for creating QR-Codes"

    def render_svg(
            self,
            content: str,
            box_size: int = 10,
            border: int = 4,
            color: str = "#000000",
            logo_enabled: bool = False,
            logo_size: float = 0.2,
            logo_image: bytes = b""
    ) -> bytes:
        xml_utility = self.env["fl.utility.xml"]
        mime_utility = self.env["fl.utility.mime"]

        namespaces = {
            "svg": "http://www.w3.org/2000/svg"
        }

        svg_qrcode = self._render_svg_qr(content, box_size=box_size, border=border)
        svg_root = xml_utility.parse(svg_qrcode)
        svg_root_attribs: dict = dict(svg_root.attrib)

        view_box: str = svg_root_attribs["viewBox"]
        vals = view_box.split()

        width = int(float(vals[2]))
        height = int(float(vals[3]))

        svg_polygon_background = xml_utility.create_root_element("polygon", attribs={
            "points": " ".join([f"{x},{y}" for x, y in [(0, 0), (0, height), (width, height), (width, 0)]]),
            "style": "fill: white; stroke-width: 0;"
        })

        svg_path_qr = svg_root.xpath("//svg:path[@id='qr-path']", namespaces=namespaces)[0]
        svg_path_qr.attrib["fill"] = color
        svg_path_qr.addprevious(svg_polygon_background)

        if logo_enabled:
            mime_type = mime_utility.guess_by_content(logo_image)
            logo_base64: bytes = base64.b64encode(logo_image)
            logo_base64_str: str = logo_base64.decode()
            href: str = f"data:{mime_type};charset=utf-8;base64,{logo_base64_str}"

            image_width: int = round(float(width * logo_size))
            image_height: int = round(float(height * logo_size))

            image_x = (width - image_width) / 2
            image_y = (height - image_height) / 2

            svg_logo = xml_utility.create_root_element("image", attribs={
                "href": href,
                "x": str(image_x),
                "y": str(image_y),
                "width": str(image_width),
                "height": str(image_height)
            })

            svg_logo_background = xml_utility.create_root_element("polygon", attribs={
                "points": " ".join([f"{x},{y}" for x, y in [
                    (image_x, image_y),
                    (image_x, image_y + image_height),
                    (image_x + image_width, image_y + image_height),
                    (image_x + image_width, image_y)
                ]]),
                "style": "fill: white; stroke-width: 0;"
            })

            svg_path_qr.addnext(svg_logo)
            svg_logo.addprevious(svg_logo_background)

        svg_raw: str = xml_utility.serialize(svg_root)
        return svg_raw.encode()

    @staticmethod
    def _render_svg_qr(text: str, box_size: int = 10, border: int = 4) -> str:
        qr: QRCode = QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=box_size,
            border=border
        )

        qr.add_data(text)
        qr.image_factory = qrcode.image.svg.SvgPathImage
        qr.make(fit=True)

        img = qr.make_image()

        stream = io.BytesIO()
        img.save(stream)
        data: str = stream.getvalue().decode()

        return data

    @staticmethod
    def _unit_to_px(val: float) -> int:
        return int((val * 96.0) / 25.4)

    @staticmethod
    def _px_to_unit(val: int) -> float:
        return float((val / 96.0) * 25.4)
