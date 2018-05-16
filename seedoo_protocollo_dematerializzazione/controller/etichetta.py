import base64
import os
import random
import re
import string
import tempfile
from io import BytesIO
from subprocess import call
from time import strftime

import barcode
import pytz
import datetime
from PIL import Image
from barcode.writer import SVGWriter
from lxml import etree
from reportlab.pdfbase import pdfdoc, pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from openerp import http, SUPERUSER_ID
from openerp.http import request
from openerp.modules import get_module_path
from ..utility.dimension import DimensionUtility


class Etichetta(http.Controller):
    @http.route("/seedoo/etichetta/<int:protocol_id>", auth="public")
    def object(self, protocol_id, **kw):
        uid = SUPERUSER_ID
        cr = http.request.cr
        ir_model_data_obj = request.registry.get('ir.model.data')
        ir_model_data_id = ir_model_data_obj.search(cr, uid, [('name', '=', 'configurazione_default')])[0]
        ir_model_data = ir_model_data_obj.browse(cr, uid, ir_model_data_id)
        configurazione = request.registry.get(ir_model_data.model).browse(cr, uid, ir_model_data.res_id)

        document = http.request \
            .env["protocollo.protocollo"] \
            .with_context({'skip_check': True}) \
            .search([["id", "=", protocol_id]])

        if len(document) == 0:
            return "Document not found"

        number = document.name

        dest_tz = pytz.timezone("Europe/Rome")
        date_obj = datetime.datetime.strptime(document.registration_date, "%Y-%m-%d %H:%M:%S")
        date_obj_dest = pytz.utc.localize(date_obj).astimezone(dest_tz)

        year = document.year
        type = document.type  # IN or OUT
        ammi_code = document.registry.company_id.ammi_code
        ident_code = document.aoo_id.ident_code
        header_code = ammi_code + " - " + ident_code if ammi_code else ident_code
        registry_code = document.registry.code

        barcode_text = "%04d0%s" % (year, number)
        type_str = "Ingresso" if type == "in" else "Uscita"
        prot_str = "%s" % (number)
        datetime_str = date_obj_dest.strftime("%Y-%m-%d %H:%M:%S")

        filename = re.sub(r"[^\w\s]", "", number)
        filename = re.sub(r"\s+", " ", filename)
        filename = "%s - %s.pdf" % (strftime("%Y-%m-%d %H-%M-%S"), filename)

        tmp_filename = os.path.join(tempfile.gettempdir(), filename)

        pos = LabelPosition()
        # pos.set_pagesize_mm(company.etichetta_larghezza, company.etichetta_altezza)
        pos.set_pagesize_mm(configurazione.etichetta_larghezza, configurazione.etichetta_altezza)

        pdfdoc.PDFCatalog.OpenAction = "<</S/JavaScript/JS(this.print\({bUI:true,bSilent:false,bShrinkToFit:false}\);)>>"

        pdf = canvas.Canvas(
            filename=tmp_filename,
            pagesize=pos.get_pagesize_points()
        )

        module_path = get_module_path('seedoo_protocollo_dematerializzazione')
        pdfmetrics.registerFont(TTFont("sans", os.path.join(module_path, "fonts", "LiberationSans-Regular.ttf")))
        pdfmetrics.registerFont(TTFont("sans_bold", os.path.join(module_path, "fonts", "LiberationSans-Bold.ttf")))
        pdfmetrics.registerFont(TTFont("monospace", os.path.join(module_path, "fonts", "LiberationMono-Regular.ttf")))
        pdfmetrics.registerFont(TTFont("monospace_bold", os.path.join(module_path, "fonts", "LiberationMono-Bold.ttf")))

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

        svg_image = open(temp_image, "rb")
        svg_lines = svg_image.readlines()
        svg_image.close()

        for i, s in enumerate(svg_lines):
            if any(item in s for item in
                   ["xml version", "DOCTYPE", "DTD SVG 1.1", "http://www.w3.org"]):
                svg_lines[i] = ""
            if "xmlns" in s:
                svg_lines[i] = s.replace(" xmlns=\"http://www.w3.org/2000/svg\"", "")

        svgdoc = etree.fromstringlist(svg_lines)

        for bad in svgdoc.xpath("//rect[@height=\"100%\" and @width=\"100%\"]"):
            bad.getparent().remove(bad)

        for bad in svgdoc.xpath("text"):
            bad.getparent().remove(bad)

        for bad in svgdoc.xpath("//rect[last()]"):
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

        # TODO: What to do with barcode number????
        # text_width = stringWidth(barcode_text, "monospace", 5)
        # temp_text = pdf.beginText((pos.get_pagesize_points()[0] - text_width) / 2, pos.y_p(0))
        # temp_text.setFont("monospace", 5)
        # temp_text.textOut(ean.get_fullcode())
        # pdf.drawText(temp_text)

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

        company_logo_data = base64.b64decode(document.registry.company_id.logo_web)
        company_logo_png = Image.open(BytesIO(company_logo_data))
        company_logo = Image.new("RGB", company_logo_png.size, (255, 255, 255))
        company_logo.paste(company_logo_png, (0, 0), company_logo_png)

        company_logo_filename = os.path.join(tempfile.gettempdir(),
                                             "".join(random.choice(string.ascii_letters + string.digits)
                                                     for _ in range(32)))
        company_logo_image = open(company_logo_filename, "wb")
        company_logo.save(company_logo_image, format="PNG")
        company_logo_image.close()

        pdf.drawImage(company_logo_filename,
                      pos.x_p(61), pos.y_p(61),
                      preserveAspectRatio=True,
                      width=pos.x_p(38), height=pos.y_p(38))
        os.remove(company_logo_filename)

        pdf.save()

        with file(tmp_filename) as tmpf:
            pdf_content = tmpf.read()

        os.remove(tmp_filename)

        return request.make_response(pdf_content,
                                     [("Content-Type", "application/pdf"),
                                      ("Content-Disposition", "inline; filename=%s" % filename)])


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
