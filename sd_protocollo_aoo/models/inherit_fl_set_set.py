from odoo import models, api


class Set(models.Model):
    _inherit = "fl.set.set"

    @api.constrains("company_id", "set_type", "aoo_id")
    def _validate_set(self):
        # In caso venga cambiata il campo aoo_id del set si triggera la validazione
        return super(Set, self)._validate_set()

    def _check_set(self, fl_set):
        protocollo_obj = self.env["sd.protocollo.protocollo"]

        res = super(Set, self)._check_set(fl_set)
        if not res:
            # Se si vuole cambiare la company o il set_type di una aoo bisogna verificare che non ci siano protocolli
            # associati tramite aoo_id. Solamente i Set di tipo aoo sono referenziati al protocollo tramite aoo_id
            # in caso non presenti signigia che il set non è una aoo oppure non ha nessun protocollo associato
            # e quindi si può modificare.
            protocolli_count = protocollo_obj.search_count([("aoo_id", "=", fl_set.id)])
            if protocolli_count > 0:
                return True
        return res
