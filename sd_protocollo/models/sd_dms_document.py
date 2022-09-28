from odoo import fields, models, api, _, SUPERUSER_ID
from odoo.modules import get_module_path
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
import os
import base64
import subprocess
import logging
import pytz
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

SELECTION_STATE_ADD = [
    ("registered", _("Registered"))
]

SELECTION_REGISTRATION_TYPE_ADD = [
    ("protocol", "Protocol"),
]

class Document(models.Model):
    _inherit = "sd.dms.document"

    state = fields.Selection(
        selection_add=SELECTION_STATE_ADD,
    )

    protocollo_id = fields.Many2one(
        string="Protocollo",
        comodel_name="sd.protocollo.protocollo",
        readonly=True,
        ondelete="set null",
        index=True
    )

    numero_protocollo_id = fields.Char(
        string="Numero Protocollo",
        related="protocollo_id.numero_protocollo",
        readonly=True
    )

    protocollo_segnatura_pdf = fields.Boolean(
        string="Segnatura PDF"
    )

    registration_type = fields.Selection(
        selection_add=SELECTION_REGISTRATION_TYPE_ADD
    )

    created_by_protocol = fields.Boolean(
        string="Created by protocol"
    )

    @api.depends("protocollo_id.state")
    def _compute_state(self):
        for rec in self:
            if rec.protocollo_id and rec.protocollo_id.state == "registrato":
                rec.state = "registered"
            elif rec.protocollo_id and rec.protocollo_id.state == "annullato":
                rec.state = "registration_canceled"

    @api.depends("protocollo_id.data_registrazione")
    def _compute_registration_date(self):
        for rec in self:
            if rec.protocollo_id and rec.protocollo_id.data_registrazione:
                rec.registration_date = rec.protocollo_id.data_registrazione

    @api.model
    def create(self, vals):
        # si recupera l'eventuale valore del protocollo_id presente nei vals
        protocollo_id = vals.get("protocollo_id", False)
        # se non è presente il protocollo_id si controla che non sia presente nel context
        if not protocollo_id:
            protocollo_id = self.env.context.get("default_protocollo_id", False)
        # se non è presente il protocollo_id si continua con il normale flusso di creazione del document
        if not protocollo_id:
            return super(Document, self).create(vals)
        # si imposta il valore created_by_protocol al document che si sta creando
        vals.update({
            "inherit_acl": False,
            "created_by_protocol": True
        })
        protocollo = self.env["sd.protocollo.protocollo"].browse(protocollo_id)
        # si recupera la tipologia del documento da creare per il protocollo
        tipologia_documento_protocollo = self.env.context.get("tipologia_documento_protocollo", "allegato")
        # se il protocollo è in stato registrato ed è abilitata la configurazione per rinominare i documenti/allegati
        # allora si deve impostare il corretto filename del document da creare
        config_obj = self.env["ir.config_parameter"].sudo()
        rinomina_documento_allegati = bool(config_obj.get_param("sd_protocollo.rinomina_documento_allegati"))
        if protocollo.state == "registrato" and rinomina_documento_allegati:
            vals["filename"] = protocollo.get_filename_documento_protocollo(
                vals["filename"], tipologia_documento_protocollo.title()
            )
        # si crea il document
        document = super(Document, self).create(vals)
        # se il document creato è il documento principale del protocollo allora si salva il riferimento del document
        # all'interno del protocollo
        if tipologia_documento_protocollo == "documento":
            # quando in creazione del documento si associa al protocollo il documento_id creato, si mette nel context
            # lo skip della security per evitare che venga generato un errore di security: la security del protocollo
            # eredita quella del documento principale, ma fino a quando non viene settato non sarà permesso l'accesso
            protocollo.with_context(skip_security=True).write({"documento_id": document.id})
        # se invece il document creato è un allegato del protocollo allora si aggiunge il document creato a tutte le acl
        # del protocollo
        if tipologia_documento_protocollo == "allegato":
            for acl in self.env["sd.dms.document.acl"].search([("protocollo_id", "=", protocollo.id)]):
                acl.write({"document_ids": [(4, document.id)]})
        # si replicano i contatti dal documento principale agli allegati
        document._compute_recipient_ids_and_sender_ids()
        # se il protocollo non è stato registrato non devono essere eseguite altre operazioni
        if not protocollo.data_registrazione:
            return document
        # eventuale inserimento della segnatura pdf se il document è il documento principale del protocollo
        if tipologia_documento_protocollo == "documento":
            document.inserisci_segnatura_pdf(raise_exception=False)
        # si impostano eventuali campi del protocollo su cui effettuare un recompute
        protocollo._add_fields_to_recompute()
        return document

    def write(self, vals):
        result = super(Document, self).write(vals)
        for rec in self:
            # si replicano i contatti dal documento principale agli allegati se almeno uno dei seguenti casi è vero:
            # caso 1: il record corrente è il documento principale del protocollo e si stanno modificando i destinatari
            #         o i mittenti
            # caso 2: il record corrente è un allegato del protocollo
            caso1 = rec.id == rec.protocollo_id.documento_id.id and \
                    ("recipient_ids" in vals or "sender_ids" in vals)
            caso2 = rec.id != rec.protocollo_id.documento_id.id and \
                    "protocollo_id" in vals
            if caso1 or caso2:
                # si verifica se devono essere replicati i contatti su altri documenti
                self._compute_recipient_ids_and_sender_ids()
        return result

    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        default["protocollo_id"] = False
        return super(Document, self).copy(default=default)

    def inserisci_segnatura_pdf(self, raise_exception=True):
        for document in self:
            # la segnatura pdf deve essere inserita solo sui document con mimetype application/pdf
            if document.mimetype != "application/pdf":
                continue

            error = None
            file_input_path, file_output_path = None, None
            try:
                protocollo = document.protocollo_id
                if not protocollo:
                    continue

                signature_string = "%s - %s%s - %s - Prot. n. %s del %s%s" % (
                    self._get_codice_ipa_aoo(protocollo),
                    self._get_codice_registro(protocollo),
                    self._get_codice_ufficio(protocollo),
                    self._get_tipologia_protocollo(protocollo),
                    self._get_numero_protocollo(protocollo),
                    self._get_data_protocollo(protocollo),
                    self._get_nome_allegato(protocollo, document.id)
                )

                file_input_name = "%s_%s_%s" % (document.checksum, protocollo.numero_protocollo, "input")
                file_input_path = os.path.join("%stmp" % os.sep, file_input_name)
                file_output_name = "%s_%s_%s" % (document.checksum, protocollo.numero_protocollo, "output")
                file_output_path = os.path.join("%stmp" % os.sep, file_output_name)

                # creazione del file temporaneo su file system: non è detto che lo storage del documento sia impostato
                # per memorizzare il file su file system, di conseguenza, per sicurezza, si legge il content e lo si
                # salva su un file temporaneo e si lavora su quello
                file_input = open(file_input_path, "wb")
                file_input.write(base64.b64decode(document.content))
                file_input.close()

                signature_cmd = os.path.join(get_module_path("sd_protocollo"), "static", "jars", "signature2.jar")
                cmd = [
                    "java",
                    "-jar",
                    signature_cmd,
                    "--input", file_input_path,
                    "--output", file_output_path
                ]
                signature_append_mode = self._get_signature_append_mode()
                if signature_append_mode:
                    cmd.append(signature_append_mode)
                signature_page_mode = self._get_signature_page_mode()
                if signature_page_mode:
                    cmd.append(signature_page_mode)
                cmd.append(signature_string)

                proc = subprocess.Popen(cmd,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        preexec_fn=resource.setrlimit(resource.RLIMIT_AS, (-1, -1)))
                stdoutdata, stderrdata = proc.communicate()
                returncode = proc.wait()
                if returncode != 0:
                    if stdoutdata:
                        _logger.warning(stdoutdata)
                    if stderrdata:
                        _logger.error(stderrdata)
                    error = "PDF Signature Error: %s" % SIGNATURE_RETURN_CODE[returncode]
                    continue

                signed_file = open(file_output_path, 'rb')
                document.write({
                    "content": base64.b64encode(signed_file.read()),
                    "protocollo_segnatura_pdf": True
                })
                signed_file.close()
            except Exception as e:
                error = str(e)
            finally:
                # eliminazione dei file temporanei
                if file_input_path and os.path.exists(file_input_path):
                    os.remove(file_input_path)
                if file_output_path and os.path.exists(file_output_path):
                    os.remove(file_output_path)
                if error:
                    _logger.error(error)
                if error and raise_exception:
                    raise ValidationError(error)

    def _compute_recipient_ids_and_sender_ids(self):
        for rec in self:
            # se il documento non ha un protocollo associato allora non devono essere fatti controlli sui contatti
            if not rec.protocollo_id:
                continue
            # si inizializzano i valori dei destinatari e dei mittenti con cui dovranno essere aggiornati gli allegati
            vals = {
                "recipient_ids": [(6, 0, rec.protocollo_id.documento_id.recipient_ids.ids)],
                "sender_ids": [(6, 0, rec.protocollo_id.documento_id.sender_ids.ids)]
            }
            # se il record è il documento principale del protocollo allora si devono aggiornare tutti gli allegati
            if rec.id == rec.protocollo_id.documento_id.id:
                allegato_list = self.search([
                    ("id", "!=", rec.id),
                    ("protocollo_id", "=", self.protocollo_id.id)
                ])
                allegato_list.write(vals)
            # altrimenti si deve aggiornare solo il record corrente in quanto allegato del protocollo
            else:
                rec.write(vals)

    ####################################################################################################################
    # CONSTRAINTS
    ####################################################################################################################

    @api.constrains("recipient_ids", "sender_ids")
    def _check_recipient_ids_and_sender_ids(self):
        for rec in self:
            # se il documento non ha un protocollo associato allora non devono essere fatti controlli sui contatti
            if not rec.protocollo_id:
                continue
            # se il documento ha un protocollo associato ma è il documento principale del protocollo allora anche in
            # questo caso non devono essere fatti controlli sui contatti
            if rec.protocollo_id.documento_id.id == rec.id:
                continue
            document_recipient_ids = rec.protocollo_id.documento_id.recipient_ids.ids
            attachment_recipeint_ids = rec.recipient_ids.ids
            if set(document_recipient_ids) != set(attachment_recipeint_ids):
                raise ValidationError(_("The document '%s' does not have the same recipients as the main document" % rec.filename))
            document_sender_ids = rec.protocollo_id.documento_id.sender_ids.ids
            attachment_sender_ids = rec.sender_ids.ids
            if set(document_sender_ids) != set(attachment_sender_ids):
                raise ValidationError(_("The document '%s' does not have the same senders as the main document" % rec.filename))

    ####################################################################################################################
    # PRIVATE METHODS
    ####################################################################################################################

    @api.model
    def _get_codice_ipa_aoo(self, protocollo):
        return self._get_codice_ipa(protocollo)

    @api.model
    def _get_codice_ipa(self, protocollo):
        if not protocollo.company_id:
            return ""
        if not protocollo.company_id.codice_ipa:
            return ""
        return protocollo.company_id.codice_ipa

    @api.model
    def _get_codice_registro(self, protocollo):
        return protocollo.registro_id.codice

    @api.model
    def _get_codice_ufficio(self, protocollo):
        return ""

    @api.model
    def _get_tipologia_protocollo(self, protocollo):
        return protocollo.tipologia_protocollo.upper()

    @api.model
    def _get_numero_protocollo(self, protocollo):
        return protocollo.numero_protocollo

    @api.model
    def _get_data_protocollo(self, protocollo):
        # TODO: inserire timezone da configurazione del modulo protocollo
        data_registrazione_it = self.env["fl.utility.dt"].utc_to_local(protocollo.data_registrazione)
        return data_registrazione_it.strftime("%d-%m-%Y")

    @api.model
    def _get_nome_allegato(self, protocollo, documento_id):
        index = False
        allegato_ids = protocollo.allegato_ids.ids
        if documento_id in allegato_ids:
            index = allegato_ids.index(documento_id) + 1
            return " - All. %s" % str(index)
        if not index:
            return ""

    def _check_company_document(self, document):
        res = super(Document, self)._check_company_document(document)
        if not res and document.protocollo_id and document.protocollo_id.company_id:
            if document.protocollo_id.company_id.id != document.company_id.id:
                return "Non è possibile completare l'operazione:\ncontrolla la company del protocollo"
        return res

    def _get_signature_append_mode(self):
        config_obj = self.env["ir.config_parameter"].sudo()
        if bool(config_obj.get_param("sd_protocollo.genera_segnatura_append_solo_pdf_firmati")):
            return "--append-mode-only-signed-pdf"

    def _get_signature_page_mode(self):
        return "--first-page"

    @api.constrains("protocollo_id")
    def _check_unique_protocollo_id(self):
        for rec in self:
            old_protocollo = self.browse(rec.id).protocollo_id
            if old_protocollo:
                if rec.protocollo_id and (rec.protocollo_id.id != old_protocollo.id):
                    raise ValidationError(_("A protocol associated with '%s' already exist" % rec.filename))

