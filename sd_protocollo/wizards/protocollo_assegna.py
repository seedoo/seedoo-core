from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

SELECTION_ASSEGNATARIO_TYPE = [
    ("competenza", "Competenza"),
    ("conoscenza", "Conoscenza")
]


class ProtocolloAssegnaStep1(models.TransientModel):
    _name = "sd.protocollo.wizard.protocollo.assegna.step1"
    _description = "Wizard Assegna Step1"

    assegnatore_ufficio_id = fields.Many2one(
        string="Ufficio Assegnatore",
        comodel_name="fl.set.set",
        domain="[('user_ids', '=', uid)]",
        required=True
    )

    assegnatore_ufficio_id_invisible = fields.Boolean(
        string="Ufficio dell'Assegnatore Invisible",
        readonly=True
    )

    assegnazione_ids = fields.One2many(
        string="Assegnatari",
        comodel_name="sd.protocollo.wizard.protocollo.assegna.assegnatari",
        inverse_name="wizard_step1_id",
        readonly=True
    )

    assegnatario_type = fields.Selection(
        string="Tipologia Assegnatario",
        selection=SELECTION_ASSEGNATARIO_TYPE,
    )

    assegnatario_competenza_id = fields.Many2one(
        string="Assegnatario",
        comodel_name="fl.set.voce.organigramma",
        domain=[("can_used_to_protocol", "=", True)],
    )

    assegnatario_conoscenza_id = fields.Many2one(
        string="Assegnatario",
        comodel_name="fl.set.voce.organigramma",
        domain=[("can_used_to_protocol", "=", True)],
    )

    messaggio = fields.Text(
        string="Messaggio",
        default=""
    )

    messaggio_invisible = fields.Boolean(
        string="Messaggio Invisible",
        readonly=True,
        default=False
    )

    riservato = fields.Boolean(
        string="Riservato",
        readonly=True
    )

    assegnatari_non_presenti = fields.Boolean(
        string="Assegnatari non Presenti",
        readonly=True
    )

    assegnatario_type_readonly = fields.Boolean(
        string="Assegnatario type readonly",
        compute="_compute_assegnatario_type_readonly"
    )

    assegnatario_competenza_id_required = fields.Boolean(
        string="assegnatario competenza required",
        compute="_compute_assegnatario_required",
        readonly=True
    )

    assegnatario_conoscenza_id_required = fields.Boolean(
        string="assegnatario conoscenza required",
        compute="_compute_assegnatario_required",
        readonly=True
    )

    button_salva_invisible = fields.Boolean(
        string="button salva visibility",
        readonly=True
    )

    button_salva_e_nuovo_invisible = fields.Boolean(
        string="button salva e nuovo visibility",
        readonly=True
    )

    @api.onchange("assegnatario_type")
    def _compute_assegnatario_required(self):
        self.ensure_one()
        assegnatario_competenza_id_required = False
        assegnatario_conoscenza_id_required = False
        if self.assegnatario_type == "competenza" and not self.assegnazione_ids:
            assegnatario_competenza_id_required = True
        if self.assegnatario_type == "conoscenza" and not self.assegnazione_ids:
            assegnatario_conoscenza_id_required = True
        self.assegnatario_competenza_id_required = assegnatario_competenza_id_required
        self.assegnatario_conoscenza_id_required = assegnatario_conoscenza_id_required

    @api.model
    def default_get(self, fields):
        result = super().default_get(fields)

        if self.env.context.get("tipologia", False) == "aggiunta":
            result = self._default_get_aggiungi(result)
        elif self.env.context.get("tipologia", False) == "aggiunta_conoscenza":
            result = self._default_get_aggiungi_per_conoscenza(result)
        return result

    def _default_get_aggiungi(self, result):
        protocollo_obj = self.env["sd.protocollo.protocollo"]
        assegnazione_obj = self.env["sd.protocollo.assegnazione"]
        protocollo = protocollo_obj.browse(self.env.context.get("protocollo_id"))
        if not protocollo:
            return result
        result = self._get_protocollo_info(result, protocollo)

        competenza_count = assegnazione_obj.search_count(
            [("protocollo_id", "=", protocollo.id), ("tipologia", "=", "competenza")])
        # verifica che non ci siano assegnatari per competenza nei record aggiungi
        if any(x[2]["assegnatario_type"] == "competenza" for x in result["assegnazione_ids"]):
            competenza_count += 1
        result["assegnatario_type"] = "competenza"
        if competenza_count != 0:
            result["assegnatario_type"] = "conoscenza"

        result["button_salva_invisible"] = False
        result["button_salva_e_nuovo_invisible"] = False

        return result

    def _default_get_aggiungi_per_conoscenza(self, result):
        protocollo_obj = self.env["sd.protocollo.protocollo"]
        protocollo = protocollo_obj.browse(self.env.context.get("protocollo_id"))
        if not protocollo:
            return result

        result = self._get_protocollo_info(result, protocollo)
        result["assegnatario_type"] = "conoscenza"
        result["assegnatario_type_readonly"] = True

        result["button_salva_invisible"] = False
        result["button_salva_e_nuovo_invisible"] = False
        return result

    def _get_protocollo_info(self, result, protocollo):
        voce_organigramma_obj = self.env["fl.set.voce.organigramma"]
        assegnazioni = []
        for assegnazione in self.env.context.get("assegnazioni", []):
            assegnazioni.append((0,0,{
                "assegnatario_id":assegnazione[0],
                "assegnatario_type":assegnazione[1],
                "messaggio_assegnatario":assegnazione[2],
            }))
        result["assegnazione_ids"] = assegnazioni

        assegnazione_obj = self.env["sd.protocollo.assegnazione"]
        result["riservato"] = protocollo.riservato
        # ricerca assegnatore disponibile, se non presente sarà possibile l'inserimento da form
        assegnatore_ufficio = assegnazione_obj.get_default_assegnatore_ufficio(protocollo.id)
        result["assegnatore_ufficio_id"] = assegnatore_ufficio if assegnatore_ufficio else False
        result["assegnatore_ufficio_id_invisible"] = True if assegnatore_ufficio else False
        conteggio_voci_organigramma = voce_organigramma_obj.search([], count=True)
        result["assegnatari_non_presenti"] = True if conteggio_voci_organigramma == 0 else False

        if not protocollo.is_stato_tracciamento_storico() or not protocollo.assegnazione_competenza_ids:
            result["messaggio_invisible"] = True
        return result

    @api.depends("assegnazione_ids")
    def _compute_assegnatario_type_readonly(self):
        protocollo_obj = self.env["sd.protocollo.protocollo"]
        protocollo = protocollo_obj.browse(self.env.context.get("protocollo_id"))

        # Wizard aperto in modifica
        if self.env.context.get("tipologia", False) != "aggiunta":
            self.assegnatario_type_readonly = True
            return

        # verifica se presente un assegnatario con competenza in un record precedentemente inserito o nel protocollo
        assegnatario_type_readonly = False
        if protocollo.assegnazione_competenza_ids:
            assegnatario_type_readonly = True
        else:
            for wizard in self.assegnazione_ids:
                if wizard.assegnatario_type == "competenza":
                    assegnatario_type_readonly = True
                    break
        self.assegnatario_type_readonly = assegnatario_type_readonly
        if assegnatario_type_readonly:
            self.assegnatario_type = "conoscenza"

    def action_save_and_new(self):
        self.ensure_one()

        context = self.env.context
        # creazione e aggiunta alla tree del nuovo assegnatario
        assegnatario_id = self.assegnatario_conoscenza_id.id
        if self.assegnatario_type == "competenza":
            assegnatario_id = self.assegnatario_competenza_id.id
        if assegnatario_id:
            self.assegnazione_ids = [(0, 0, {
                "assegnatario_type": self.assegnatario_type,
                "assegnatario_id": assegnatario_id,
                "messaggio_assegnatario": self.messaggio
            })]
            context = dict(
                self.env.context,
                assegnazioni=[(x.assegnatario_id.id, x.assegnatario_type ,x.messaggio_assegnatario) for x in self.assegnazione_ids],
            )
            context = self.disable_assegnatario(context, assegnatario_id)
        return {
            "name": "Aggiungi Assegnatario",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "sd.protocollo.wizard.protocollo.assegna.step1",
            "type": "ir.actions.act_window",
            "target": "new",
            "context": context
        }

    def disable_assegnatario(self,context, assegnatario_id):
        assegnatario_disable_ids = self._get_nodes_to_disable(assegnatario_id)
        config_obj = self.env["ir.config_parameter"].sudo()
        if not bool(config_obj.get_param("sd_protocollo.abilita_assegnazione_stesso_utente_ufficio")):
            context["assegnatario_competenza_disable_ids"].extend(assegnatario_disable_ids)
            context["assegnatario_conoscenza_disable_ids"].extend(assegnatario_disable_ids)
        elif self.assegnatario_type == "competenza":
            context["assegnatario_competenza_disable_ids"].extend(assegnatario_disable_ids)
        elif self.assegnatario_type == "conoscenza":
            context["assegnatario_conoscenza_disable_ids"].extend(assegnatario_disable_ids)
        return context

    def action_save(self):
        self.ensure_one()
        assegnazione_list = []

        assegnatario_id = self.assegnatario_conoscenza_id.id
        if self.assegnatario_type == "competenza":
            assegnatario_id = self.assegnatario_competenza_id.id


        if assegnatario_id:
            self.assegnazione_ids = [(0, 0, {
                "assegnatario_type": self.assegnatario_type,
                "assegnatario_id": assegnatario_id,
                "messaggio_assegnatario": self.messaggio
            })]
        for assegnazione in self.assegnazione_ids:
            assegnazione_list.append((0, 0, {
                "assegnatario_type": assegnazione.assegnatario_type,
                "assegnatario_id": assegnazione.assegnatario_id.id,
                "messaggio_assegnatario": assegnazione.messaggio_assegnatario
            }))
        context = dict(
            self.env.context,
            assegnazioni=[(x.assegnatario_id.id, x.assegnatario_type, x.messaggio_assegnatario) for x in self.assegnazione_ids],
            assegnazione_list=assegnazione_list,
            default_assegnatore_ufficio_id=self.assegnatore_ufficio_id.id,
        )
        context = self.disable_assegnatario(context, assegnatario_id)
        return {
            "name": "Aggiungi Assegnatario",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "sd.protocollo.wizard.protocollo.assegna.step2",
            "type": "ir.actions.act_window",
            "target": "new",
            "context": context
        }

    def _get_nodes_to_disable(self, assegnatario_id):
        voce_organigramma_obj = self.env["fl.set.voce.organigramma"]
        assegnatario = voce_organigramma_obj.browse(assegnatario_id)
        # Se l'assegnatario ha dei figli è un ufficio e andreanno disabilitati i figli
        child = self._get_child_assegnatario(assegnatario)
        if child:
            child.append(assegnatario_id)
            return child
        # Se l'assegnatario ha un parent di conseguenza sarà un figlio e andrà disabilitato l'ufficio padre
        if assegnatario.parent_id:
            return [assegnatario_id, assegnatario.parent_id.id]

        return [assegnatario_id]

    def _get_child_assegnatario(self, assegnatario):
        child_list = []
        for child in assegnatario.child_ids:
            if not child.child_ids:
                child_list.append(child.id)
        return child_list


class ProtocolloAssegnaAssegnatari(models.TransientModel):
    _name = "sd.protocollo.wizard.protocollo.assegna.assegnatari"
    _description = "Wizard protocollo assegna assegnatari"
    _order = "assegnatario_type"

    wizard_step1_id = fields.Many2one(
        string="Wizard Step1",
        comodel_name="sd.protocollo.wizard.protocollo.assegna.step1",
        readonly=True
    )

    wizard_step2_id = fields.Many2one(
        string="Wizard Step2",
        comodel_name="sd.protocollo.wizard.protocollo.assegna.step2",
        readonly=True
    )

    assegnatario_type = fields.Selection(
        string="Tipologia",
        selection=SELECTION_ASSEGNATARIO_TYPE,
        readonly=True
    )

    assegnatario_id = fields.Many2one(
        string="Assegnatario",
        comodel_name="fl.set.voce.organigramma",
        readonly=True
    )

    messaggio_assegnatario = fields.Text(
        string="Messaggio",
        readonly=True
    )


class ProtocolloAssegnaStep2(models.TransientModel):
    _name = "sd.protocollo.wizard.protocollo.assegna.step2"
    _description = "Wizard Assegna Step1"

    assegnatore_ufficio_id = fields.Many2one(
        string="Ufficio dell'Assegnatore",
        comodel_name="fl.set.set",
        domain="[('user_ids', '=', uid)]",
        required=True,
        invisible=True
    )

    assegnazione_ids = fields.One2many(
        string="Assegnatari",
        comodel_name="sd.protocollo.wizard.protocollo.assegna.assegnatari",
        inverse_name="wizard_step2_id",
        readonly=True
    )


    def default_get(self, fields_list):
        res = super(ProtocolloAssegnaStep2, self).default_get(fields_list)
        res["assegnazione_ids"] = self.env.context.get("assegnazione_list", [])
        return res

    def salva_competenza(self, protocollo, assegnatore_id, assegnatore_ufficio_id, assegnazioni):
        assegnatario_competenza_ids = assegnazioni

        old_assegnatario_id = False
        for assegnazione in protocollo.assegnazione_competenza_ids:
            old_assegnatario_id = assegnazione.assegnatario_id.id
        new_assegnatario_id = assegnatario_competenza_ids[
            0].assegnatario_id.id if assegnatario_competenza_ids else False
        messaggio = False
        if assegnatario_competenza_ids and assegnatario_competenza_ids[0].messaggio_assegnatario:
            messaggio = {new_assegnatario_id: assegnatario_competenza_ids[0].messaggio_assegnatario}

        if protocollo.data_registrazione and self.env.context.get("modifica_assegnatari",
                                                                  False) and not assegnatario_competenza_ids:
            raise ValidationError("Per completare l'assegnazione è necessario inserire un assegnatario per Competenza")

        # Se il protocollo è registrato e il nuovo assegnatario coincide con il vecchio, allora gli assegnatari per
        # competenza non devono essere modificati. In pratica un utente con il permesso di modifica assegnatari, sta
        # salvando l'assegnazione senza però cambiarla. Solamente se il nuovo assegnatario è diverso dal vecchio, si
        # devono eliminare tutti i vecchi assegnatari, compresi quelli inseriti tramite lo smistamento
        if protocollo.data_registrazione and \
                old_assegnatario_id and new_assegnatario_id and old_assegnatario_id == new_assegnatario_id:
            return "", ""
        values = {
            "messaggi": messaggio
        }
        if new_assegnatario_id:
            protocollo.salva_assegnazione_competenza(
                [new_assegnatario_id],
                assegnatore_id,
                assegnatore_ufficio_id,
                values=values
            )

    def salva_conoscenza(self, protocollo, assegnatore_id, assegnatore_ufficio_id, assegnazioni):
        assegnatario_conoscenza_to_save_ids = [a.assegnatario_id.id for a in protocollo.assegnazione_conoscenza_ids]
        messaggi = {}
        assegnatari_ids = []
        # Popolamento lista assegnatari e lista messaggi
        for a in assegnazioni:
            assegnatari_ids.append(a.assegnatario_id.id)
            # Aggiunta del messaggio, se presente, in formato {id:messaggio}
            if a.messaggio_assegnatario:
                messaggi.update({a.assegnatario_id.id: a.messaggio_assegnatario})

        # Verifica che non si stia andando a creare un assegnatario già presente nel protocollo
        for wizard in assegnazioni:
            assegnatario = wizard.assegnatario_id
            if assegnatario.tipologia == "ufficio" or (
                    assegnatario.parent_id and assegnatario.parent_id.id not in assegnatari_ids):
                assegnatario_conoscenza_to_save_ids.append(assegnatario.id)
        values = {
            "messaggi": messaggi
        }
        protocollo.salva_assegnazione_conoscenza(
            assegnatario_conoscenza_to_save_ids,
            assegnatore_id,
            assegnatore_ufficio_id,
            values=values
        )

    def _get_assegnazioni_to_save(self, protocollo):
        stato_iniziale_assegnatari = self.env.context.get("stato_iniziale_assegnatari", False)
        if stato_iniziale_assegnatari:
            if stato_iniziale_assegnatari != protocollo.assegnazione_parent_ids.ids:
                error = _(
                    "Non è più possibile eseguire l'operazione richiesta! Il protocollo è già stato assegnato da un altro utente!")
                raise ValidationError(error)

        a_comp_wiz_ids = []
        a_con_wiz_ids = []
        assegnatario_competenza_id = []
        assegnatario_conoscenza_ids = []

        for a in self.assegnazione_ids:
            if a.assegnatario_type == "competenza":
                a_comp_wiz_ids.append(a)
                assegnatario_competenza_id.append(a.assegnatario_id.id)
            elif a.assegnatario_type == "conoscenza":
                a_con_wiz_ids.append(a)
                assegnatario_conoscenza_ids.append(a.assegnatario_id.id)

        return a_comp_wiz_ids, a_con_wiz_ids, assegnatario_competenza_id, assegnatario_conoscenza_ids

    def action_save(self):
        self.ensure_one()
        protocollo_obj = self.env["sd.protocollo.protocollo"]
        protocollo = protocollo_obj.browse(self.env.context.get("protocollo_id"))

        a_comp_wiz_ids, a_con_wiz_ids, assegnatario_competenza_id, assegnatario_conoscenza_ids = self._get_assegnazioni_to_save(
            protocollo)

        if not protocollo.assegnazione_competenza_ids and not a_comp_wiz_ids:
            raise ValidationError("Per completare l'assegnazione è necessario inserire un assegnatario per Competenza")

        self.salva_competenza(protocollo, self.env.uid, self.assegnatore_ufficio_id.id, a_comp_wiz_ids)
        self.salva_conoscenza(protocollo, self.env.uid, self.assegnatore_ufficio_id.id, a_con_wiz_ids)
        protocollo.storico_aggiungi_assegnatario(assegnatario_competenza_id, assegnatario_conoscenza_ids, "")

    def action_torna_indietro(self):
        self.ensure_one()
        context = dict(
            self.env.context,
        )
        return {
            "name": "Aggiungi Assegnatario",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "sd.protocollo.wizard.protocollo.assegna.step1",
            "type": "ir.actions.act_window",
            "target": "new",
            "context": context
        }

