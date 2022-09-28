# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class MailMail(models.Model):
    _inherit = "mail.mail"

    pec = fields.Boolean(
        string="PEC",
    )

    pec_type = fields.Selection([
        ("posta-certificata", "Pec Mail"),
        ("errore", "Pec Mail Anomaly"),
        ("accettazione", "Reception"),
        ("non-accettazione", "No Reception"),
        ("presa-in-carico", "In Progress"),
        ("avvenuta-consegna", "Delivery"),
        ("errore-consegna", "Delivery Error"),
        ("preavviso-errore-consegna", "Notice Delivery Error"),
        ("rilevazione-virus", "Virus Detected"),
    ],
        string="Pec Type",
        readonly=True
    )

    error = fields.Boolean(
        string="Reception Delivery Error",
        default=False
    )

    err_type = fields.Selection([
        ("nessuno", "No Error"),
        ("no-dest", "Recipient Adress Error"),
        ("no-dominio", "Recipient domain Error"),
        ("virus", "Virus Detected Error"),
        ("altro", "Undefined Error"),
    ], "Pec Error Type", readonly=True)

    cert_datetime = fields.Datetime(
        string="Certified Datetime",
        readonly=True
    )

    recipient_addr = fields.Char(
        string="Recipient Address",
        readonly=True
    )

    pec_msg_id = fields.Char(
        string="PEC Message Id",
        readonly=True
    )

    pec_mail_parent_id = fields.Many2one(
        "mail.mail",
        string="Parent PEC Mail",
        readonly=True
    )

    pec_mail_child_ids = fields.One2many(
        "mail.mail",
        "pec_mail_parent_id",
        string="Related Notifications",
        readonly=True
    )

    resized_subject = fields.Char(
        string="Resized Subject",
        compute="_compute_resized_subject"
    )

    pec_mail_child_count = fields.Integer(
        string="Related Notifications",
        compute="_compute_pec_mail_child_count"
    )

    @api.model
    def create(self, vals):
        if self._context.get("mail_compose_message", False) and vals:
            vals["pec"] = self._context.get("pec", False)
            vals["pec_type"] = self._context.get("pec_type", False)
        mail = super(MailMail, self).create(vals)
        return mail

    def _compute_resized_subject(self):
        for rec in self:
            resized_subject = rec.subject
            if len(rec.subject) > 80:
                subject = rec.subject.split()
                list = []
                char_cout = 0
                for word in subject:
                    if char_cout < 90:
                        char_cout += len(word)
                        list.append(word)
                        continue
                    break
                str_subject = " ".join(list)
                resized_subject = str_subject + " ..." if len(list) != len(subject) else str_subject
            rec.resized_subject = resized_subject

    def _compute_pec_mail_child_count(self):
        for rec in self:
            rec.pec_mail_child_count = self.search([
                ("pec_mail_parent_id", "=", self.id)
            ], count=True)