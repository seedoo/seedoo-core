from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.fields import Datetime


class DocumentoWizardCreaBozzaProtocollo(models.TransientModel):
    _name = "sd.protocollo.wizard.documento.crea.bozza"
    _description = "Wizard protocollo documento crea bozza"

    def _get_documenti_protocollo_selection(self):
        selection_tipologia_protocollo = []
        if "documento_ids" in self.env.context:
            documeto_ids = self.env.context["documento_ids"]
            documenti = self.env["sd.dms.document"].search([("id", "in", documeto_ids)])
            for documento in documenti:
                selection_tipologia_protocollo.append((str(documento.id), documento.filename))
        return selection_tipologia_protocollo

    selection_documenti = fields.Selection(
        string="Documents",
        selection=lambda self: self._get_documenti_protocollo_selection(),
    )

    crea_bozza = fields.Boolean(
        string="Create draft"
    )

    registro_id = fields.Many2one(
        string="Register",
        comodel_name="sd.protocollo.registro",
        domain="[('can_used_to_protocol', '=', True)]",
    )

    registro_id_readonly = fields.Boolean(
        string="Company invisible"
    )

    company_id = fields.Many2one(
        string="Azienda",
        comodel_name="res.company",
        required=True,
        default=lambda self: self.env["sd.protocollo.protocollo"]._default_company_id()
    )

    company_id_invisible = fields.Boolean(
        string="Company invisible"
    )

    mezzo_trasmissione_id = fields.Many2one(
        string="Means of transmission",
        comodel_name="sd.protocollo.mezzo.trasmissione",
        domain="[('can_used_to_protocol','=',True)]"
    )

    mezzo_trasmissione_id_invisible = fields.Boolean(
        string="Means of transmission invisible",
        compute="_compute_mezzo_trasmissione_id_invisible"
    )

    user_tipologia_protocollo = fields.Selection(
        string="Typology",
        selection=lambda self: self.env["sd.protocollo.protocollo"]._get_user_tipologia_protocollo_selection(),
    )

    protocollatore_ufficio_id = fields.Many2one(
        string="Office head of protocol",
        comodel_name="fl.set.set",
        domain="[('can_used_to_protocol', '=', True)]",
    )

    protocollo_id = fields.Many2one(
        string="Protocol",
        comodel_name="sd.protocollo.protocollo",
        domain=lambda self: "[('state','=', 'bozza'),('protocollatore_id','=', %s)]" % self.env.uid
    )

    riservato = fields.Boolean(
        string="Riservato"
    )

    field_selection_documenti_invisible = fields.Boolean(
        string="selection_documenti_invisible",
        compute="_compute_field_selection_documenti_invisible",
        default=False
    )

    data_ricezione = fields.Datetime(
        string="Data Ricezione"
    )


    @api.model
    def default_get(self, fields_list):
        protocollo_obj = self.env["sd.protocollo.protocollo"]
        res = super(DocumentoWizardCreaBozzaProtocollo, self).default_get(fields_list)
        documento_ids = self.env.context.get("documento_ids", False)
        if documento_ids:
            res["crea_bozza"] = True
            res["registro_id"] = protocollo_obj._default_registro_id()
            res["protocollatore_ufficio_id"] = protocollo_obj._default_protocollatore_ufficio_id()
            res["mezzo_trasmissione_id"] = False
            res["user_tipologia_protocollo"] = False
            res["protocollo_id"] = False
            res["company_id_invisible"] = protocollo_obj._default_company_id_readonly()
            res["registro_id_readonly"] = protocollo_obj._default_registro_id_readonly()
            res["selection_documenti"] = str(documento_ids[0])
            res["riservato"] = False
        return res

    @api.onchange("protocollatore_ufficio_id")
    def onchange_protocollatore_ufficio_id(self):
        protocollo_obj = self.env["sd.protocollo.protocollo"]
        self.registro_id = protocollo_obj._default_registro_id()
        self.registro_id_readonly = protocollo_obj._default_registro_id_readonly()

    @api.onchange("mezzo_trasmissione_id", "user_tipologia_protocollo")
    def _default_data_ricezione(self):
        self.ensure_one()
        if not self.data_ricezione and self.user_tipologia_protocollo == "ingresso":
            self.data_ricezione = Datetime.now()

        if self.user_tipologia_protocollo != "ingresso":
            self.data_ricezione = False

    @api.depends("user_tipologia_protocollo")
    def _compute_mezzo_trasmissione_id_invisible(self):
        self.ensure_one()

        if not self.user_tipologia_protocollo:
            self.mezzo_trasmissione_id_invisible = True
            return

        if self.user_tipologia_protocollo not in ["uscita", "ingresso"]:
            self.mezzo_trasmissione_id_invisible = True
            return

        if not self.company_id:
            self.mezzo_trasmissione_id_invisible = True
            return

        self.mezzo_trasmissione_id_invisible = False

    @api.onchange("crea_bozza", "protocollo_id")
    def _compute_field_selection_documenti_invisible(self):
        for rec in self:
            documento_ids = self.env.context.get("documento_ids", False)
            field_selection_documenti_invisible = False
            if (not rec.crea_bozza and rec.protocollo_id and rec.protocollo_id.documento_id.content) or len(documento_ids) == 1:
                field_selection_documenti_invisible = True
            rec.field_selection_documenti_invisible = field_selection_documenti_invisible

    @api.onchange("protocollo_id")
    def _onchange_protocollo_id(self):
        self.ensure_one()
        if self.protocollo_id and self.protocollo_id.documento_id.content:
            self.selection_documenti = False

    def _get_allegati_list(self, main_document):
        return [int(x[0]) for x in self._get_documenti_protocollo_selection() if int(x[0]) != main_document]

    def _get_values_protocollo(self, main_document_id, allegati_list):
        protocollo_obj = self.env["sd.protocollo.protocollo"]
        archivio_id = protocollo_obj._default_archivio_id()
        if not archivio_id:
            raise UserError(_("You need to configure the archive"))

        self._get_clear_document(main_document_id)

        return {
            "company_id": self.company_id.id,
            "documento_id": main_document_id,
            "riservato": self.riservato,
            "allegato_ids": [(6, 0, allegati_list)],
            "protocollatore_id": self.env.user.id,
            "registro_id": self.registro_id.id,
            "mezzo_trasmissione_id": self.mezzo_trasmissione_id.id if self.mezzo_trasmissione_id else False,
            "tipologia_protocollo": self.user_tipologia_protocollo,
            "protocollatore_ufficio_id": self.protocollatore_ufficio_id.id,
            "archivio_id": archivio_id,
            "data_ricezione": self.data_ricezione if self.data_ricezione else False
        }

    def _get_clear_document(self, documento_id):
        document_obj = self.env["sd.dms.document"]

        if self.user_tipologia_protocollo == "uscita":
            documento = document_obj.browse(documento_id)
            documento.sender_ids = [(6, 0, [])]

        if self.user_tipologia_protocollo == "ingresso":
            documento = document_obj.browse(documento_id)
            documento.recipient_ids = [(6, 0, [])]

    def crea_protocollo(self):
        document_obj = self.env["sd.dms.document"]
        main_document_id = int(self.selection_documenti) if self.selection_documenti else False
        allegati_list = self._get_allegati_list(main_document_id)
        protocollo_obj = self.env["sd.protocollo.protocollo"]
        protocollo_values = self._get_values_protocollo(main_document_id, allegati_list)
        protocollo = protocollo_obj.with_context(
            from_module=_("Documents")).create(protocollo_values)

        documento = document_obj.browse(main_document_id)
        documento.storico_aggiunta_documento_a_bozza(protocollo.numero_protocollo)
        allegato_list = []
        if allegati_list:
            allegati = document_obj.search([("id", "in", allegati_list)])
            for allegato in allegati:
                allegato_list.append(allegato.filename)
                allegato.storico_aggiunta_allegato_a_bozza(protocollo.numero_protocollo)
        if allegato_list:
            protocollo.storico_bozza_aggiunta_allegato_da_documenti(allegato_list)
        protocollo._default_mittente_interno_id()
        return {
            "name": "Protocollo",
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "sd.protocollo.protocollo",
            "res_id": protocollo.id,
            "target": "current",
            "context": self.env.context
        }

    def aggiungi_a_protocollo(self):
        protocollo_values = {}
        document_obj = self.env["sd.dms.document"]
        documento_id = int(self.selection_documenti) if self.selection_documenti else False
        allegati_list = [(4, x) for x in self._get_allegati_list(documento_id)]
        documento = False
        # inserimento del riferimento del protocollo al nuovo documento/allegati
        if documento_id:
            documento = self.protocollo_id.documento_id
            protocollo_values.update({"documento_id": documento_id})
            new_document = document_obj.browse(documento_id)
            new_document.storico_aggiunta_documento_a_bozza(self.protocollo_id.numero_protocollo)
        if allegati_list:
            protocollo_values.update({"allegato_ids": allegati_list})
            allegati = document_obj.search([("id", "in", self._get_allegati_list(documento_id))])
            for allegato in allegati:
                allegato.storico_aggiunta_allegato_a_bozza(self.protocollo_id.numero_protocollo)

        self.protocollo_id.write(protocollo_values)
        # ricerca delle acl esistenti
        acl_list = self.env["sd.dms.document.acl"].search([("protocollo_id", "=", self.protocollo_id.id)])
        # aggiunta delle acl al nuovo documento
        if documento_id:
            for acl in acl_list:
                acl.write({"document_ids": [(4, documento_id)]})
        if allegati_list:
            for acl in acl_list:
                acl.write({"document_ids": allegati_list})
        # eliminazione del vecchio documento senza file
        if documento:
            documento.unlink()
        # restituzione della vista del protocollo
        return {
            "name": "Protocollo",
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "sd.protocollo.protocollo",
            "res_id": self.protocollo_id.id,
            "target": "current",
            "context": self.env.context
        }