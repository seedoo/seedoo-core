# Copyright 2020-2022 Flosslab S.r.l.
# Copyright 2017-2019 MuK IT GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # ----------------------------------------------------------
    # Security Addons
    # ----------------------------------------------------------

    module_fl_acl = fields.Boolean(
        string="ACL Users",
        help="Enables control access list for users in apps"
    )

    module_fl_acl_set = fields.Boolean(
        string="ACL Sets",
        help="Enables control access list for sets in apps"
    )

    # ----------------------------------------------------------
    # Base Addons
    # ----------------------------------------------------------

    module_fl_dms_version = fields.Boolean(
        string="Versioning",
        help="Enables version control for files."
    )

    # ----------------------------------------------------------
    # Attachment Addons
    # ----------------------------------------------------------

    module_fl_dms_attachment = fields.Boolean(
        string="Documents Storage Location",
        help="Allows attachments to be stored inside of Documents."
    )

    # ----------------------------------------------------------
    # Other Addons
    # ----------------------------------------------------------

    module_fl_dms_conservazione = fields.Boolean(
        string="Conservazione digitale",
    )

    module_sd_dms_titolario = fields.Boolean(
        string="Classifica tramite titolario",
    )

    module_sd_dms_aoo = fields.Boolean(
        string="Gestione AOO",
    )

    module_fl_dms_fulltext = fields.Boolean(
        string="Full-text Content Search"
    )

    module_fl_dms_onlyoffice = fields.Boolean(
        string="Onlyoffice editor"
    )

    module_fl_dms_workflow = fields.Boolean(
        string="Workflow"
    )

    module_fl_dms_importer = fields.Boolean(
        string="Massive file importer"
    )
	
    module_fl_dms_repertorio = fields.Boolean(
        string="Repertory"
    )

    module_fl_dms_set_folder = fields.Boolean(
        string="Set folders"
    )
	
    # ----------------------------------------------------------
    # Document Preview
    # ----------------------------------------------------------

    module_fl_web_preview = fields.Boolean(
        string="Preview PDF",
    )

    module_fl_web_preview_csv = fields.Boolean(
        string="Preview CSV",
    )

    module_fl_web_preview_image = fields.Boolean(
        string="Preview image",
    )

    module_fl_web_preview_libreoffice = fields.Boolean(
        string="Preview LibreOffice",
    )

    module_fl_web_preview_msoffice = fields.Boolean(
        string="Preview MSOffice",
    )

    module_fl_web_preview_rst = fields.Boolean(
        string="Preview RST",
    )

    module_fl_web_preview_text = fields.Boolean(
        string="Preview text ",
    )

    module_fl_web_preview_mail = fields.Boolean(
        string="Preview mail",
    )

    module_fl_dms_preview_sidebox = fields.Boolean(
        string="Preview sidebox",
    )

    fl_web_preview_msoffice_web_base_url = fields.Char(
        string="Odoo base url to fetch file in MSOffice iframe",
        config_parameter="fl_web_preview_msoffice.web_base_url"
    )