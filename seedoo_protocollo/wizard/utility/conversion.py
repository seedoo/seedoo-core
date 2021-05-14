import datetime
import os
import random
import string
import re
import subprocess
import urllib2
import logging
import pypandoc
import tempfile

from contextlib import closing
from openerp.tools.misc import find_in_path
from BeautifulSoup import BeautifulSoup

_logger = logging.getLogger(__name__)


class ConversionUtility:
    def __init__(self):
        pass

    @staticmethod
    def html_to_pdf_file(body="", css_file=""):
        now = datetime.datetime.now()
        random_string = "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(16))
        tempfile = "/tmp/seedoo-temp-%s-%s.pdf" % (now.strftime("%Y%m%d%H%M%S"), random_string)

        extra_args = ["--standalone"]

        if css_file and len(css_file) > 0 and os.path.isfile(css_file):
            extra_args.append("--css=%s" % css_file)

        cleaned_body = ConversionUtility.remove_img(body)

        pypandoc.convert(
            cleaned_body,
            "html5",
            outputfile=tempfile,
            format="html",
            extra_args=extra_args)

        return tempfile

    @staticmethod
    def html_to_pdf(body="", css_file=""):
        tempfile = ConversionUtility.html_to_pdf_file(body=body, css_file=css_file)

        with file(tempfile) as tmpf:
            pdf_content = tmpf.read()

        os.remove(tempfile)
        return pdf_content

    @staticmethod
    def html_to_pdf_by_wkhtml(html_content):
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
                    message = "Wkhtmltopdf failed (error code: %s). Message: %s"
                message = "%s %s" % (error_message, error_message_d)
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


    # TODO: sostituire con un metodo per il parsing delle immagini come viene impiegato nella verisone 12 di odoo
    @staticmethod
    def remove_img(content=""):
        ret = content

        while "<img" in ret:
            soup = BeautifulSoup(ret)
            soup.img.decompose()
            ret = str(soup)

        try:
            regular_expression = '.*background-image: ?url\(.*\).*;?'
            soup = BeautifulSoup(ret)
            results = soup.findAll(attrs={'style': re.compile(regular_expression)})
            for result in results:
                for attribute in result.attrs:
                    if attribute[0]=='style' and re.match(regular_expression, attribute[1]):
                        found = re.search(regular_expression, attribute[1])
                        if found:
                            url_to_check = re.sub(".*background-image: ?url\('", '', found.group(0))
                            url_to_check = re.sub("'\).*;?", '', url_to_check)
                            error = False
                            try:
                                ret = urllib2.urlopen(url_to_check)
                            except Exception as e:
                                error = True
                            if error or ret.code!=200:
                                result['style'] = attribute[1].replace("url('" + url_to_check + "')", 'none')
            ret = str(soup)
        except Exception as e:
            _logger.error(str(e))
        return ret
