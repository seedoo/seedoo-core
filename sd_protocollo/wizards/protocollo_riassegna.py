from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class ProtocolloRiassegna(models.TransientModel):
    _name = "sd.protocollo.wizard.protocollo.riassegna"
    _description = "Wizard Riassegna"

    assegnatore_ufficio_id = fields.Many2one(
        string="Ufficio dell'Assegnatore",
        comodel_name="fl.set.set",
        domain="[('user_ids', '=', uid)]",
        required=True
    )

    assegnatario_competenza_id = fields.Many2one(
        string="Nuovo Assegnatario",
        comodel_name="fl.set.voce.organigramma",
        domain=[("can_used_to_protocol", "=", True)],
        required=True
    )

    assegnazione_competenza_id = fields.Many2one(
        string="Assegnazione Rifiutata",
        comodel_name="sd.protocollo.assegnazione",
        readonly=True
    )

    assegnazione_competenza_name = fields.Char(
        string="Vecchio Assegnatario",
        readonly=True
    )

    messaggio = fields.Text(
        string="Messaggio",
        default=""
    )

    assegnatari_non_presenti = fields.Boolean(
        string="Assegnatari non Presenti",
        readonly=True
    )

    assegnatore_ufficio_id_invisible = fields.Boolean(
        string="Ufficio dell'Assegnatore Invisible",
        readonly=True
    )

    @api.model
    def default_get(self, fields):
        result = super(ProtocolloRiassegna, self).default_get(fields)

        protocollo_obj = self.env["sd.protocollo.protocollo"]
        assegnazione_obj = self.env["sd.protocollo.assegnazione"]
        voce_organigramma_obj = self.env["fl.set.voce.organigramma"]
        protocollo = protocollo_obj.browse(self.env.context.get("protocollo_id"))
        if not protocollo:
            return result

        uid = self.env.uid
        # si recupera l'assegnazione per competenza rifiutata di cui l'utente corrente è l'assegnatore
        assegnazione_rifiutata_ids = protocollo.get_assegnazione_assegnatore_ids("competenza", "rifiutato", uid)
        assegnazione_rifiutata = assegnazione_obj.browse(assegnazione_rifiutata_ids[0])
        result["assegnazione_competenza_id"] = assegnazione_rifiutata.id
        result["assegnazione_competenza_name"] = assegnazione_rifiutata.assegnatario_id.path_name
        # l'ufficio dell'assegnatore deve essere lo stesso dell'assegnazione rifiutata
        result["assegnatore_ufficio_id"] = assegnazione_rifiutata.assegnatore_parent_id.id
        # nella monocompetenza l'ufficio dell'assegnatore è sempre invisibile perchè ci potrà essere sempre una sola
        # assegnazione per competenza rifiutata alla volta
        result["assegnatore_ufficio_id_invisible"] = True

        # l'assegnatario per competenza non deve essere preselezionato
        result["assegnatario_competenza_id"] = False

        conteggio_voci_organigramma = voce_organigramma_obj.search([], count=True)
        result["assegnatari_non_presenti"] = True if conteggio_voci_organigramma == 0 else False
        return result

    @api.onchange("assegnatario_competenza_id")
    def on_change_assegnatario_competenza_id(self):
        data = {}
        protocollo_obj = self.env["sd.protocollo.protocollo"]
        assegnazione_obj = self.env["sd.protocollo.assegnazione"]
        protocollo = protocollo_obj.browse(self.env.context.get("protocollo_id"))
        if not protocollo:
            return data
        uid = self.env.uid
        assegnazione_rifiutata_ids = protocollo.get_assegnazione_assegnatore_ids("competenza", "rifiutato", uid)
        assegnazione_rifiutata = assegnazione_obj.browse(assegnazione_rifiutata_ids[0])
        if assegnazione_rifiutata.assegnatario_id.id == self.assegnatario_competenza_id.id:
            data = {
                "warning": {
                    "title": "Attenzione",
                    "message": "Hai selezionato lo stesso Assegnatario per Competenza che ha rifiutato l'assegnazione!"
                }
            }
        return data

    def salva_competenza(self, protocollo, assegnatore_id, assegnatore_ufficio_id):
        old_assegnatario_ids = [a.assegnatario_id.id for a in self.assegnazione_competenza_id]
        new_assegnatario_id = self.assegnatario_competenza_id.id if self.assegnatario_competenza_id else False
        protocollo.salva_assegnazione_competenza(
            [new_assegnatario_id] if new_assegnatario_id else [],
            assegnatore_id,
            assegnatore_ufficio_id,
            old_assegnatario_ids,
            values={"messaggi": {new_assegnatario_id: self.messaggio}}
        )

    def action_riassegna(self):
        self.ensure_one()
        protocollo_obj = self.env["sd.protocollo.protocollo"]
        protocollo = protocollo_obj.browse(self.env.context.get("protocollo_id"))
        old_assegnatario_id = self.assegnazione_competenza_id.assegnatario_id.id

        stato_iniziale_assegnatari = self.env.context.get("stato_iniziale_assegnatari", False)
        if stato_iniziale_assegnatari:
            if stato_iniziale_assegnatari != protocollo.assegnazione_parent_ids.ids:
                error = _("Non è più possibile eseguire l'operazione richiesta!")
                raise ValidationError(error)

        self.salva_competenza(protocollo, self.env.uid, self.assegnatore_ufficio_id.id)
        protocollo.storico_riassegna(old_assegnatario_id, self.assegnatario_competenza_id.id)