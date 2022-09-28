# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class FetchmailServerHistory(models.Model):

    _name = "fetchmail.server.history"
    _description = "Fetchmail Server History"
    _order = "create_date DESC"

    fetchmail_server_id = fields.Many2one(
        "fetchmail.server",
        "Server",
        readonly=True
    )

    action = fields.Selection(
        [("fetch", "Fetch")],
        "Action",
        readonly=True
    )

    result = fields.Selection(
        [('success', 'SUCCESS'), ('error', 'ERROR')],
        "Result",
        readonly=True
    )

    error_description = fields.Html(
        "Errors",
        readonly=True
    )

    email_successed_count = fields.Integer(
        "Processed",
        readonly=True
    )

    email_failed_count = fields.Integer(
        "Failed",
        readonly=True
    )

    datetime_start = fields.Datetime(
        "Start",
        readonly=True
    )

    datetime_end = fields.Datetime(
        "End",
        readonly=True
    )