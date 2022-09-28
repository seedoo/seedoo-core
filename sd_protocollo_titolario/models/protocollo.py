from odoo import models, fields, api


class Protocollo(models.Model):
    _inherit = "sd.protocollo.protocollo"

    documento_id_voce_titolario_id = fields.Many2one(
        string="Voce Titolario",
        related="documento_id.voce_titolario_id",
        readonly=False
    )

    def _get_documento_values(self, protocollo):
        vals = super(Protocollo, self)._get_documento_values(protocollo)
        voce_titolario = None
        if protocollo.documento_id_voce_titolario_id:
            voce_titolario = protocollo.documento_id_voce_titolario_id
        if not voce_titolario:
            return vals
        vals.update({
            "voce_titolario_id": voce_titolario.id,
            "voce_titolario_name": voce_titolario.path_name
        })
        return vals

    def _check_company_protocollo(self, protocollo):
        check_company = super(Protocollo, self)._check_company_protocollo(protocollo)
        if not check_company:

            # Controllo company del titolario del documento sia uguale a quella selezionata
            if protocollo.documento_id_voce_titolario_id and protocollo.documento_id_voce_titolario_id.titolario_company_id != protocollo.company_id:
                return "Verificare la company della classificazione del documento:\nla company della classificazione " \
                       "deve essere uguale a quella del protocollo "

            # Controllo che la company del titolare degli allegati sia la stessa del documento
            for allegati in protocollo.allegato_ids:
                if allegati.voce_titolario_id:
                    if allegati.voce_titolario_id.titolario_company_id != protocollo.company_id:
                        return "Verificare la company della classificazione degli allegati:\nla company della  " \
                               "classificazione deve essere uguale a quella del protocollo "
        return check_company

    @api.onchange("documento_id_voce_titolario_id")
    def _onchange_voce_titolario_id(self):
        self.ensure_one()
        if self.documento_id_voce_titolario_id:
            protocollo = self.browse(self.id.origin)
            if self.documento_id_voce_titolario_id.id != protocollo.documento_id_voce_titolario_id.id:
                # se non ci sono assegnatari default configurati non mostra lo step di aggiunta/sostituzione assegnatariz\
                if self._get_classificazione_assegnatario_default_ids(self.documento_id_voce_titolario_id):
                    # Recupero della vecchia voce di titolario che verrà passata nel context
                    type = "action,sd_protocollo_titolario.action_sd_protocollo_wizard_protocollo_classifica_step2_assegna"
                    return {
                        "warning": {
                            "type": type
                        }
                    }

    @api.onchange("documento_id_document_type_id")
    def _onchange_documento_id_document_type_id(self):
        if self.documento_id_document_type_id:
            self.documento_id_voce_titolario_required = True

    # TODO: aggiungere campo parent_active al modello della voce organigramma e inserire le condizioni nel if-else
    def get_assegnatario_default_ids(self, protocollo, voce_titolario):
        assegnatario_default_ids = []
        if not voce_titolario:
            return assegnatario_default_ids
        # voce_titolario.assegnatario_default_in.parent_active and \
        if protocollo.tipologia_protocollo == "ingresso" and \
                voce_titolario.assegnatario_default_in and \
                voce_titolario.assegnatario_default_in.active and \
                not self.skip_assegnatario_default(protocollo, voce_titolario, voce_titolario.assegnatario_default_in):
            assegnatario_default_ids.append(voce_titolario.assegnatario_default_in.id)
        # voce_titolario.assegnatario_default_out.parent_active and \
        elif protocollo.tipologia_protocollo == "uscita" and \
                voce_titolario.assegnatario_default_out and \
                voce_titolario.assegnatario_default_out.active and \
                not self.skip_assegnatario_default(protocollo, voce_titolario, voce_titolario.assegnatario_default_out):
            assegnatario_default_ids.append(voce_titolario.assegnatario_default_out.id)
        return assegnatario_default_ids

    def skip_assegnatario_default(self, protocollo, voce_titolario, assegnatario_default):
        # se il protocollo è registrato e possiede già degli assegnatari per competenza allora deve mostrare
        # l'assegnatario anche se coincide con l'ufficio del protocollatore
        if protocollo.data_registrazione and protocollo.assegnazione_competenza_ids:
            return False
        # se il protocollo non è registrato o non possiede già degli assegnatari per competenza allora deve mostrare
        # l'assegnatario solo se è diverso dall'ufficio del protocollatore
        if voce_titolario.assegnatario_default_skip and \
                protocollo.protocollatore_ufficio_id and \
                protocollo.protocollatore_ufficio_id.id == assegnatario_default.ufficio_id.id:
            return True
        return False

    def _get_classificazione_assegnatario_default_ids(self, voce_titolario, return_ids=False):
        config_obj = self.env["ir.config_parameter"].sudo()
        sostituisci_assegnatari = config_obj.sudo().get_param("sd_protocollo.sostituisci_assegnatari", False)
        # il messaggio di aggiunta/sostituzione assegnatari default deve essere mostrato sempre quando il protocollo non
        # è stato registrato oppure quando il protocollo è registrato e il parametro di sostituzione assegnatari è
        # abilitato
        if not self.data_registrazione or (self.data_registrazione and sostituisci_assegnatari):
            assegnatario_list = self.get_assegnatario_default_ids(self, voce_titolario)
            if assegnatario_list:
                return assegnatario_list if return_ids else True
        return False

    def write(self, vals):
        # Casistica in cui non si passa dal wizard triggherato via onchange, old_voce_titolario è presente nel context
        # solo quando inserito via button di classificazione
        if not self.env.context.get("storico_classifica", False):
            if "documento_id_voce_titolario_id" in vals and vals["documento_id_voce_titolario_id"]:
                # Recupero della vecchia voce di titolario
                old_voce_titolario = self.documento_id_voce_titolario_id
                res = super(Protocollo, self).write(vals)
                if old_voce_titolario.id != self.documento_id_voce_titolario_id.id:
                    self.classifica_documento(self.documento_id_voce_titolario_id, old_voce_titolario)
                # Aggiunta della classificazione del documento principale per tutti gli allegati che ne sono sprovvisti
                for allegato in self.allegato_ids:
                    if not allegato.voce_titolario_id or allegato.voce_titolario_id.id == old_voce_titolario.id:
                        allegato.write({"voce_titolario_id": self.documento_id_voce_titolario_id.id})
                return res
        return super(Protocollo, self).write(vals)

    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        default["documento_id_voce_titolario_id"] = self.documento_id_voce_titolario_id.id
        return super(Protocollo, self).copy(default=default)