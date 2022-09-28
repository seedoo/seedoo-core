from odoo import fields, models, api


class VoceOrganigramma(models.Model):
    _inherit = "fl.set.voce.organigramma"

    can_used_to_protocol = fields.Boolean(
        string="Can Used To Protocol",
        compute="_compute_can_used_to_protocol",
        search="_search_can_used_to_protocol"
    )

    @api.model
    def get_domain_can_used_to_protocol(self):
        field_dict = self.get_domain_from_protocol()
        domain_utente = self.get_domain_utente(field_dict)
        domain_ufficio = self.get_domain_ufficio(field_dict)
        domain = ["|"] + domain_utente + domain_ufficio
        return domain

    @api.model
    def get_domain_from_protocol(self):
        protocollo_id = self.env.context.get("protocollo_id", False)
        if not protocollo_id:
            return False
        protocollo_obj = self.env["sd.protocollo.protocollo"]
        field_list = protocollo_obj.search_read([("id", "=", protocollo_id)], self.get_protocollo_fields())
        if field_list:
            return field_list[0]
        return False

    @api.model
    def get_protocollo_fields(self):
        return ["company_id"]

    @api.model
    def get_ids_can_used_to_protocol(self):
        ids = self.search(self.get_domain_can_used_to_protocol()).ids
        return ids

    def _compute_can_used_to_protocol(self):
        ids = self.get_ids_can_used_to_protocol()
        for registro_emergenza in self:
            if registro_emergenza.id in ids:
                registro_emergenza.can_used_to_protocol = True
            else:
                registro_emergenza.can_used_to_protocol = False

    def _search_can_used_to_protocol(self, operator=None, operand=None):
        ids = self.get_ids_can_used_to_protocol()
        return [("id", "in", ids)]

    @api.model
    def get_configurazione_assegnazione(self, prima_assegnazione):
        config_obj = self.env["ir.config_parameter"].sudo()
        if prima_assegnazione:
            return config_obj.get_param("sd_protocollo.prima_assegnazione", False)
        return self.env["ir.config_parameter"].sudo().get_param("sd_protocollo.assegnazione")

    @api.model
    def get_disable_ids(self, prima_assegnazione=False):
        configurazione_assegnazione = self.get_configurazione_assegnazione(prima_assegnazione)
        if configurazione_assegnazione == "utenti":
            # se la configurazione dell'assegnazione prevede solo utenti allora devono essere disabilitati tutti gli uffici
            domain = [("tipologia", "=", "ufficio")]
        else:
            # altrimenti devono essere disabilitati tutti gli uffici che non contengono utenti
            ufficio_abilitato_list = self.search_read([
                ("tipologia", "=", "utente"),
                ("parent_id", "!=", False)
            ], ["parent_id"])
            ufficio_abilitato_ids = [ufficio_abilitato["parent_id"][0] for ufficio_abilitato in ufficio_abilitato_list]
            domain = ["&", ("tipologia", "=", "ufficio"), ("id", "not in", ufficio_abilitato_ids)]
            if configurazione_assegnazione == "uffici":
                # inoltre se la configurazione dell'assegnazione prevede solo uffici allora devono essere disabilitati anche tutti gli utenti
                domain.insert(0, "|")
                domain.insert(1, ("tipologia", "=", "utente"))
        results = self.search_read(domain, ["id"])
        return [result["id"] for result in results]

    # Fix widget ztree -> Ufficio senza utenti impostato come user
    def _get_extra_fields_ztree(self):
        if self._name == 'fl.set.voce.organigramma':
            return ['ufficio_id']
        return []

    def _get_extra_record_value_ztree(self, x):
        if self._name == 'fl.set.voce.organigramma':
            if x["ufficio_id"]:
                return {'isParent': True}
        return {}
