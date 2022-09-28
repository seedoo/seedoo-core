from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class Protocollo(models.Model):
    _inherit = "sd.protocollo.protocollo"

    account_id = fields.Many2one(
        string="Account",
        comodel_name="fl.mail.client.account"
    )

    mail_id = fields.Many2one(
        string="Mail",
        comodel_name="mail.mail",
        readonly=True
    )

    da_gestire_invio = fields.Boolean(
        string="Invio da gestire",
        compute="_compute_da_gestire_invio",
        store=True
    )

    in_uscita_invio = fields.Boolean(
        string="Invio in uscita",
        compute="_compute_in_uscita_invio",
        store=True
    )

    @api.depends("invio_ids.da_reinviare", "invio_ids.da_resettare", "invio_ids", "invio_ids.state")
    def _compute_da_gestire_invio(self):
        invio_ids = self.env["sd.protocollo.invio"].search_read([
            ("protocollo_id", "in", self.ids),
            ("mezzo_trasmissione_integrazione", "=", "pec"), ("invio_successivo_ids", "=", False),
            '|', ("da_resettare", "=", True), '&', ("state", "=", 'exception'), ('invio_successivo_ids', '=', False)
        ], ["id"], limit=len(self.ids))
        invio_ids = [x["id"] for x in invio_ids]
        for rec in self:
            invio_da_gestire = False
            if any(x.id in invio_ids for x in rec.invio_ids):
                invio_da_gestire = True
            rec.da_gestire_invio = invio_da_gestire

    @api.depends("invio_ids", "invio_ids.state")
    def _compute_in_uscita_invio(self):
        invio_ids = self.env["sd.protocollo.invio"].search_read([
            ("protocollo_id", "in", self.ids),
            ("state", "=", "outgoing")
        ], ["id"], limit=len(self.ids))
        invio_ids = [x["id"] for x in invio_ids]
        for rec in self:
            in_uscita_invio = False
            if any(x.id in invio_ids for x in rec.invio_ids):
                in_uscita_invio = True
            rec.in_uscita_invio = in_uscita_invio

    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        if self.mail_id:
            raise ValidationError(_("You can't copy protocol with source mail!"))
        return super(Protocollo, self).copy(default=default)

    def _compute_data_ricezione_readonly(self):
        super(Protocollo, self)._compute_data_ricezione_readonly()
        for protocollo in self:
        # - caso 4: Il protocollo è stato creato da una mail o pec con preimpostata la relativa data di ricezione
            if protocollo.mail_id and protocollo.data_ricezione:
                protocollo.data_ricezione_readonly = True

    def _compute_mezzo_trasmissione_id_readonly(self):
        super(Protocollo, self)._compute_mezzo_trasmissione_id_readonly()
        for protocollo in self:
            # - caso 5: il protocollo è in bozza ma è stato creato da una mail
            caso5 = protocollo.state == "bozza" and protocollo.mail_id
            protocollo.mezzo_trasmissione_id_readonly = protocollo.mezzo_trasmissione_id_readonly or caso5

    def _compute_documento_id_content_readonly(self):
        super(Protocollo, self)._compute_documento_id_content_readonly()
        config = bool(self.env["ir.config_parameter"].sudo().get_param("sd_protocollo.modifica_documenti_pec"))
        for protocollo in self:
            # il content di un documento di un protocollo deve essere in sola lettura anche in un terzo caso:
            # - caso 3: protocollo in bozza, il campo mail_id è popolato e il parametro modifica_documenti_pec è false
            caso3 = protocollo.state == "bozza" and protocollo.mail_id and not config
            protocollo.documento_id_content_readonly = protocollo.documento_id_content_readonly or caso3

    @api.onchange("tipologia_protocollo")
    def _onchange_tipologia_protocollo(self):
        super(Protocollo, self)._onchange_tipologia_protocollo()
        fields_list = []
        if self.tipologia_protocollo == "ingresso":
            fields_list = ["mittente_interno_id", "destinatario_ids"]
            integrazione_values = self.env["sd.protocollo.mezzo.trasmissione"].get_integrazione_values()
            if self.mezzo_trasmissione_id.integrazione in integrazione_values:
                self.mezzo_trasmissione_id = False
        for field in fields_list:
            self[field] = False

    @api.depends("data_registrazione", "invio_ids.da_inviare")
    def _compute_da_inviare(self):
        super(Protocollo, self)._compute_da_inviare()
        for protocollo in self:
            if protocollo.data_registrazione and protocollo.tipologia_protocollo == "uscita" and protocollo.invio_ids:
                for invio in protocollo.invio_ids:
                    if invio.da_inviare:
                        protocollo.da_inviare = True
                        break

    def _compute_source_count(self):
        super(Protocollo, self)._compute_source_count()
        for protocollo in self:
            if protocollo.mail_id:
                protocollo.source_count = 1