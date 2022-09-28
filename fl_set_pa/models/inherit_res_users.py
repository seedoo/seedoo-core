from odoo import models


class ResUsers(models.Model):
    _inherit = "res.users"

    def get_aoo_id_readonly(self):
        """
        Verifica se l'utente appartiene a più di una AOO
        @return: False (<=1); True (>1)
        """
        if len(list(dict.fromkeys(self.fl_set_set_ids.aoo_id.ids))) > 1:
            return False
        return True