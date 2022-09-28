from odoo import models, api
from odoo.tools.translate import _
from odoo.tools.misc import find_in_path
from contextlib import closing
import tempfile
import subprocess
import logging
import os

_logger = logging.getLogger(__name__)


class UtilityPdf(models.AbstractModel):
    _name = "fl.utility.pdf"
    _description = "Utility for PDF printing"

    @api.model
    def html2pdf(self, html_content):
        try:
            command_args = []
            temporary_files = []
            wkhtmltopdf_bin_path = find_in_path("wkhtmltopdf")
            # add charset utf-8 to encode correctly all characters (example: accented characters, etc)
            if html_content:
                html_content = "<head><meta charset='utf-8'></head>" + html_content
            # write html content in a temporary file html_content_file
            html_content_fd, html_content_path = tempfile.mkstemp(suffix=".html", prefix="content.tmp.")
            with closing(os.fdopen(html_content_fd, "w")) as html_content_file:
                html_content_file.write(html_content)
            temporary_files.append(html_content_path)
            # create a temporary file pdf_content_file in which to write pdf content
            pdf_content_fd, pdf_content_path = tempfile.mkstemp(suffix=".pdf", prefix="content.tmp.")
            os.close(pdf_content_fd)
            temporary_files.append(pdf_content_path)
            # generate pdf content using wkhtmltopdf bin and write in pdf_content_file
            wkhtmltopdf = [wkhtmltopdf_bin_path] + command_args + [html_content_path] + [pdf_content_path]
            process = subprocess.Popen(wkhtmltopdf, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = process.communicate()
            # if there is an error then write log and return None content
            if process.returncode not in [0, 1]:
                error_message = "Wkhtmltopdf failed (error code: %s)."
                if process.returncode == -11:
                    error_message_d = "Memory limit too low or maximum file number of subprocess reached. Message : %s"
                else:
                    error_message_d = "Message: %s"
                    message = _("Wkhtmltopdf failed (error code: %s). Message: %s")
                message = "%s %s" % _(error_message + error_message_d)
                _logger.error(message, process.returncode, err[-1000:])
                return None
            if err:
                _logger.warning("wkhtmltopdf: %s" % err)
            # read content from pdf_content_file
            with open(pdf_content_path, "rb") as pdf_file:
                pdf_content = pdf_file.read()
            # manual cleanup of the temporary files
            for temporary_file in temporary_files:
                try:
                    os.unlink(temporary_file)
                except (OSError, IOError):
                    _logger.error("Error when trying to remove file %s" % temporary_file)
            # return pdf content
            return pdf_content
        except Exception as e:
            logging.error("Error in html to pdf converting process: %s" % str(e))
            return None