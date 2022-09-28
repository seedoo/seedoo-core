import base64
import os
import random
import re
import string
import tempfile
from io import BytesIO
from subprocess import call

import barcode
import pytz
from barcode.writer import SVGWriter
from lxml import etree
from reportlab.pdfbase import pdfdoc, pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from odoo import http
from odoo.http import request
from odoo.modules import get_module_path


class Etichetta(http.Controller):
    @http.route("/protocollo/etichetta/<string:protocollo_id>", auth="public")
    def etichetta(self, protocollo_id):
        ir_config_obj = request.env['ir.config_parameter'].sudo()
        ir_attachment_obj = request.env["ir.attachment"].sudo()
        etichetta_altezza = int(ir_config_obj.get_param('sd_protocollo.etichetta_altezza'))
        etichetta_larghezza = int(ir_config_obj.get_param('sd_protocollo.etichetta_larghezza'))
        etichetta_logo_id = ir_config_obj.get_param('sd_protocollo.etichetta_logo_id')
        protocol = http.request.env["sd.protocollo.protocollo"].browse(int(protocollo_id))

        protocol_number = "%04d%s.pdf" % (protocol.anno, protocol.numero_protocollo)
        filename, file_extension = os.path.splitext(protocol_number)
        if len(filename) != 11:
            return "Error in protocol number"
        if not protocol:
            return "Protocollo non trovato"

        dest_tz = pytz.timezone("Europe/Rome")
        date_obj = protocol.data_registrazione
        if not date_obj:
            "Il protocollo deve essere registrato"

        date_obj_dest = pytz.utc.localize(date_obj).astimezone(dest_tz)

        name = protocol.numero_protocollo
        protocol_type = protocol.tipologia_protocollo
        header_code = request.env["sd.dms.document"]._get_codice_ipa_aoo(protocol)
        registry_code = protocol.registro_id.codice

        barcode_text = "%04d0%s" % (protocol.anno, name)

        type_str = ""
        # Ricerca la selection con Sudo per avere la visibilità su tutta la selection
        for selection_tuple_value in http.request.env[
            "sd.protocollo.protocollo"]._fields["tipologia_protocollo"].selection:
            if protocol_type == selection_tuple_value[0]:
                type_str = selection_tuple_value[1]
                break

        prot_str = "%s" % name
        datetime_str = date_obj_dest.strftime("%d-%m-%Y %H:%M:%S")

        filename = "%s.pdf" % re.sub(r"[^\w\s]", "", filename)

        tmp_filename = os.path.join(tempfile.gettempdir(), filename)

        pos = LabelPosition()

        # pos.set_pagesize_mm(company.etichetta_larghezza, company.etichetta_altezza)
        pos.set_pagesize_mm(etichetta_larghezza, etichetta_altezza)

        pdfdoc.PDFCatalog.OpenAction = "<</S/JavaScript/JS(this.print\({bUI:true,bSilent:false,bShrinkToFit:false}\);)>>"

        pdf = canvas.Canvas(
            filename=tmp_filename,
            pagesize=pos.get_pagesize_points()
        )

        module_path = get_module_path('sd_protocollo')
        pdfmetrics.registerFont(
            TTFont("sans", os.path.join(module_path, "static/fonts", "LiberationSans-Regular.ttf")))
        pdfmetrics.registerFont(
            TTFont("sans_bold", os.path.join(module_path, "static/fonts", "LiberationSans-Bold.ttf")))
        pdfmetrics.registerFont(
            TTFont("monospace", os.path.join(module_path, "static/fonts", "LiberationMono-Regular.ttf")))
        pdfmetrics.registerFont(
            TTFont("monospace_bold", os.path.join(module_path, "static/fonts", "LiberationMono-Bold.ttf")))

        writer = SVGWriter()
        writer.set_options({
            "compress": False,
            "module_width": pos.x_mm(90),
            "module_height": pos.y_mm(60)
        })
        ean = barcode.get(name="ean13",
                          code=barcode_text,
                          writer=writer)

        temp_filename = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(32))
        temp_image = os.path.join(tempfile.gettempdir(), temp_filename)
        svg_image = open(temp_image, "wb")
        ean.write(svg_image)
        svg_image.close()

        svg_image = open(temp_image, "r")
        svg_lines = svg_image.readlines()
        svg_image.close()

        for i, s in enumerate(svg_lines):
            if any(item in s for item in ["xml version", "DOCTYPE", "DTD SVG 1.1", "http://www.w3.org"]):
                svg_lines[i] = ""

            if "xmlns" in s:
                svg_lines[i] = s.replace(" xmlns=\"http://www.w3.org/2000/svg\"", "")

        svgdoc = etree.fromstringlist(svg_lines)

        for bad in svgdoc.xpath("//rect[@height=\"100%\" and @width=\"100%\"]"):
            bad.getparent().remove(bad)
        for bad in svgdoc.xpath("//text"):
            bad.getparent().remove(bad)
        etree.strip_elements(svgdoc, etree.Comment)

        et = etree.ElementTree(svgdoc)
        svg_image = open(temp_image, "wb")
        et.write(svg_image)
        svg_image.close()

        png_image = "%s.png" % temp_image

        call(["inkscape",
              "--file", temp_image,
              "--export-png", png_image,
              "--export-dpi", "600",
              "--export-area-drawing"])
        os.remove(temp_image)

        pdf.drawImage(png_image,
                      pos.x_p(5), pos.y_p(0),
                      preserveAspectRatio=False,
                      width=pos.x_p(90), height=pos.y_p(30))
        os.remove(png_image)

        temp_text = pdf.beginText(pos.y_p(5), pos.y_p(85))
        temp_text.setFont("sans", 8)
        temp_text.textOut("%s" % header_code)
        pdf.drawText(temp_text)

        temp_text = pdf.beginText(pos.y_p(5), pos.y_p(75))
        temp_text.setFont("sans", 8)
        temp_text.textOut(registry_code)
        pdf.drawText(temp_text)

        temp_text = pdf.beginText(pos.y_p(5), pos.y_p(65))
        temp_text.setFont("sans", 8)
        temp_text.textOut(type_str)
        pdf.drawText(temp_text)

        temp_text = pdf.beginText(pos.y_p(5), pos.y_p(45))
        temp_text.setFont("sans_bold", 8)
        temp_text.textOut("Prot. n. %s " % prot_str)
        pdf.drawText(temp_text)

        temp_text = pdf.beginText(pos.y_p(5), pos.y_p(35))
        temp_text.setFont("sans", 8)
        temp_text.textOut("del %s" % datetime_str)
        pdf.drawText(temp_text)

        if etichetta_logo_id:
            ir_attachment = ir_attachment_obj.search([("id", "=", int(etichetta_logo_id))])
            if ir_attachment.datas:
                etichetta_logo_io = BytesIO(base64.b64decode(ir_attachment.datas))
                etichetta_logo_image_reader = ImageReader(etichetta_logo_io)
                pdf.drawImage(etichetta_logo_image_reader,
                              pos.x_p(61), pos.y_p(61),
                              mask="auto",
                              preserveAspectRatio=True,
                              width=pos.x_p(38), height=pos.y_p(38))

        pdf.save()

        with open(tmp_filename, "rb") as tmpf:
            pdf_content = tmpf.read()

        os.remove(tmp_filename)

        return request.make_response(
            data=pdf_content,
            headers=[
                ("Content-Type", "application/pdf"),
                ("Content-Disposition", "inline; filename=%s" % filename)
            ]
        )


class LabelPosition:
    def __init__(self):
        self._width = 0
        self._height = 0
        pass

    def set_pagesize_mm(self, width, height):
        self._width = DimensionUtility.mm_to_pt(width)
        self._height = DimensionUtility.mm_to_pt(height)

    def get_pagesize_points(self):
        return self._width, self._height

    def x_p(self, width=0):
        if width < 0:
            width = 0
        if width > 100:
            width = 100
        return (self._width / 100) * width

    def y_p(self, height=0):
        if height < 0:
            height = 0
        if height > 100:
            height = 100
        return (self._height / 100) * height

    def x_mm(self, width=0):
        if width < 0:
            width = 0
        if width > 100:
            width = 100
        return DimensionUtility.pt_to_mm((self._width / 100) * width)

    def y_mm(self, height=0):
        if height < 0:
            height = 0
        if height > 100:
            height = 100
        return DimensionUtility.pt_to_mm((self._height / 100) * height)


class DimensionUtility:
    def __init__(self):
        pass

    @staticmethod
    def mm_to_in(value=0):
        return value * 0.0393701

    @staticmethod
    def in_to_mm(value=0.00):
        return value / 0.0393701

    @staticmethod
    def mm_to_pt(value=0):
        return DimensionUtility.mm_to_in(value) * 72

    @staticmethod
    def pt_to_mm(value=0.00):
        return DimensionUtility.in_to_mm(value / 72)

    @staticmethod
    def xymm_to_pt(value=(0, 0)):
        return (
            DimensionUtility.mm_to_pt(value[0]),
            DimensionUtility.mm_to_pt(value[1]),
        )
