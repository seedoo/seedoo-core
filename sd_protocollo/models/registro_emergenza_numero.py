from odoo import models, fields


class RegistroEmergenzaNumero(models.Model):
    _name = "sd.protocollo.registro.emergenza.numero"
    _description = "Registro Emergenza Numero"

    _rec_name = "numero_protocollo"

    numero_protocollo = fields.Char(
        string="Numero Protocollo",
        required=True
    )

    registro_emergenza_id = fields.Many2one(
        string="Registro Emergenza",
        comodel_name="sd.protocollo.registro.emergenza",
        required=True
    )

    protocollo_id = fields.Many2one(
        string="Protocollo",
        comodel_name="sd.protocollo.protocollo",
        required=True
    )

    emergenza_numero_protocollo = fields.Char(
        string="Emergenza Numero Protocolo",
        related="protocollo_id.emergenza_numero_protocollo"
    )

    emergenza_data_registrazione = fields.Datetime(
        string="Emergenza Numero Protocolo",
        related="protocollo_id.emergenza_data_registrazione"
    )
