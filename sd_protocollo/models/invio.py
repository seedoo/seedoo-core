from odoo import models, fields, api
import datetime

SELECTION_STATE = [
    ("outgoing", "In Uscita"),
    ("sent", "Inviato"),
    ("accepted", "Accettato"),
    ("received", "Ricevuto"),
    ("exception", "Errore"),
    ("cancel", "Cancellato")
]


class Invio(models.Model):
    _name = "sd.protocollo.invio"
    _description = "Invio"
    _order = 'id desc'

    protocollo_id = fields.Many2one(
        string="Protocollo",
        comodel_name="sd.protocollo.protocollo",
        ondelete="cascade",
        required=True
    )

    mezzo_trasmissione_id = fields.Many2one(
        string="Mezzo di Trasmissione",
        comodel_name="sd.protocollo.mezzo.trasmissione"
    )

    mezzo_trasmissione_nome = fields.Char(
        string="Nome Mezzo Trasmissione",
    )

    data_invio = fields.Datetime(
        string="Data Invio",
    )

    destinatario_ids = fields.One2many(
        string="Destinatari",
        comodel_name="sd.protocollo.invio.destinatario",
        inverse_name="invio_id"
    )

    state = fields.Selection(
        string="State",
        selection=SELECTION_STATE,
        compute="compute_state",
        store=True
    )

    invio_precedente_ids = fields.Many2many(
        string="Invio Precedente",
        comodel_name="sd.protocollo.invio",
        relation="sd_protocollo_invio_rel",
        column1="invio_successivo_id",
        column2="invio_precedente_id"
    )

    invio_successivo_ids = fields.Many2many(
        string="Invio Successivo",
        comodel_name="sd.protocollo.invio",
        relation="sd_protocollo_invio_rel",
        column1="invio_precedente_id",
        column2="invio_successivo_id"
    )

    def compute_state(self):
        for rec in self:
            rec.state = "sent"

    @api.model
    def crea_invio_analogico(self, protocollo_id, mezzo_trasmissione_id, contatto_ids):
        invio_obj = self.env["sd.protocollo.invio"]
        mezzo_obj = self.env["sd.protocollo.mezzo.trasmissione"]
        mezzo_trasmissione_nome = mezzo_obj.browse(mezzo_trasmissione_id).nome
        for contatto_id in contatto_ids:
            invio_obj.create({
                "protocollo_id": protocollo_id,
                "mezzo_trasmissione_id": mezzo_trasmissione_id,
                "mezzo_trasmissione_nome": mezzo_trasmissione_nome,
                "data_invio": datetime.datetime.now(),
                "destinatario_ids": [(0, 0, {"contatto_id": contatto_id})],
                "state": "sent"
            })
