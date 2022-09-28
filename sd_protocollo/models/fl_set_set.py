from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Set(models.Model):
    _inherit = "fl.set.set"

    can_used_to_protocol = fields.Boolean(
        string="Can Used To Protocol",
        compute="_compute_can_used_to_protocol",
        search="_search_can_used_to_protocol"
    )

    @api.model
    def get_domain_can_used_to_protocol(self):
        registro_ids = self.env["sd.protocollo.registro"].search([("can_used_to_protocol", "=", True)]).ids
        return [
            ("user_ids", "in", [self.env.uid]),
            ("company_id.registro_ids", "in", registro_ids)
        ]

    @api.model
    def get_ids_can_used_to_protocol(self):
        ids = self.env["fl.set.set"].search(self.get_domain_can_used_to_protocol()).ids
        return ids

    def _compute_can_used_to_protocol(self):
        set_ids = self.get_ids_can_used_to_protocol()
        for set in self:
            if set.id in set_ids:
                set.can_used_to_protocol = True
            else:
                set.can_used_to_protocol = False

    def _search_can_used_to_protocol(self, operator=None, operand=None):
        ids = self.get_ids_can_used_to_protocol()
        return [("id", "in", ids)]

    @api.constrains("company_id", "set_type")
    def _validate_set(self):
        for fl_set in self:
            if self._check_set(fl_set):
                self._raise_error_message()

    def _check_set(self, fl_set):
        voce_orgnanigramma_obj = self.env["fl.set.voce.organigramma"]
        prot_obj = self.env["sd.protocollo.protocollo"]
        assegnazione_obj = self.env["sd.protocollo.assegnazione"]

        # Verifico la presenza di protocolli associati tramite "protocollatore_ufficio_id"
        protocolli_associati = prot_obj.search_count([("protocollatore_ufficio_id", "=", fl_set.id)])
        if protocolli_associati > 0:
            return True

        # Verifico la presenza di assegnazioni riconducibili al set che si vuole controllare
        assegnazioni_associate = assegnazione_obj.search_count(
            ['|', ("assegnatario_ufficio_id", "=", fl_set.id), ("assegnatore_parent_id", "=", fl_set.id)])
        if assegnazioni_associate > 0:
            return True

        # Ricerco i protocolli che hanno come mittente_interno_id una voce_organigramma con ufficio_id uguale al set
        mittente_organigramma_id = voce_orgnanigramma_obj.search([("ufficio_id", "=", fl_set.id)]).id
        protocolli_associati = prot_obj.search_count([("mittente_interno_id", "=", mittente_organigramma_id)])
        if protocolli_associati > 0:
            return True

        return False

    def _raise_error_message(self, message=False):
        if not message:
            message = "Non è possibile modificare la struttura:\nÈ stata già utilizzata nella protocollazione"
        raise ValidationError(_(message))
