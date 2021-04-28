import datetime
import os
import random
import string
import re
import urllib2
import logging

import pypandoc
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
