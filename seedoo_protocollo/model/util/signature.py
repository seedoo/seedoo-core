# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DSDT
from openerp.tools.translate import _
from openerp.osv import orm
import subprocess
import datetime
import logging
import shutil
import base64
import os

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
}

class Signature(orm.Model):
    _name = 'protocollo.signature'

    def sign_doc(self, cr, uid, prot, prot_number, prot_date, document, attachment_index=False):
        pd = prot_date.split(' ')[0]
        prot_date = datetime.datetime.strptime(pd, DSDT)

        prot_dir = ''
        for selection_tuple_value in self.pool.get('protocollo.protocollo')._fields['type'].selection:
            if prot.type == selection_tuple_value[0]:
                prot_dir = selection_tuple_value[1].upper()
                break

        ammi_code = prot.registry.company_id.ammi_code + " - " if prot.registry.company_id.ammi_code else ""
        attachment_name = " - All. " + str(attachment_index) if attachment_index else ""
        prot_def = "%s%s - %s - %s - Prot. n. %s del %s%s" % (
            ammi_code,
            prot.aoo_id.ident_code,
            prot.registry.code,
            prot_dir,
            prot_number,
            prot_date.strftime("%d-%m-%Y"),
            attachment_name
        )

        return self._sign_doc(cr, uid, prot, prot_number, prot_date, prot_def, document)


    def _sign_doc(self, cr, uid, prot, prot_number, prot_date, prot_def, document, all_pages=False):
        return self._sign_doc_old(cr, uid, prot, prot_number, prot_date, prot_def, document, all_pages)


    def _sign_doc_old(self, cr, uid, prot, prot_number, prot_date, prot_def, document, all_pages):
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
            prot_def
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


    def _sign_doc_new(self, cr, uid, prot, prot_number, prot_date, prot_def, document, all_pages):
        attachment_obj = self.pool.get('ir.attachment')
        file_path_input = attachment_obj._full_path(cr, uid, document.store_fname)
        file_path_output = file_path_input + '_' + prot_number

        signature_jar = "signature2.jar"
        signature_cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)), signature_jar)
        signature_mode = "--all-pages" if all_pages else "--first-page"
        cmd = [
            "java",
            "-XX:MaxHeapSize=1g",
            "-XX:InitialHeapSize=512m",
            "-XX:CompressedClassSpaceSize=64m",
            "-XX:MaxMetaspaceSize=128m",
            "-XX:+UseConcMarkSweepGC",
            "-jar",
            signature_cmd,
            "--input", file_path_input,
            "--output", file_path_output,
            signature_mode,
            prot_def
        ]

        returncode = subprocess.call(cmd)
        if returncode != 0:
            error = "Signature Error: %s" % SIGNATURE_RETURN_CODE[returncode]
            raise Exception(error)

        signed_file = open(file_path_output, 'r')
        signed_file_datas = base64.encodestring(signed_file.read())
        signed_file.close()
        # eliminazione del file con la signature
        os.remove(file_path_output)

        return signed_file_datas