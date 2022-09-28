from odoo import models, fields


class InvioDestinatario(models.Model):
    _name = "sd.protocollo.invio.destinatario"
    _description = "Destinatario"

    invio_id = fields.Many2one(
        string="Invio",
        comodel_name="sd.protocollo.invio",
        ondelete="cascade",
        required=True
    )

    contatto_id = fields.Many2one(
        string="Nome",
        comodel_name="sd.dms.contact",
        required=True
    )

    contatto_id_name = fields.Char(
        string="Nome",
        related="contatto_id.name"
    )

    invio_precedente_destinatario_id = fields.Many2one(
        string="Destiantario invio precedente",
        comodel_name="sd.protocollo.invio.destinatario"
    )