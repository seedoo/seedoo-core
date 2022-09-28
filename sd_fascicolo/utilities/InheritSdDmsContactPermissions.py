# Copyright 2020-2022 Flosslab S.r.l.
# Copyright 2017-2019 MuK IT GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, fields, api


class InheritSdDmsContactPermissions(models.Model):
    _inherit = "sd.dms.contact"

    def _compute_button_edit_contact_invisible(self):
        fascicolo_id = self.env.context.get("fascicolo_id", False)
        if not fascicolo_id:
            return super(InheritSdDmsContactPermissions, self)._compute_button_edit_contact_invisible()

        for rec in self:
            rec.button_edit_contact_invisible = False
            # il button di modifica contatti è invisibile se almeno uno dei documenti associati è in sola lettura
            dossiers = self.env["sd.fascicolo.fascicolo"].search(["|","|","|",
                                                                ("rup_ids", "=", rec.id),
                                                                ("soggetto_intestatario_ids", "=", rec.id),
                                                                ("amministrazione_partecipante_ids", "=", rec.id),
                                                                ("amministrazione_titolare_ids", "=", rec.id)])
            for dossier in dossiers:
                if dossier.state == "chiuso" or not dossier.perm_write:
                    rec.button_edit_contact_invisible = True
                    break