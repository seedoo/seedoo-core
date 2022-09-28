# Copyright 2020-2022 Flosslab S.r.l.
# Copyright 2017-2019 MuK IT GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import models,fields, api
from odoo.exceptions import ValidationError
import time
import logging

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = "res.users"

    default_folder_id = fields.Many2one(
        string="Default folder",
        help="Default folder in documents kanban view",
        comodel_name="sd.dms.folder",
        domain=[("is_root_folder", "=", True)]
    )

    def __init__(self, pool, cr):
        init_res = super().__init__(pool, cr)
        type(self).SELF_WRITEABLE_FIELDS = self.SELF_WRITEABLE_FIELDS + ['default_folder_id']
        type(self).SELF_READABLE_FIELDS = self.SELF_READABLE_FIELDS + ['default_folder_id']
        return init_res

    def _request_notify_message(self, type, title, message, sticky=False):
        """
        @param str type: type of notification (success, danger, warning, info, default)
        @param str title: Header of the notification
        @param str message: Body of the notification
        @param bool sticky: True if sticky False if the notification disappear
        """
        self.ensure_one()

        message = {
            "title": title,
            "message": message,
            "sticky": sticky
        }
        if type == "success":
            self.notify_success(**message)
        elif type == "danger":
            self.notify_danger(**message)
        elif type == "warning":
            self.notify_warning(**message)
        elif type == "info":
            self.notify_info(**message)
        elif type == "default":
            self.notify_default(**message)
        else:
            raise ValidationError("Type of notification selected doesn't exist!")

    @api.model
    def create(self, vals):
        record = super(ResUsers, self).create(vals)
        record._update_folders_acl()
        return record

    def write(self, vals):
        result = super(ResUsers, self).write(vals)
        self._update_folders_acl()
        return result

    def _update_folders_acl(self):
        self._update_folder_acl(
            folder_xml_id="sd_dms.data_sd_dms_folder_root",
            module_xml_id="base.module_sd_dms",
            group_xml_id="sd_dms.group_sd_dms_user",
            perm_create=False,
            perm_read=True,
            perm_write=False,
            perm_delete=False
        )

    def _update_folder_acl(self, folder_xml_id, module_xml_id, group_xml_id, perm_create, perm_read, perm_write, perm_delete):
        module = self.env.ref(module_xml_id)
        if not module:
            return
        folder = self.env.ref(folder_xml_id)
        if not folder:
            return
        for record in self:
            folder_acl = self.env["sd.dms.folder.acl"].search([
                ("id", "in", folder.system_acl_ids.ids),
                ("res_model", "=", "res_users"),
                ("res_id", "=", record.id),
                ("module_id", "=", module.id),
                ("create_system", "=", True)
            ], limit=1)
            if record.with_user(record).user_has_groups(group_xml_id) and not folder_acl:
                folder.write({
                    "system_acl_ids": [(0, 0, {
                        "res_model": "res_users",
                        "res_id": record.id,
                        "res_name": record.name,
                        "module_id": module.id,
                        "create_system": True,
                        "perm_create": perm_create,
                        "perm_read": perm_read,
                        "perm_write": perm_write,
                        "perm_delete": perm_delete
                    })]
                })
            elif record.with_user(record).user_has_groups(group_xml_id) and folder_acl:
                folder_acl.write({
                    "perm_create": perm_create,
                    "perm_read": perm_read,
                    "perm_write": perm_write,
                    "perm_delete": perm_delete
                })
            elif not record.with_user(record).user_has_groups(group_xml_id) and folder_acl:
                folder_acl.unlink()

    def get_default_folder_for_documents(self):
        self.ensure_one()
        default_folder = self.env.ref("sd_dms.data_sd_dms_folder_root").id
        return {"folder_id": self.default_folder_id.id or default_folder}