from odoo import models, fields, api, _


class Document(models.Model):
    _inherit = "sd.dms.document"

    voce_titolario_id = fields.Many2one(
        string="Classificazione",
        comodel_name="sd.dms.titolario.voce.titolario",
        domain="[('titolario_id.active','=',True), ('titolario_id.state','=',True), ('parent_active', '=', True)]",
        required=False
    )

    voce_titolario_name = fields.Char(
        string="Voce Titolario Nome"
    )

    @api.onchange("voce_titolario_id")
    def _onchange_voce_titolario_id(self):
        document = self.browse(self.id.origin)
        voce_titolario_company_id = self.voce_titolario_id.titolario_id.company_id.id
        if voce_titolario_company_id and document and self.company_id:
            if document and document.company_id.id != voce_titolario_company_id or self.company_id.id != voce_titolario_company_id:
                return {'warning': {
                    'title': _('Warning!'),
                    'message': _(
                        "La company del titolario è diversa da quella del documento, non sarà possibile salvarla."
                    ),
                }}

    @api.constrains("category_id", "voce_titolario_id")
    def _validate_document(self):
        return super(Document, self)._validate_document()

    def _check_company_document(self, document):
        res = super(Document, self)._check_company_document(document)
        if not res:
            if document.voce_titolario_id and document.voce_titolario_id.titolario_company_id != document.company_id:
                return "Non è possibile completare l'operazione:\ncontrolla la company della voce di titolario inserita"
        return res

    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        if self.voce_titolario_id:
            default["voce_titolario_id"] = self.voce_titolario_id.id
            default["voce_titolario_name"] = self.voce_titolario_id.path_name
        else:
            default["voce_titolario_id"] = False
            default["voce_titolario_name"] = False
        return super(Document, self).copy(default=default)

    @api.model
    def _get_fields_to_hide(self):
        fields_to_hide = super(Document, self)._get_fields_to_hide()
        fields_to_hide.append("voce_titolario_name")
        return fields_to_hide