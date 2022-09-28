from odoo import models, fields


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    message_ids = fields.Many2many(
        string="Messages",
        comodel_name="mail.message",
        relation="message_attachment_rel",
        column1="attachment_id",
        column2="message_id",
        readonly=True
    )