from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class Protocollo(models.Model):
    _inherit = "sd.protocollo.protocollo"

    aoo_id = fields.Many2one(
        string="AOO",
        comodel_name="fl.set.set",
        readonly=True
    )

    mittente_interno_utente_id_parent_id = fields.Char(
        char="Mittente interno parent (UO)",
        compute="compute_mittente_ufficio_id_values"
    )

    mittente_interno_ufficio_id_aoo_id_name = fields.Char(
        string="Mittente interno ufficio aoo nome",
        compute="compute_mittente_ufficio_id_values"
    )

    mittente_interno_ufficio_id_aoo_id_company_id_name = fields.Char(
        string="Mittente interno ufficio aoo nome",
        compute="compute_mittente_ufficio_id_values"
    )

    documento_id_cartella_id = fields.Many2one(
        domain="[('company_id', '=', company_id),('aoo_id','=', aoo_id),('perm_create', '=', True)]",
    )

    @api.depends("mittente_interno_id")
    def compute_mittente_ufficio_id_values(self):
        for rec in self:
            mittente_interno_ufficio_id_aoo_id_name = False
            mittente_interno_ufficio_id_aoo_id_company_id_name = False
            mittente_interno_utente_id_parent_id = False

            if rec.mittente_interno_id.ufficio_id:
                mittente_interno_ufficio_id_aoo_id_name = rec.mittente_interno_id.ufficio_id.aoo_id.name
                mittente_interno_ufficio_id_aoo_id_company_id_name = rec.mittente_interno_id.ufficio_id.aoo_id.company_id.name

            elif rec.mittente_interno_id.utente_id:
                aoo = rec.mittente_interno_id.parent_id.aoo_id
                mittente_interno_utente_id_parent_id = rec.mittente_interno_id.parent_id.nome
                mittente_interno_ufficio_id_aoo_id_name = aoo.name
                mittente_interno_ufficio_id_aoo_id_company_id_name = aoo.company_id.name

            rec.mittente_interno_utente_id_parent_id = mittente_interno_utente_id_parent_id
            rec.mittente_interno_ufficio_id_aoo_id_name = mittente_interno_ufficio_id_aoo_id_name
            rec.mittente_interno_ufficio_id_aoo_id_company_id_name = mittente_interno_ufficio_id_aoo_id_company_id_name

    @api.onchange("protocollatore_ufficio_id")
    def onchange_protocollatore_ufficio_id(self):
        aoo_id = self.protocollatore_ufficio_id.aoo_id.id
        self.aoo_id = aoo_id
        context = dict(
            self.env.context,
            aoo_id=aoo_id
        )
        self = self.with_context(context)
        super(Protocollo, self).onchange_protocollatore_ufficio_id()

    def _get_mittente_interno_display_name(self):
        display_name_list = super(Protocollo, self)._get_mittente_interno_display_name()
        pa_display_name_list = []
        if self.mittente_interno_ufficio_id_aoo_id_company_id_name:
            pa_display_name_list.append(self.mittente_interno_ufficio_id_aoo_id_company_id_name)
        if self.mittente_interno_ufficio_id_aoo_id_name:
            pa_display_name_list.append(self.mittente_interno_ufficio_id_aoo_id_name)
        if self.mittente_interno_utente_id:
            pa_display_name_list.append(self.mittente_interno_utente_id_parent_id)
        pa_display_name_list.append(display_name_list[0])
        return pa_display_name_list

    @api.model
    def _get_copy_context(self, protocollatore_ufficio):
        context = super(Protocollo, self)._get_copy_context(protocollatore_ufficio)
        aoo_id = self.protocollatore_ufficio_id.aoo_id.id
        self.aoo_id = aoo_id
        context = dict(
            context,
            aoo_id=aoo_id
        )
        return context