from odoo import fields, models, api


class VoceOrganigramma(models.Model):
    _inherit = "fl.set.voce.organigramma"

    aoo_id = fields.Many2one(
        string="AOO",
        comodel_name="fl.set.set"
    )

    @api.model
    def get_view_fields_from_users(self):
        view_fields = super(VoceOrganigramma, self).get_view_fields_from_users()
        view_fields += """,
            fss.aoo_id AS aoo_id
        """
        return view_fields

    @api.model
    def get_view_fields_from_sets(self):
        view_fields = super(VoceOrganigramma, self).get_view_fields_from_sets()
        view_fields += """,
            uf.aoo_id AS aoo_id
        """
        return view_fields

    @api.model
    def get_domain_utente(self, field_dict=False):
        domain_utente = super(VoceOrganigramma, self).get_domain_utente(field_dict)
        if field_dict and "aoo_id" in field_dict:
            aoo_id = field_dict["aoo_id"][0]
        elif self.env.context.get("aoo_id", False):
            aoo_id = self.env.context.get("aoo_id")
        else:
            return domain_utente
        domain_utente = ["&"] + domain_utente + [("aoo_id", "=", aoo_id)]
        return domain_utente

    @api.model
    def get_domain_ufficio(self, field_dict=False):
        domain_ufficio = super(VoceOrganigramma, self).get_domain_ufficio(field_dict)
        domain_ufficio = ["&"] + domain_ufficio + [("tipologia_ufficio", "=", "uo")]
        if field_dict and "aoo_id" in field_dict:
            aoo_id = field_dict["aoo_id"][0]
        elif self.env.context.get("aoo_id", False):
            aoo_id = self.env.context.get("aoo_id")
        else:
            return domain_ufficio
        domain_ufficio = ["&"] + domain_ufficio + [("aoo_id", "=", aoo_id)]
        return domain_ufficio

    @api.model
    def get_protocollo_fields(self):
        field_list = super(VoceOrganigramma, self).get_protocollo_fields()
        field_list.append("aoo_id")
        return field_list
