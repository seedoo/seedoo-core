from odoo import models, fields, api


class WizardProtocolloClassificaStep1(models.TransientModel):
    _name = "sd.protocollo.wizard.protocollo.classifica.step1"
    _description = "Wizard Protocollo Classifica Step1"

    protocollo_company_id = fields.Many2one(
        string="Protocollo Company",
        comodel_name="res.company",
        readonly=True
    )

    voce_titolario_id = fields.Many2one(
        string="Classificazione",
        comodel_name="sd.dms.titolario.voce.titolario",
        domain="[('titolario_id.active','=',True), ('titolario_id.state','=',True), ('parent_active', '=', True), ('titolario_company_id','=',protocollo_company_id )]"
    )

    voci_titolario_non_presenti = fields.Boolean(
        string="Voce titolari non presenti",
        readonly=True
    )

    voce_titolario_required = fields.Boolean(
        string="Voce titolario required",
        readonly=True
    )

    @api.model
    def default_get(self, fields_list):
        protocollo_obj = self.env["sd.protocollo.protocollo"]
        voce_titolario_obj = self.env["sd.dms.titolario.voce.titolario"]
        res = super(WizardProtocolloClassificaStep1, self).default_get(fields_list)

        protocollo_id = self.env.context.get("protocollo_id", False)
        protocollo = protocollo_obj.browse(protocollo_id)
        documento_id = protocollo.documento_id
        count = voce_titolario_obj.search_count([("parent_active", "=", True)])

        res["voce_titolario_id"] = documento_id.voce_titolario_id if documento_id.voce_titolario_id else False
        res["voce_titolario_required"] = True if protocollo.data_registrazione else False
        res["voci_titolario_non_presenti"] = False if count>0 else True
        res["protocollo_company_id"] = protocollo.company_id.id
        return res

    def action_salva(self):
        self.ensure_one()
        protocollo_id = self.env.context.get("protocollo_id")
        protocollo_obj = self.env["sd.protocollo.protocollo"]
        protocollo = protocollo_obj.browse(protocollo_id)
        assegnatario_default_ids = protocollo._get_classificazione_assegnatario_default_ids(self.voce_titolario_id, True)
        old_voce_titolario = protocollo.documento_id_voce_titolario_id
        # se non ci sono assegnatari default configurati non mostra lo step di aggiunta/sostituzione assegnatari
        if assegnatario_default_ids:
            context = dict(
                self.env.context,
                voce_titolario_id=self.voce_titolario_id.id,
                old_voce_titolario=old_voce_titolario.id,
                storico_classifica=True
            )
            return {
                "name": self.env.context.get("wizard_label"),
                "type": "ir.actions.act_window",
                "res_model": "sd.protocollo.wizard.protocollo.classifica.step2",
                "view_mode": "form",
                "target": "new",
                "context": context
            }
        protocollo.documento_id_voce_titolario_id = self.voce_titolario_id.id



class WizardProtocolloClassificaStep2(models.TransientModel):
    _name = "sd.protocollo.wizard.protocollo.classifica.step2"
    _description = "Wizard Protocollo Classifica Step2"

    assegnatari_default = fields.Text(
        string="Assegnatario Default"
    )

    messaggio_sostituzione_invisible = fields.Boolean(
        string="Messaggio Sostituzione Invisibile",
        readonly=True,
        default=True
    )

    @api.model
    def default_get(self, fields_list):
        res = super(WizardProtocolloClassificaStep2, self).default_get(fields_list)
        protocollo = self.env["sd.protocollo.protocollo"].browse(self.env.context.get("protocollo_id"))
        voce_organigramma_obj = self.env["fl.set.voce.organigramma"]
        voce_titolario = self.env["sd.dms.titolario.voce.titolario"].browse(self.env.context.get("voce_titolario_id"))
        assegnatario_default_ids = protocollo.get_assegnatario_default_ids(protocollo, voce_titolario)
        assegnatario_default_list = voce_organigramma_obj.search_read([
            ("id", "in", assegnatario_default_ids)
        ], ["nome_completo"])
        assegnatario_nome_completo_list = []
        for assegnatario_default in assegnatario_default_list:
            assegnatario_nome_completo_list.append(assegnatario_default["nome_completo"])
        assegnatari_default = "\n".join(assegnatario_nome_completo_list)
        res["assegnatari_default"] = assegnatari_default

        # se il protocollo è registrato e ha già degli assegnatari per competenza, allora deve essere mostrato il
        # messaggio di aggiunta assegnatari e non quello di sostituzione
        if protocollo.data_registrazione and protocollo.assegnazione_competenza_ids:
            res["messaggio_sostituzione_invisible"] = False

        return res

    def salva_competenza(self, protocollo, assegnatario_ids, assegnatore_id, assegnatore_ufficio_id):
        assegnatario_to_replace_ids = []
        for a in protocollo.assegnazione_competenza_ids:
            assegnatario_to_replace_ids.append(a.assegnatario_id.id)
        before = ", ".join([a.assegnatario_id.nome for a in protocollo.assegnazione_competenza_ids])
        protocollo.salva_assegnazione_competenza(
            assegnatario_ids,
            assegnatore_id,
            assegnatore_ufficio_id,
            assegnatario_to_replace_ids
        )
        after = ", ".join([a.assegnatario_id.nome for a in protocollo.assegnazione_competenza_ids])
        return before, after

    def action_yes(self):
        self.ensure_one()
        protocollo = self.env["sd.protocollo.protocollo"].browse(self.env.context.get("protocollo_id"))
        new_voce_titolario = self.env["sd.dms.titolario.voce.titolario"].browse(self.env.context.get("voce_titolario_id"))
        assegnatario_default_ids = protocollo.get_assegnatario_default_ids(protocollo, new_voce_titolario)
        before_com, after_com = self.salva_competenza(
            protocollo,
            assegnatario_default_ids,
            self.env.uid,
            protocollo.protocollatore_ufficio_id.id
        )
        # Passato da Step1 e non dal wizard dell'onchange
        old_voce_titolario = self.env.context.get("old_voce_titolario", False)
        storico_classifica = self.env.context.get("storico_classifica", False)
        if storico_classifica:
            # Storico classificazione
            protocollo.documento_id_voce_titolario_id = new_voce_titolario.id
            protocollo.classifica_documento(new_voce_titolario, old_voce_titolario)
        # Storico Assegnazione
        protocollo.classifica_documento(False, False, before_com, after_com)

    def action_no(self):
        protocollo = self.env["sd.protocollo.protocollo"].browse(self.env.context.get("protocollo_id"))
        new_voce_titolario = self.env["sd.dms.titolario.voce.titolario"].browse(self.env.context.get("voce_titolario_id"))
        old_voce_titolario = self.env.context.get("old_voce_titolario", False)
        storico_classifica = self.env.context.get("storico_classifica", False)

        # Passato da Step1 e non dal wizard dell'onchange
        if storico_classifica:
            protocollo.documento_id_voce_titolario_id = new_voce_titolario.id
            protocollo.classifica_documento(new_voce_titolario, old_voce_titolario)
