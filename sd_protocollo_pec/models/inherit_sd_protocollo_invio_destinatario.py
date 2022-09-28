from odoo import models, fields

SELECTION_EMAIL_TIPOLOGIA = [
    ("email", "e-mail"),
    ("pec_mail", "PEC e-mail"),
    ("digital_domicile", "Domicilio digitale"),
    ("email_address", "Altro indirizzo e-mail"),
]

SELECTION_DATICERT_TIPO = [
    ("certificato", "Certificato"),
    ("esterno", "Esterno")
]

class InheritSdProtocolloInvioDestinatario(models.Model):
    _inherit = "sd.protocollo.invio.destinatario"

    email = fields.Char(
        string="E-mail",
    )

    email_tipologia = fields.Selection(
        string="Tipologia e-mail",
        selection=SELECTION_EMAIL_TIPOLOGIA
    )

    daticert_tipo = fields.Selection(
        string="Daticert tipo",
        selection=SELECTION_DATICERT_TIPO
    )