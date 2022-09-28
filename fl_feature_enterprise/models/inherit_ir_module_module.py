from odoo import models, api


class IrModuleModule(models.Model):
    _inherit = "ir.module.module"

    @api.model
    def show_dialog_on_checkbox_click(self, module_name):
        show_dialog = True

        # campi enterprise che non installano direttamente il modulo
        modules_field_value = {
            # fl_mail
            "fetch_from_custom_folder": ["module_fl_mail_client_fetch_flow"],
            "move_processed_mail": ["module_fl_mail_client_fetch_flow"],
            # sd_protocollo
            "genera_segnatura_allegati": ["module_fl_protocollo_segnatura_pdf"],
            "genera_segnatura_su_ogni_pagina": ["module_fl_protocollo_segnatura_pdf"],
            "codice_ufficio_in_segnatura": ["module_fl_protocollo_segnatura_pdf"]
        }

        if modules_field_value.get(module_name[0], False):
            module_name = modules_field_value[module_name[0]]

        module_name_list = module_name[0].split("_")
        # rimozione del module_ dal module_name es. module_fl_feature_enterprise -> fl_feature_enterprise
        module_name_list.pop(0)
        module_name_str = "_".join(module_name_list)
        module = self.search([("name", "=", module_name_str)], limit=1)
        if module:
            show_dialog = False

        return show_dialog
