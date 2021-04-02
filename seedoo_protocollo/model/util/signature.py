# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DSDT
from openerp.tools.translate import _
from openerp.osv import orm
from ..protocollo import convert_datetime
import subprocess
import datetime
import logging
import shutil
import base64
import os
import resource

_logger = logging.getLogger(__name__)

SIGNATURE_RETURN_CODE = {
    0: 'OK',
    1: 'GENERIC_ERROR',
    10: 'INVALID_COMMAND_LINE',
    11: 'INVALID_INPUT_FILE',
    12: 'INVALID_OUTPUT_FILE',
    13: 'INVALID_SIGNATURE_TEXT',
    20: 'FILE_ERROR',
    30: 'PDF_TOOL_ERROR',
    40: 'SIGNED_PDF'
}

class Signature(orm.Model):
    _name = 'protocollo.signature'

    def sign_doc(self, cr, uid, prot, prot_number, prot_date, document, attachment_index=False):
        signature_string = "%s%s - %s%s - %s - Prot. n. %s del %s%s" % (
            self._get_ammi_code(cr, uid, prot),
            self._get_aoo_code(cr, uid, prot),
            self._get_registry_code(cr, uid, prot),
            self._get_department_code(cr, uid, prot),
            self._get_protocollo_type(cr, uid, prot),
            self._get_protocollo_number(cr, uid, prot, prot_number),
            self._get_protocollo_date(cr, uid, prot, prot_date),
            self._get_attachment_name(cr, uid, prot, attachment_index)
        )
        return self._sign_doc(cr, uid, prot, prot_number, prot_date, signature_string, document)


    def _get_ammi_code(self, cr, uid, prot):
        return prot.registry.company_id.ammi_code + " - " if prot.registry.company_id.ammi_code else ""


    def _get_aoo_code(self, cr, uid, prot):
        return prot.aoo_id.ident_code


    def _get_registry_code(self, cr, uid, prot):
        return prot.registry.code


    def _get_department_code(self, cr, uid, prot):
        return ''


    def _get_protocollo_type(self, cr, uid, prot):
        protocollo_type = ''
        for selection_tuple_value in self.pool.get('protocollo.protocollo')._fields['type'].selection:
            if prot.type == selection_tuple_value[0]:
                protocollo_type = selection_tuple_value[1].upper()
                break
        return protocollo_type


    def _get_protocollo_number(self, cr, uid, prot, prot_number):
        return prot_number


    def _get_protocollo_date(self, cr, uid, prot, prot_date):
        return convert_datetime(prot_date, from_timezone="UTC", to_timezone="Europe/Rome", format_to="%d-%m-%Y")


    def _get_attachment_name(self, cr, uid, prot, attachment_index):
        return " - All. " + str(attachment_index) if attachment_index else ""


    def _sign_doc(self, cr, uid, prot, prot_number, prot_date, signature_string, document, all_pages=False):
        return self._sign_doc_old(cr, uid, prot, prot_number, prot_date, signature_string, document, all_pages)


    def _sign_doc_old(self, cr, uid, prot, prot_number, prot_date, signature_string, document, all_pages):
        attachment_obj = self.pool.get('ir.attachment')
        file_path_orig = attachment_obj._full_path(cr, uid, document.store_fname)
        file_path = file_path_orig + '_' + prot_number
        # duplica il file con un percorso univoco per evitare problematiche nella generazione del file con la signature
        # nel caso ci siano due protocolli da registrare con stesso file. La procedura potrebbe essere migliorata se ci
        # fosse un modo per generare il file con la signature con un nome contenente il numero del protocollo.
        shutil.copy(file_path_orig, file_path)

        maintain_orig = False
        strong_encryption = False

        signature_jar = "signature.jar"
        signature_cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)), signature_jar)
        cmd = [
            "java",
            "-XX:MaxHeapSize=1g",
            "-XX:InitialHeapSize=512m",
            "-XX:CompressedClassSpaceSize=64m",
            "-XX:MaxMetaspaceSize=128m",
            "-XX:+UseConcMarkSweepGC",
            "-jar",
            signature_cmd,
            file_path,
            signature_string
        ]

        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
            stdoutdata, stderrdata = proc.communicate()
            if proc.wait() != 0:
                _logger.warning(stdoutdata)
                raise Exception(stderrdata)
            if os.path.isfile(file_path + '.dec.pdf'):
                maintain_orig = True
            if os.path.isfile(file_path + '.enc'):
                strong_encryption = True
                os.remove(file_path + '.enc')
            if os.path.isfile(file_path + '.fail'):
                os.remove(file_path + '.fail')
                raise orm.except_osv(_("Errore"), _("Qualcosa è andato storto nella aggiunta della segnatura!"))
        except Exception as e:
            raise Exception(e)
        finally:
            # eliminazione del file duplicato
            os.remove(file_path)

        signed_file_datas = document.datas
        if maintain_orig:
            self._create_attachment_encryped_file(cr, uid, prot, file_path + '.dec.pdf')
        elif strong_encryption:
            pass
        else:
            # shutil.move(file_path + '.pdf', file_path)
            signed_file_path = file_path + '.pdf'
            signed_file = open(signed_file_path, 'r')
            signed_file_datas = base64.encodestring(signed_file.read())
            signed_file.close()
            # eliminazione del file con la signature
            os.remove(signed_file_path)

        # return sha1OfFile(file_path_for_sha1)
        return signed_file_datas


    def _sign_doc_new(self, cr, uid, prot, prot_number, prot_date, signature_string, document, all_pages):
        attachment_obj = self.pool.get('ir.attachment')
        file_path_input = attachment_obj._full_path(cr, uid, document.store_fname)
        file_path_output = file_path_input + '_' + prot_number

        signature_jar = "signature2.jar"
        signature_cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)), signature_jar)
        signature_mode = "--all-pages" if all_pages else "--first-page"
        cmd = self._get_cmd(cr, uid, signature_cmd, file_path_input, file_path_output, signature_mode, signature_string)
        #returncode = subprocess.call(cmd)
        def set_limits():
            resource.setrlimit(resource.RLIMIT_AS, (-1, -1))
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=set_limits)
        stdoutdata, stderrdata = proc.communicate()
        returncode = proc.wait()
        if returncode == 40:
            return None
        elif returncode != 0:
            if stdoutdata:
                _logger.warning(stdoutdata)
            if stderrdata:
                _logger.error(stderrdata)
            error = "Signature Error: %s" % SIGNATURE_RETURN_CODE[returncode]
            raise Exception(error)

        signed_file = open(file_path_output, 'r')
        signed_file_datas = base64.encodestring(signed_file.read())
        signed_file.close()
        # eliminazione del file con la signature
        os.remove(file_path_output)

        return signed_file_datas

    def _get_cmd(self, cr, uid, signature_cmd, file_path_input, file_path_output, signature_mode, signature_string):
        return [
            "java",
            # "-Xms256m",
            # "-Xmx512m",
            "-jar",
            signature_cmd,
            "--input", file_path_input,
            "--output", file_path_output,
            signature_mode,
            signature_string
        ]