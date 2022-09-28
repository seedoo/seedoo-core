from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

SELECTION_INTEGRAZIONE = [
    ("pec", "PEC"),
]


class MezzoTrasmissione(models.Model):
    _inherit = "sd.protocollo.mezzo.trasmissione"

    integrazione = fields.Selection(
        string="Integrazione",
        selection=SELECTION_INTEGRAZIONE,
    )

    @api.constrains("integrazione", "company_id")
    def _check_unique_mezzo_trasmissione(self):
        # Verifico che esista solo un mezzo di trasmissione di tipo pec, se il search_count ne restituisce più di uno
        # per company significa che si sta provando a crearne un altro e si fa il raise dell'errore
        for rec in self:
            domain_list = rec._get_constraint_integrazione_domain()
            for domain in domain_list:
                if self.search_count(domain) > 1:
                    return self._raise_message_error(rec.integrazione)

    def _raise_message_error(self, integrazione):
        if integrazione:
            msg_error = "È già presente un mezzo di trasmissione con integrazione (%s) per questa company" % integrazione
            raise ValidationError(_(msg_error))

    def _get_constraint_integrazione_domain(self):
        return [[("integrazione", "=", "pec"), ("company_id", "=", self.company_id.id)]]

    def get_domain_can_used_to_protocol(self):
        domain = super(MezzoTrasmissione, self).get_domain_can_used_to_protocol()
        tipologia_protocollo = self.env.context.get("tipologia_protocollo", False)
        if tipologia_protocollo == "ingresso":
            domain.append(("integrazione", "not in", self.get_integrazione_values()))
            return domain
        if tipologia_protocollo == "uscita":
            account_count = self.env["fl.mail.client.account"].search([
                ('use_outgoing_server', '=', True),
                ('pec', '=', True)
            ], count=True)
            if account_count == 0:
                domain.append(("integrazione", "not in", ["pec"]))
            return domain
        return domain

    @api.model
    def get_integrazione_values(self):
        return ["pec"]
