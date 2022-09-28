from odoo import models, api


class InheritResUsers(models.Model):
    _inherit = 'res.users'

    def _update_folders_acl(self):
        super(InheritResUsers, self)._update_folders_acl()
        self._update_folder_acl(
            folder_xml_id="sd_protocollo.data_sd_dms_folder_protocollo",
            module_xml_id="base.module_sd_protocollo",
            group_xml_id="sd_protocollo.group_sd_protocollo_assegnatario",
            perm_create=False,
            perm_read=True,
            perm_write=False,
            perm_delete=False
        )
        self._update_folder_acl(
            folder_xml_id="sd_protocollo.data_sd_dms_folder_protocolli",
            module_xml_id="base.module_sd_protocollo",
            group_xml_id="sd_protocollo.group_sd_protocollo_assegnatario",
            perm_create=True,
            perm_read=True,
            perm_write=True,
            perm_delete=False
        )
        self._update_folder_acl(
            folder_xml_id="sd_protocollo.data_sd_dms_folder_registri_giornalieri",
            module_xml_id="base.module_sd_protocollo",
            group_xml_id="sd_protocollo.group_sd_protocollo_manager",
            perm_create=True,
            perm_read=True,
            perm_write=True,
            perm_delete=False
        )