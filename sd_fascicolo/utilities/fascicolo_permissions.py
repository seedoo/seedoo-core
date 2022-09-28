from odoo import models, fields, api


class Fascicolo(models.Model):
    _inherit = "sd.fascicolo.fascicolo"

    field_readonly = fields.Boolean(
        string="field readonly",
        compute="_compute_buttons_invisible"
    )

    documento_ids_readonly = fields.Boolean(
        string="documento_ids readonly",
        compute="_compute_buttons_invisible"
    )

    button_apri_fascicolo_invisible = fields.Boolean(
        string="button apri fascicolo invisible",
        compute="_compute_buttons_invisible"
    )

    button_chiudi_fascicolo_invisible = fields.Boolean(
        string="button chiudi fascicolo invisible",
        compute="_compute_buttons_invisible"
    )

    button_fascicolo_aggiungi_documento_invisible = fields.Boolean(
        string="button fascicolo aggiungi documento invisible",
        compute="_compute_buttons_invisible"
    )

    button_tree_disassocia_fascicolo_invisible = fields.Boolean(
        string="button tree disassocia fascicolo invisible",
        compute="_compute_button_tree_disassocia_fascicolo_invisible"
    )

    button_add_rup_invisible = fields.Boolean(
        string="button aggiungi rup invisible",
        compute="_compute_buttons_invisible"
    )

    button_add_soggetto_intestatario_invisible = fields.Boolean(
        string="button aggiungi soggetto intestatario invisible",
        compute="_compute_buttons_invisible"
    )

    button_add_amministrazione_titolare_invisible = fields.Boolean(
        string="button aggiungi amministrazione titolare invisible",
        compute="_compute_buttons_invisible"
    )

    button_add_amministrazione_partecipante_invisible = fields.Boolean(
        string="button aggiungi amministrazione partecipante invisible",
        compute="_compute_buttons_invisible"
    )

    ufficio_autore_id_readonly = fields.Boolean(
        string="Ufficio autore readonly",
        compute="_compute_ufficio_autore_id_readonly",
    )

    categoria_readonly = fields.Boolean(
        string="Categoria readonly",
        compute="_compute_categoria_readonly",
        default=False
    )

    @api.depends("autore_id")
    def _compute_ufficio_autore_id_readonly(self):
        # Visibilità autore_id_readonly:
        # utente corrente = all'untente che ha creato il documento;
        # stato in bozza o aperto
        # permesso di write delle acl (perm_write) a True
        # se appartiene ad un solo ufficio e l'ufficio è uguale a quello presente nel record
        for dossier in self:
            fl_set_set_obj = self.env["fl.set.set"].sudo()
            has_changed_office = False
            if dossier.ufficio_autore_id:
                if self.env.user.id not in fl_set_set_obj.browse(dossier.ufficio_autore_id.id).user_ids.ids:
                    has_changed_office = True
            condition_1 = (fl_set_set_obj.search([("user_ids", "=", dossier.autore_id.id)],count=True) == 1
                           and not has_changed_office)
            # se
            condition_2 = not ((self.env.user == dossier.create_uid or not dossier.create_uid)
                               and dossier.state != "chiuso" and dossier.perm_write)
            if condition_1 or condition_2:
                dossier.ufficio_autore_id_readonly = True
            else:
                dossier.ufficio_autore_id_readonly = False

    @api.depends("state")
    def _compute_buttons_invisible(self):
        for rec in self:
            rec.field_readonly = rec._compute_field_readonly()
            rec.documento_ids_readonly = rec._compute_documento_ids_readonly()
            rec.button_apri_fascicolo_invisible = rec._compute_button_apri_fascicolo_invisible()
            rec.button_chiudi_fascicolo_invisible = rec._compute_button_chiudi_fascicolo_invisible()
            rec.button_fascicolo_aggiungi_documento_invisible = rec._compute_button_fascicolo_aggiungi_documento_invisible()
            rec.button_add_rup_invisible = rec._compute_button_add_rup_invisible()
            rec.button_add_soggetto_intestatario_invisible = rec._compute_button_add_soggetto_intestatario_invisible()
            rec.button_add_amministrazione_titolare_invisible = rec._compute_button_add_amministrazione_titolare_invisible()
            rec.button_add_amministrazione_partecipante_invisible = rec._compute_button_add_amministrazione_partecipante_invisible()

    def _compute_categoria_readonly(self):
        # Visibilità categoria_readonly:
        # utente corrente = all'untente che ha creato il documento;
        # stato in bozza o aperto
        # permesso di write delle acl (perm_write) a True
        for dossier in self:
            if (
                    self.env.user == dossier.create_uid or not dossier.create_uid) and dossier.state != "chiuso" and dossier.perm_write:
                dossier.categoria_readonly = False
            else:
                dossier.categoria_readonly = True

    def _compute_field_readonly(self):
        # Visibilità field_readonly:
        # utente corrente = all'untente che ha creato il documento;
        # stato in bozza
        # permesso di write delle acl (perm_write) a True
        field_readonly = True
        if (self.env.user == self.create_uid or not self.create_uid) and self.state == "bozza" and self.perm_write:
            field_readonly = False
        return field_readonly

    def _compute_documento_ids_readonly(self):
        # Visibilità documento_ids_readonly:
        # utente corrente = all'untente che ha creato il documento;
        # stato in bozza o aperto
        # permesso di write delle acl (perm_write) a True
        documento_ids_readonly = True
        if (self.env.user == self.create_uid or not self.create_uid) and self.state != "chiuso" and self.perm_write:
            documento_ids_readonly = False
        return documento_ids_readonly

    def _compute_button_apri_fascicolo_invisible(self):
        # Visibilità button_apri_fasciolo_invisible:
        # utente corrente = all'untente che ha creato il documento;
        # stato in bozza o chiuso
        # permesso di write delle acl (perm_write) a True
        button_apri_fasciolo_invisible = True
        if (self.env.user == self.create_uid or not self.create_uid) and self.state != "aperto" and self.perm_write:
            button_apri_fasciolo_invisible = False
        return button_apri_fasciolo_invisible

    def _compute_button_chiudi_fascicolo_invisible(self):
        # Visibilità button_chiudi_fascicolo_invisible:
        # utente corrente = all'untente che ha creato il documento;
        # stato = aperto
        # permesso di write delle acl (perm_write) a True
        button_chiudi_fascicolo_invisible = True
        if (self.env.user == self.create_uid or not self.create_uid) and self.state == "aperto" and self.perm_write:
            button_chiudi_fascicolo_invisible = False
        return button_chiudi_fascicolo_invisible

    def _compute_button_fascicolo_aggiungi_documento_invisible(self):
        if self.perm_write and self.state == "aperto":
            return False
        else:
            return True

    def _compute_button_tree_disassocia_fascicolo_invisible(self):
        for rec in self:
            button_tree_disassocia_fascicolo_invisible = True
            if rec.env.context.get("disassocia_fascicolo_documento_id", False) and rec.perm_write:
                button_tree_disassocia_fascicolo_invisible = False
            rec.button_tree_disassocia_fascicolo_invisible = button_tree_disassocia_fascicolo_invisible

    def _compute_button_add_rup_invisible(self):
        for rec in self:
            if len(rec.rup_ids) > 0 or not rec.perm_write or rec.state == "chiuso":
                return True
        return False

    def _compute_button_add_soggetto_intestatario_invisible(self):
        for rec in self:
            if len(rec.soggetto_intestatario_ids) > 0 or not rec.perm_write or rec.state == "chiuso":
                return True
        return False

    def _compute_button_add_amministrazione_titolare_invisible(self):
        for rec in self:
            if len(rec.amministrazione_titolare_ids) > 0 or not rec.perm_write or rec.state == "chiuso":
                return True
        return False

    def _compute_button_add_amministrazione_partecipante_invisible(self):
        for rec in self:
            if not rec.perm_write or rec.state == "chiuso":
                return True
        return False
