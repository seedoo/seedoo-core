# Copyright 2020-2022 Flosslab S.r.l.
# Copyright 2017-2019 MuK IT GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, fields, api


class FolderPermissions(models.Model):
    _inherit = "sd.dms.folder"

    name_readonly = fields.Boolean(
        string="name readonly",
        compute="_compute_fields_readonly"
    )

    parent_folder_id_readonly = fields.Boolean(
        string="parent_folder_id readonly",
        compute="_compute_fields_readonly"
    )

    def _compute_fields_readonly(self):
        for record in self:
            record.name_readonly = record._compute_name_readonly()
            record.parent_folder_id_readonly = record._compute_parent_folder_id_readonly()

    def _compute_name_readonly(self):
        # Readonly se:
        # - l'utente corrente non ha permessi di scrittura sul record
        if not self.perm_write:
            return True
        return self._is_structure_folder_readonly()

    def _compute_parent_folder_id_readonly(self):
        # Readonly se:
        # - l'utente corrente non ha permessi di scrittura sul record
        if not self.perm_write:
            return True
        return self._is_structure_folder_readonly()

    def _is_structure_folder_readonly(self):
        # il campo per essere readonly deve avere entrambe le seguenti condizioni vere:
        # - l'utente corrente non ha il gruppo group_sd_dms_administrator
        # - la cartella è stata creata mediante l'algoritmo di structure folder
        return not self.env.user.has_group("sd_dms.group_sd_dms_administrator") and \
               self.structure_folder