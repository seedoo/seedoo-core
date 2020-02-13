# -*- coding: utf-8 -*-
import base64
import datetime
import logging
import time

from openerp import models, fields, api
from openerp.exceptions import ValidationError
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT

_logger = logging.getLogger(__name__)

SELECTION_STATE = [
    ("draft", "Aperto"),
    ("closed", "Chiuso")
]


class ProtocolloJournal(models.Model):
    _name = "protocollo.journal"
    _description = "Registro Giornaliero"
    _order = "date DESC"

    name = fields.Date(
        string="Data evento",
        required=True,
        readonly=True,
        compute="_compute_name",
        store=True
    )

    display_name = fields.Char(
        string="Nome Registro",
        readonly=True,
        compute="_compute_name",
        store=True
    )

    date = fields.Date(
        string="Data Registro",
        required=True,
        default=fields.Date.today(),
        readonly=True
    )

    user_id = fields.Many2one(
        string="Autore Registro",
        comodel_name="res.users",
        required=False,

        readonly=True
    )

    protocol_ids = fields.Many2many(
        string="Protocollazioni della Giornata",
        comodel_name="protocollo.protocollo",
        relation="protocollo_journal_rel",
        column1="journal_id",
        column2="protocollo_id",
        required=False,
        readonly=True,
        compute="_compute_protocol_ids"
    )

    state = fields.Selection(
        string="Stato",
        help="Stato del registro",
        selection=SELECTION_STATE,
        required=False,
        default="draft",
        readonly=True
    )

    aoo_id = fields.Many2one(
        string="AOO",
        comodel_name="protocollo.aoo",
        ondelete="cascade",
        required=True
    )

    ts_chiusura = fields.Datetime(
        string="Data ed ora chiusura",
        help="Data ed ora di chiusura del registro",
        readonly=True
    )

    @api.depends("date")
    @api.multi
    def _compute_name(self):
        for rec in self:
            rec.name = rec.date
            rec.display_name = "Registro Giornaliero del %s" % rec.date

    @api.depends("aoo_id", "date")
    @api.multi
    def _compute_protocol_ids(self):
        for rec in self:
            protocollo_ids = self.get_protocolli_day(rec.aoo_id, rec.date)
            rec.protocol_ids = [(6, 0, protocollo_ids.ids)]

    @api.multi
    def action_close(self):
        ir_attachment_obj = self.env["ir.attachment"]

        for rec in self:
            name = "%s.pdf" % rec.display_name
            ir_attachment_obj.create({
                "name": name,
                "datas_fname": name,
                "res_model": rec._name,
                "res_id": rec.id,
                "datas": base64.b64encode(rec.render_pdf()),
                "file_type": "application/json"
            })

            rec.write({
                "state": "closed",
                "ts_chiusura": fields.Datetime.now()
            })

    @api.multi
    def action_print(self):
        self.ensure_one()

        return {
            "type": "ir.actions.act_url",
            "url": "/seedoo_protocollo/journal/pdf/%d" % self.id,
            "target": "new"
        }

    @api.multi
    def render_pdf(self):
        self.ensure_one()

        report_obj = self.env["report"]
        pdf_content = report_obj.get_pdf(self, "seedoo_protocollo.journal_qweb")
        return pdf_content

    @api.model
    def cron_generate_missing(self):
        aoo_obj = self.env["protocollo.aoo"]

        aoo_ids = aoo_obj.search([])

        for aoo_id in aoo_ids:
            self.generate_missing_aoo(aoo_id)

        return True

    @api.model
    def generate_missing_aoo(self, aoo_id):
        journal_obj = self.env["protocollo.journal"]

        last_journal_id = journal_obj.search(
            args=[
                ("aoo_id", "=", aoo_id.id),
                ("state", "in", self.get_closed_states()),
                ("date", "<", time.strftime(DEFAULT_SERVER_DATE_FORMAT))
            ],
            order="date DESC",
            limit=1
        )

        date_list = []

        if last_journal_id:
            today = datetime.datetime.now()
            last_journal_date = datetime.datetime.strptime(last_journal_id.date, DEFAULT_SERVER_DATE_FORMAT)
            num_days = (today - last_journal_date).days
            if num_days in (0, 1):
                return

            for day in range(1, num_days):
                last_date = (last_journal_date + datetime.timedelta(days=day))
                date_list.append(last_date)

        else:
            today = datetime.datetime.now()
            yesterday = today + datetime.timedelta(days=-1)
            date_list.append(yesterday)

        for date_day in date_list:
            try:
                journal_id = self.journal_create(aoo_id, date_day)
                journal_id.action_close()
            except Exception as e:
                _logger.error("Error creating journal via cron: %s" % e)

    @api.model
    def get_closed_states(self):
        return ["closed"]

    @api.model
    def journal_create(self, aoo_id, day_date):
        journal_obj = self.env["protocollo.journal"]

        _logger.info("Creating journal for %s - %s" % (aoo_id.name, day_date))

        journal_id = journal_obj.search([
            ("date", "=", day_date),
            ("aoo_id", "=", aoo_id.id)
        ])

        if journal_id:
            raise ValidationError("Registro già esistente per la data selezionata")

        try:
            journal_id = journal_obj.create({
                "name": day_date,
                "date": day_date,
                "user_id": self.env.user.id,
                "aoo_id": aoo_id.id,
            })
        except Exception as e:
            _logger.error(e)
            raise ValidationError("Impossibile creare il Registro di Protocollo per la data %s" % day_date)

        return journal_id

    @api.model
    def get_protocolli_day(self, aoo_id, day_date):
        protocollo_obj = self.env["protocollo.protocollo"]

        protocollo_ids = protocollo_obj.search([
            ("aoo_id", "=", aoo_id.id),
            ("state", "in", ["registered", "notified", "sent", "waiting", "error", "canceled"]),
            ("registration_date", ">", day_date + " 00:00:00"),
            ("registration_date", "<", day_date + " 23:59:59"),
        ])

        return protocollo_ids
