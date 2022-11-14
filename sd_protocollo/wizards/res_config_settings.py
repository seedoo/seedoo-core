from odoo.addons.base.models.res_partner import _tzs
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

SELECTION_ASSEGNAZIONE = [
    ("tutti", "Uffici e Utenti"),
    ("uffici", "Solo Uffici")
]

SELECTION_PRIMA_ASSEGNAZIONE = [
    ("tutti", "Uffici e Utenti"),
    ("uffici", "Solo Uffici"),
    ("utenti", "Solo Utenti")
]


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # ----------------------------------------------------------
    # Generale
    # ----------------------------------------------------------

    # genera_segnatura = fields.Boolean(
    #     string="Genera segnatura in PDF post-registrazione",
    #     config_parameter="sd_protocollo.genera_segnatura"
    # )

    rinomina_documento_allegati = fields.Boolean(
        string="Rinomina documento principale e allegati",
        config_parameter="sd_protocollo.rinomina_documento_allegati"
    )

    assegnazione = fields.Selection(
        string="Assegnazione",
        selection=SELECTION_ASSEGNAZIONE,
        config_parameter="sd_protocollo.assegnazione"
    )

    prima_assegnazione = fields.Selection(
        string="Prima assegnazione",
        selection=SELECTION_PRIMA_ASSEGNAZIONE,
        config_parameter="sd_protocollo.prima_assegnazione"
    )

    abilita_assegnazione_stesso_utente_ufficio = fields.Boolean(
        string="Abilita assegnazione alla stesso utente/ufficio per competenza e conoscenza",
        config_parameter="sd_protocollo.abilita_assegnazione_stesso_utente_ufficio"
    )

    abilita_lettura_assegnazione_competenza = fields.Boolean(
        string="Abilita lettura assegnazione competenza",
        config_parameter="sd_protocollo.abilita_lettura_assegnazione_competenza"
    )

    aggiungi_allegati_post_registrazione = fields.Boolean(
        string="Aggiungi allegato Post-Registrazione",
        config_parameter="sd_protocollo.aggiungi_allegati_post_registrazione"
    )

    abilita_aggiungi_assegnatari_cc = fields.Boolean(
        string="Abilita button \"Aggiungi assegnatari per conoscenza\"",
        config_parameter="sd_protocollo.abilita_aggiungi_assegnatari_cc"
    )

    visualizza_motivazione_completa_lavorazione = fields.Boolean(
        string="Visualizza il campo \"Motivazione\" in completa lavorazione",
        config_parameter="sd_protocollo.visualizza_motivazione_completa_lavorazione"
    )

    registro_logo_id = fields.Many2one(
        string="Logo Registro Giornaliero",
        comodel_name="ir.attachment",
        config_parameter="sd_protocollo.registro_logo_id",
        readonly=True
    )

    registro_logo_fname = fields.Char(
        string="File Name"
    )

    registro_logo_datas = fields.Binary(
        string="Logo Registro Attachment",
        compute="_compute_logo_datas",
        inverse="_inverse_registro_logo_datas",
        readonly=False
    )

    # ----------------------------------------------------------
    # Campi obbligatori per Registrazione Protocollo
    # ----------------------------------------------------------

    required_assegnatari_competenza_uffici = fields.Boolean(
        string="Uffici assegnatari per competenza",
        config_parameter="sd_protocollo.required_assegnatari_competenza_uffici"
    )

    required_assegnatari_competenza_dipendenti = fields.Boolean(
        string="Dipendenti assegnatari per competenza",
        config_parameter="sd_protocollo.required_assegnatari_competenza_dipendenti"
    )

    required_assegnatari_conoscenza_uffici = fields.Boolean(
        string="Uffici assegnatari per conoscenza",
        config_parameter="sd_protocollo.required_assegnatari_conoscenza_uffici"
    )

    required_assegnatari_conoscenza_dipendenti = fields.Boolean(
        string="Dipendenti assegnatari per conoscenza",
        config_parameter="sd_protocollo.required_assegnatari_conoscenza_dipendenti"
    )

    required_assegnatari_competenza_uffici_senza_doc = fields.Boolean(
        string="Uffici assegnatari per competenza (senza documento)",
        config_parameter="sd_protocollo.required_assegnatari_competenza_uffici_senza_doc"
    )

    required_assegnatari_competenza_dipendenti_senza_doc = fields.Boolean(
        string="Dipendenti assegnatari per competenza (senza documento)",
        config_parameter="sd_protocollo.required_assegnatari_competenza_dipendenti_senza_doc"
    )

    required_assegnatari_conoscenza_uffici_senza_doc = fields.Boolean(
        string="Uffici assegnatari per conoscenza (senza documento)",
        config_parameter="sd_protocollo.required_assegnatari_conoscenza_uffici_senza_doc"
    )

    required_assegnatari_conoscenza_dipendenti_senza_doc = fields.Boolean(
        string="Dipendenti assegnatari per conoscenza (senza documento)",
        config_parameter="sd_protocollo.required_assegnatari_conoscenza_dipendenti_senza_doc"
    )

    required_data_ricezione = fields.Boolean(
        string="Data ricezione documento",
        config_parameter="sd_protocollo.required_data_ricezione"
    )

    # ----------------------------------------------------------
    # Interoperabilità
    # ----------------------------------------------------------

    module_fl_protocollo_segnatura_xml = fields.Boolean(
        string="Segnatura.xml"
    )

    module_fl_protocollo_interoperabilita = fields.Boolean(
        string="Messaggi di ritorno"
    )

    genera_segnatura_append_solo_pdf_firmati = fields.Boolean(
        string="Segnatura append solo su PDF firmati",
        config_parameter="sd_protocollo.genera_segnatura_append_solo_pdf_firmati"
    )

    genera_segnatura_allegati = fields.Boolean(
        string="Segnatura allegati",
        config_parameter="sd_protocollo.genera_segnatura_allegati"
    )

    genera_segnatura_ogni_pagina = fields.Boolean(
        string="Segnatura su tutte le pagine",
        config_parameter="sd_protocollo.genera_segnatura_ogni_pagina"
    )

    codice_ufficio_in_segnatura = fields.Boolean(
        string="Codice ufficio",
        config_parameter="fl_protocollo_segnatura_pdf.codice_ufficio_in_segnatura"
    )

    # ----------------------------------------------------------
    # Dashboard
    # ----------------------------------------------------------

    assegnato_a_me_active = fields.Boolean(
        string="Visualizza box \"Assegnati a me\"",
        config_parameter="sd_protocollo.assegnato_a_me_active"
    )

    assegnato_a_mio_ufficio_active = fields.Boolean(
        string="Visualizza box \"Assegnati al mio ufficio\"",
        config_parameter="sd_protocollo.assegnato_a_mio_ufficio_active"
    )

    assegnato_a_me_competenza_active = fields.Boolean(
        string="Visualizza box \"Assegnati a me per competenza\"",
        config_parameter="sd_protocollo.assegnato_a_me_competenza_active"
    )

    assegnato_a_mio_ufficio_competenza_active = fields.Boolean(
        string="Visualizza box \"Assegnati al mio ufficio per competenza\"",
        config_parameter="sd_protocollo.assegnato_a_mio_ufficio_competenza_active"
    )

    assegnato_cc_active = fields.Boolean(
        string="Visualizza box \"Assegnati per conoscenza\"",
        config_parameter="sd_protocollo.assegnato_cc_active"
    )

    assegnato_da_me_active = fields.Boolean(
        string="Visualizza box \"Assegnati da me\"",
        config_parameter="sd_protocollo.assegnato_da_me_active"
    )

    da_assegnare_active = fields.Boolean(
        string="Visualizza box \"Da assegnare\"",
        config_parameter="sd_protocollo.da_assegnare_active"
    )

    # ----------------------------------------------------------
    # Configurazione Etichetta
    # ----------------------------------------------------------

    etichetta_altezza = fields.Integer(
        string="Altezza",
        config_parameter="sd_protocollo.etichetta_altezza"
    )

    etichetta_larghezza = fields.Integer(
        string="Larghezza",
        config_parameter="sd_protocollo.etichetta_larghezza"
    )

    etichetta_logo_id = fields.Many2one(
        string="Logo",
        comodel_name="ir.attachment",
        config_parameter="sd_protocollo.etichetta_logo_id",
        readonly=True
    )

    etichetta_logo_fname = fields.Char(
        string="File Name "
    )

    etichetta_logo_datas = fields.Binary(
        string="Logo Etichetta Attachment",
        compute="_compute_logo_datas",
        inverse="_inverse_etichetta_logo_datas",
        readonly=False
    )

    # ----------------------------------------------------------
    # Segnatura PDF
    # ----------------------------------------------------------

    segnatura_pdf_protocollo_ingresso = fields.Boolean(
        string="Segnatura PDF protocollazioni ingresso",
        config_parameter="sd_protocollo.segnatura_pdf_protocollo_ingresso",
    )

    segnatura_pdf_protocollo_uscita = fields.Boolean(
        string="Segnatura PDF protocollazioni uscita",
        config_parameter="sd_protocollo.segnatura_pdf_protocollo_uscita",
    )

    # ----------------------------------------------------------
    # Installazione moduli Enterprise e Aggiuntivi
    # ----------------------------------------------------------

    module_fl_protocollo_mezzo_trasmissione_misto = fields.Boolean(
        string="Invio misto"
    )

    module_fl_protocollo_gruppi_destinatari = fields.Boolean(
        string="Aggiunta destinatari da un gruppo"
    )

    module_sd_protocollo_pec = fields.Boolean(
        string="Integrazione PEC"
    )

    module_fl_protocollo_email = fields.Boolean(
        string="Integrazione e-mail"
    )

    module_sd_protocollo_aoo = fields.Boolean(
        string="Gestione AOO "
    )

    module_sd_protocollo_titolario = fields.Boolean(
        string="Classifica tramite titolario "
    )

    module_sd_protocollo_fascicolo = fields.Boolean(
        string="Fascicola documenti"
    )

    module_sd_protocollo_conservazione_rgp = fields.Boolean(
        string="Conservazione del registro giornaliero"
    )

    module_fl_protocollo_invio_unicast = fields.Boolean(
        string="Invio unicast"
    )

    module_fl_protocollo_interno = fields.Boolean(
        string="Protocollazione interna"
    )

    module_fl_protocollo_segnatura_pdf = fields.Boolean(
        string="Extra segnatura PDF"
    )

    module_fl_protocollo_preview_sidebox = fields.Boolean(
        string="Box laterale anteprima"
    )

    module_fl_protocollo_dms_folder = fields.Boolean(
        string="Struttura Cartelle"
    )

    module_fl_protocollo_smistamento = fields.Boolean(
        string="Switching"
    )

    module_fl_protocollo_riferimento = fields.Boolean(
        string="Reference"
    )

    module_fl_protocollo_registro = fields.Boolean(
        string="Protocol register"
    )

    module_fl_protocollo_ricevute = fields.Boolean(
        string="Receipts"
    )

    module_fl_protocollo_importer = fields.Boolean(
        string="Scans"
    )

    module_fl_protocollo_archivio = fields.Boolean(
        string="Archiving"
    )

    module_fl_protocollo_notifiche = fields.Boolean(
        string="Notifiche assegnazione protocollo"
    )

    # ----------------------------------------------------------
    # Timezone
    # ----------------------------------------------------------

    def _get_timezone(self):
        return _tzs

    timezone = fields.Selection(
        selection=_get_timezone,
        string="Fuso orario",
        default=lambda self: self._context.get("tz"),
        config_parameter="sd_protocollo.timezone",
    )

    @api.model
    def set_values(self):
        if self.genera_segnatura_allegati or self.genera_segnatura_ogni_pagina or self.codice_ufficio_in_segnatura:
            self.module_fl_protocollo_segnatura_pdf = True
        return super(ResConfigSettings, self).set_values()

    @api.depends("etichetta_logo_id", "registro_logo_id")
    def _compute_logo_datas(self):
        for rec in self:
            if rec.etichetta_logo_id:
                rec.etichetta_logo_datas = rec.etichetta_logo_id.datas
            if rec.registro_logo_id:
                rec.registro_logo_datas = rec.registro_logo_id.datas

    def _inverse_etichetta_logo_datas(self):
        for rec in self:
            ir_config_parameter = self.env["ir.config_parameter"].sudo()
            if self.etichetta_logo_datas:
                config_etichetta_logo_id = ir_config_parameter.get_param("sd_protocollo.etichetta_logo_id")
                attachment = self._create_attachment_for_binary_field(
                    config_param=config_etichetta_logo_id,
                    name=self.etichetta_logo_fname,
                    datas=self.etichetta_logo_datas,
                    store_fname=self.etichetta_logo_fname
                )
                if attachment:
                    rec.etichetta_logo_id = attachment.id

    def _inverse_registro_logo_datas(self):
        for rec in self:
            ir_config_parameter = self.env["ir.config_parameter"].sudo()
            if self.registro_logo_datas:
                config_registro_logo_id = ir_config_parameter.get_param("sd_protocollo.registro_logo_id")
                attachment = self._create_attachment_for_binary_field(
                    config_param=config_registro_logo_id,
                    name=self.registro_logo_fname,
                    datas=self.registro_logo_datas,
                    store_fname=self.registro_logo_fname
                )
                if attachment:
                    rec.registro_logo_id = attachment.id

    def _create_attachment_for_binary_field(self, config_param, name, datas, store_fname):
        ir_attachment = self.env["ir.attachment"].sudo()

        attachment_vals = {
            "name": name,
            "datas": datas,
            "store_fname": store_fname
        }

        if config_param:
            attachment = ir_attachment.browse(int(config_param))
            if attachment.datas != datas:
                attachment.write(attachment_vals)
                return False
        else:
            new_attachment = ir_attachment.create(attachment_vals)
            return new_attachment

    @api.constrains("module_fl_protocollo_interoperabilita")
    def _check_codice_ipa(self):
        if self.module_fl_protocollo_interoperabilita:
            if not self.env.company.codice_ipa:
                raise ValidationError(_("IPA code not completed! Before installing this module, add the ipa code to your company."))
