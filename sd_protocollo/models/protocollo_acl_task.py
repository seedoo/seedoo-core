from odoo import models, fields
from .sd_dms_document_acl import SELECTION_PROTOCOLLO_VISIBILITY

SELECTION_STATE = [
    ("in_attesa", "In Attesa"),
    ("in_esecuzione", "In Esecuzione"),
    ("errore", "Errore")
]

SELECTION_TIPOLOGIA = [
    ("intervallo_protocollo", "Intervallo Protocollo"),
    ("istanza_protocollo", "Istanza Protocollo")
]


class ProtocolloAclTask(models.Model):

    _name = "sd.protocollo.protocollo.acl.task"
    _description = "Protocollo Acl Task"

    state = fields.Selection(
        string="Stato",
        selection=SELECTION_STATE,
        default=SELECTION_STATE[0][0],
        required=True
    )

    tipologia = fields.Selection(
        string="Stato",
        selection=SELECTION_STATE,
        default=SELECTION_STATE[0][0],
        required=True
    )

    istanza_protocollo_id = fields.Many2one(
        string="Istanza Protocollo",
        comodel_name="sd.protocollo.protocollo",
        ondelete="cascade"
    )

    intervallo_protocollo_inizio_id = fields.Many2one(
        string="Intervallo Protocollo Inizio",
        comodel_name="sd.protocollo.protocollo",
        ondelete="cascade"
    )

    intervallo_protocollo_fine_id = fields.Many2one(
        string="Intervallo Protocollo Inizio",
        comodel_name="sd.protocollo.protocollo",
        ondelete="cascade"
    )

    visibilita = fields.Selection(
        string="Visibilità",
        selection=SELECTION_PROTOCOLLO_VISIBILITY
    )

    user_id = fields.Many2one(
        string="Utente",
        comodel_name="res.users",
        ondelete="cascade"
    )