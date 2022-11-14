import base64
import datetime
import logging
import time

from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, UserError
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

SELECTION_STATE = [
    ("aperto", "Aperto"),
    ("chiuso", "Chiuso"),
    ("protocollato", "Protocollato")
]


class RegistroGiornaliero(models.Model):
    _name = "sd.protocollo.registro.giornaliero"
    _description = "Registro Giornaliero"
    _rec_name = "nome"
    _order = "data DESC"

    nome = fields.Char(
        string="Nome",
        compute="_compute_nome",
        store=True,
        readonly=True
    )

    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        required=True,
        default=lambda self: self.env.company.id
    )

    state = fields.Selection(
        string="Stato",
        selection=SELECTION_STATE,
        default=SELECTION_STATE[0][0],
        readonly=True
    )

    data = fields.Date(
        string="Data",
        required=True
    )

    autore_id = fields.Many2one(
        string="Autore",
        comodel_name="res.users",
        readonly=True,
        default=lambda self: self.env.user
    )

    data_chiusura = fields.Datetime(
        string="Data ed Ora Chiusura",
        readonly=True
    )

    protocollo_id = fields.Many2one(
        string="Protocollo",
        comodel_name="sd.protocollo.protocollo",
        readonly=True
    )

    protocollo_ids = fields.One2many(
        string="Protocolli",
        comodel_name="sd.protocollo.protocollo",
        inverse_name="registro_giornaliero_id",
        readonly=True
    )

    protocollo_count = fields.Integer(
        "# Protocollo",
        compute="_compute_protocollo_count",
    )

    documento_id = fields.Many2one(
        string="Documento",
        comodel_name="sd.dms.document",
        readonly=True
    )

    documento_id_content = fields.Binary(
        string="File",
        related="documento_id.content",
        readonly=True
    )

    documento_id_filename = fields.Char(
        string="Nome File",
        related="documento_id.filename",
        readonly=True
    )

    field_readonly = fields.Boolean(
        string="Field Invisible",
        compute="compute_field_readonly",
        readonly=True
    )

    _sql_constraints = [
        (
            "unique",
            "UNIQUE(data, company_id)",
            "Esiste già un registro per la stessa data"
        )
    ]

    @api.depends("protocollo_ids")
    def _compute_protocollo_count(self):
        for rec in self:
            rec.protocollo_count = len(rec.protocollo_ids.ids)

    def get_protocollo_domain(self):
        self.ensure_one()
        domain = [
            ("company_id", "=", self.company_id.id),
        ]
        return domain

    @api.depends("data")
    @api.onchange("data")
    def _compute_nome(self):
        for rec in self:
            if rec.data:
                rec.nome = "Registro Giornaliero del %s" % rec.data.strftime('%d-%m-%Y')
            else:
                rec.nome = "Registro Giornaliero"

    def action_stampa(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "url": "/seedoo_protocollo/registro_giornaliero/pdf/%d" % self.id,
            "target": "new"
        }

    @api.depends("state")
    def compute_field_readonly(self):
        for rec in self:
            field_readonly = True
            if rec.state == "aperto":
                field_readonly = False
            rec.field_readonly = field_readonly

    def render_pdf(self, registro_giornaliero):
        report_registro_giornaliero = self.env.ref("sd_protocollo.report_sd_protocollo_registro_giornaliero_qweb")
        registro_giornaliero_data = report_registro_giornaliero.sudo()._render_qweb_pdf([registro_giornaliero])[0]
        return registro_giornaliero_data

    def action_chiudi(self):
        documento_obj = self.env["sd.dms.document"]
        for rec in self:
            folder = self.env["sd.protocollo.cartella"].get_folder(rec, "registro_giornaliero")
            if not folder:
                raise ValidationError("La cartella per il salvataggio dei registri giornalieri non è configurata")
            data_pdf = self.render_pdf(rec.id)
            name = "%s.pdf" % rec.nome
            documento = documento_obj.create({
                "filename": name,
                "content": base64.b64encode(data_pdf),
                "folder_id": folder.id,
                "document_type_id": self.env.ref("sd_protocollo.data_sd_dms_document_type_rgp").id,
                "producer": "Metafora"
            })
            rec.write({
                "state": "chiuso",
                "documento_id": documento.id,
                "data_chiusura": fields.Datetime.now()
            })
            rec.protocolla_registro_giornaliero(documento)

    @api.model
    def get_state_chiusi(self):
        return ["chiuso"]

    @api.model
    def genera_registri_mancanti(self):
        registro_obj = self.env["sd.protocollo.registro"]
        company_list = self.env["res.company"].search([])
        for company in company_list:
            if registro_obj.search([("ufficiale", "=", True), ("company_id", "=", company.id)], count=True) == 0:
                continue
            kwargs = {"company_id": company.id}
            self.crea_registro_giornaliero(**kwargs)
        return True

    @api.model
    def crea_registro_giornaliero(self, **kwargs):
        domain = []
        for kwarg in kwargs:
            domain.append((kwarg, "=", kwargs[kwarg]))
        domain += [
            #("state", "in", self.get_state_chiusi()),
            ("data", "<", time.strftime(DEFAULT_SERVER_DATE_FORMAT))
        ]
        registro_giornaliero = self.search(domain, order="data DESC", limit=1)
        date_list = []
        if registro_giornaliero:
            today = datetime.datetime.now()
            registro_giornaliero_data = datetime.datetime.strptime(str(registro_giornaliero.data),
                                                                   DEFAULT_SERVER_DATE_FORMAT)
            num_days = (today - registro_giornaliero_data).days
            if num_days in (0, 1):
                return
            for day in range(1, num_days):
                last_date = (registro_giornaliero_data + datetime.timedelta(days=day))
                date_list.append(last_date)
        else:
            today = datetime.datetime.now()
            yesterday = today + datetime.timedelta(days=-1)
            date_list.append(yesterday)
        for date_day in date_list:
            try:
                _logger.debug("Creazione registro giornaliero con valori: %s" % str(kwargs))
                kwargs["data"] = date_day
                vals = kwargs
                vals["autore_id"] = self.env.user.id
                registro_giornaliero = self.create(vals)
                self.env.cr.commit()
                registro_giornaliero.action_chiudi()
                self.env.cr.commit()
            except Exception as e:
                _logger.error(e)
                self.env.cr.rollback()
                continue

    @api.model
    def protocolla_registro_giornaliero(self, documento):
        self.ensure_one()
        registro_configurazione_obj = self.env["sd.protocollo.registro.giornaliero.configurazione"]
        protocollo_obj = self.env["sd.protocollo.protocollo"]
        contact_obj = self.env["sd.dms.contact"]

        config = registro_configurazione_obj.search(self._get_domain_configurazione_registro_giornaliero())
        if not config:
            return

        contact_values = contact_obj.get_values_partner_contact(config.destinatario_id)
        destinatario_id = contact_obj.create(contact_values).id
        documento.recipient_ids = [(6, 0, [destinatario_id])]

        protocollo_vals = config._get_protocollo_values()
        protocollo_vals.update({
            "documento_id": documento.id,
            "documento_id_cartella_id": documento.folder_id.id
        })
        try:
            protocollo = protocollo_obj.with_context(cron_company_id=config.company_id.id).create(protocollo_vals)
            protocollo.registra()
            protocollo.protocollatore_stato = "lavorazione_completata"
            self.protocollo_id = protocollo.id
            self.state = "protocollato"
        except Exception as e:
            _logger.info(e)

    def _get_domain_configurazione_registro_giornaliero(self):
        return [("company_id", "=", self.company_id.id)]

    @api.model
    def create(self, vals):
        rec = super(RegistroGiornaliero, self).create(vals)
        protocollo_obj = self.env["sd.protocollo.protocollo"]
        # conversione della data selezionata per la ricerca dei protocolli in quanto la data di registrazione
        # del protocollo è salvata in utc e a noi interessa sapere tutti i protocolli registrati in data locale
        # il risultato per Europe/Rome da UTC è UTC+1h es:
        # (data in utc) 01-01-2021 00:00:00 - 23:59:59
        # (data in Europe/Rome) 01-01-2021 01:00:00 - 02-01-2021 00:59:59
        selected_start_date = datetime.datetime(rec.data.year, rec.data.month, rec.data.day)
        selected_end_date = selected_start_date.replace(hour=23, minute=59, second=59)
        selected_start_date = str(protocollo_obj._get_local_date(selected_start_date))
        selected_end_date = str(protocollo_obj._get_local_date(selected_end_date))
        domain = rec.get_protocollo_domain()
        domain += [
            ("state", "in", ["registrato", "annullato"]),
            ("data_registrazione", ">", selected_start_date),
            ("data_registrazione", "<", selected_end_date),
        ]
        protocollo_list = protocollo_obj.sudo().search(domain)
        protocollo_list.sudo().write({"registro_giornaliero_id": rec.id})
        return rec

    def unlink(self):
        document_list = []
        for rec in self:
            if rec.documento_id:
                document_list.append(rec.documento_id)
        result = super(RegistroGiornaliero, self).unlink()
        for document in document_list:
            document.sudo().unlink()
        return result

    def action_show_protocollo_ids(self):
        self.ensure_one()
        return {
            "name": "Protocolli",
            "view_mode": "tree,form",
            "res_model": "sd.protocollo.protocollo",
            "type": "ir.actions.act_window",
            "target": "current",
            "context": {
                "search_default_registro_giornaliero_id": self.id
            },
        }