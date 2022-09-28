from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class RegistroGiornalieroConfigurazione(models.Model):
    _name = "sd.protocollo.registro.giornaliero.configurazione"
    _description = "Configurazione Registro Giornaliero"
    _rec_name = "nome"

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

    ### CONFIGURAZIONE CREAZIONE PROTOCOLLO ###

    protocollatore_id = fields.Many2one(
        string="Protocollatore",
        comodel_name="res.users",
        required=True
    )

    protocollatore_ufficio_id = fields.Many2one(
        string="Ufficio protocollatore",
        comodel_name="fl.set.set",
        required=True
    )

    registro_id = fields.Many2one(
        string="Registro",
        comodel_name="sd.protocollo.registro",
        domain=[("can_used_to_protocol", "=", True)],
        required=True
    )

    archivio_id = fields.Many2one(
        string="Archivio",
        comodel_name="sd.protocollo.archivio",
        domain=[("can_used_to_protocol", "=", True)],
        required=True
    )

    mittente_interno_id = fields.Many2one(
        string="Mittente",
        comodel_name="fl.set.voce.organigramma",
        domain=[("can_used_to_protocol", "=", True)],
        required=True
    )

    destinatario_id = fields.Many2one(
        string="Destinatario",
        comodel_name="res.partner",
        required=True
    )

    mezzo_trasmissione_id = fields.Many2one(
        string="Mezzo di trasmissione",
        comodel_name="sd.protocollo.mezzo.trasmissione",
        required=True
    )

    oggetto_documento = fields.Text(
        string="Oggetto documento",
        default="Registro Giornaliero",
        required=True
    )

    tipologia_documento = fields.Many2one(
        string="Tipologia documento",
        comodel_name="sd.dms.document.type",
        required=True
    )

    riservato = fields.Boolean(
        string="Riservato",
        default=True
    )

    def _compute_nome(self):
        for rec in self:
            if rec.aoo_id:
                rec.nome = "Configurazione Registro Giornaliero - %s" % rec.company_id.name

    def _get_protocollo_values(self):
        self.ensure_one()
        # Il registro di protocollo verrà protocollato in maniera riservata, in quanto la visibilità
        # dei registri deve essere concessa solamente ad un determinato pool di persone, quindi di
        # conseguenza c'è la necessità di non includere le utenze xl alla creazione/registrazione
        protocollo_vals = {
            "riservato": self.riservato,
            "company_id": self.company_id.id,
            "protocollatore_id": self.protocollatore_id.id,
            "protocollatore_name": self.protocollatore_id.name,
            "protocollatore_ufficio_id": self.protocollatore_ufficio_id.id,
            "mezzo_trasmissione_id": self.mezzo_trasmissione_id.id,
            "mittente_interno_id": self.mittente_interno_id.id,
            "mittente_interno_nome": self.mittente_interno_id.nome,
            "tipologia_protocollo": "uscita",
            "documento_id_oggetto": self.oggetto_documento,
            "registro_id": self.registro_id.id,
            "archivio_id": self.archivio_id.id
        }
        return protocollo_vals
