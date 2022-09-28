from odoo import models, fields, api


class WizardProtocolloCaricaDocumento(models.TransientModel):
    _name = "sd.protocollo.wizard.protocollo.carica.documento"
    _description = "Wizard Protocollo Carica Documento"

    filename = fields.Char(
        string="File Name",
        required=True
    )

    content = fields.Binary(
        string="Content",
        required=True
    )

    folder_id = fields.Many2one(
        string="Folder",
        comodel_name="sd.dms.folder",
        domain="[('perm_create', '=', True)]",
        required=True
    )

    subject = fields.Text(
        string="Subject"
    )

    @api.model
    def default_get(self, fields_list):
        protocollo_obj = self.env["sd.protocollo.protocollo"]
        documento_obj = self.env["sd.dms.document"]

        res = super(WizardProtocolloCaricaDocumento, self).default_get(fields_list)
        tipologia_documento = self.env.context.get("tipologia_documento", False)
        protocollo_id = self.env.context.get("protocollo_id", False)
        active_model = self.env.context.get("active_model", False)
        default_folder = False
        if protocollo_id and active_model=="sd.protocollo.protocollo":
            protocollo = protocollo_obj.browse(protocollo_id)
            default_folder = self.env["sd.protocollo.cartella"].get_folder(protocollo, "protocollo")

        if self.env.context.get("allegato_id", False):
            documento = documento_obj.browse(protocollo_id)
        elif tipologia_documento == "allegato":
            documento = documento_obj
        else:
            documento = protocollo_obj.browse(protocollo_id).documento_id

        res["filename"] = documento.filename
        res["content"] = documento.content
        res["folder_id"] = documento.folder_id if documento.folder_id else default_folder
        res["subject"] = documento.subject

        return res

    def action_create_modify(self):
        protocollo_obj = self.env["sd.protocollo.protocollo"]
        documento_obj = self.env["sd.dms.document"]

        tipologia_documento = self.env.context.get("tipologia_documento", False)
        protocollo_id = self.env.context.get("protocollo_id", False)

        # SI STA MODIFICANDO UN ALLEGATO
        if self.env.context.get("allegato_id", False):
            documento = documento_obj.browse(protocollo_id)
        elif tipologia_documento == "documento":
            protocollo = protocollo_obj.browse(protocollo_id)
            documento = protocollo.documento_id
        else:
            documento = False

        documento_vals = self._get_documento_vals({
            "protocollo_id": self.id,
            "filename": self.filename,
            "content": self.content,
            "subject": self.subject,
            "folder_id": self.folder_id.id
        })

        if not documento:
            documento = documento_obj.create(documento_vals)
        else:
            documento.write(documento_vals)

        return documento

    def _get_documento_vals(self, vals):
        return vals
