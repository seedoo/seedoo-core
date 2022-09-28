from odoo import models, fields, _, api
import datetime

from odoo.exceptions import UserError, ValidationError


class Fascicolo(models.Model):
    _inherit = "sd.fascicolo.fascicolo"

    def apri_fascicolo(self):
        self.ensure_one()
        if self.parent_id and self.parent_id.state == "bozza":
            raise ValidationError(_("The dossier cannot be opened because parent is in draft state!"))
        self.state = "aperto"
        self.data_apertura = datetime.datetime.now()
        self.anno = self.data_apertura.strftime("%Y")
        self.storico_apertura_fascicolo()

    def chiudi_fascicolo(self):
        self.ensure_one()
        self.state = "chiuso"
        self.data_chiusura = datetime.datetime.now()
        self.storico_chiusura_fascicolo()

    def protocollo_lista_sottofascicoli_action(self):
        self.ensure_one()
        context = dict(
            self.env.context,
            default_tipologia="sottofascicolo",
            default_parent_id=self.id
        )
        return {
            "name": "Sottofascicoli",
            "view_mode": "tree,form",
            "res_model": "sd.fascicolo.fascicolo",
            "type": "ir.actions.act_window",
            "domain": [
                ("parent_id", "=", self.id),
                ("tipologia", "=", "sottofascicolo")
            ],
            "context": context
        }

    def protocollo_lista_inserti_action(self):
        self.ensure_one()
        context = dict(
            self.env.context,
            default_tipologia="inserto",
            default_parent_id=self.id,
        )
        return {
            "name": "Inserti",
            "view_mode": "tree,form",
            "res_model": "sd.fascicolo.fascicolo",
            "type": "ir.actions.act_window",
            "domain": [
                ("parent_id", "=", self.id),
                ("tipologia", "=", "inserto")
            ],
            "context": context
        }


    def disassocia_fascicolo(self):
        self.ensure_one()
        documento_id = self.env.context.get("disassocia_fascicolo_documento_id", False)
        if not documento_id:
            return
        self.fascicolo_disassocia_documenti([documento_id])

    def action_show_documents(self):
        self.ensure_one()
        context = dict(self._context or {})
        context["default_fascicolo_ids"] = [(6, 0, self.ids)]
        context["disassocia_documento_fascicolo_id"] = self.id
        #TODO: gestire la creazione di un documento con associazione del fascicolo
        context["create"] = False
        return {
            "name": _("Documents"),
            "view_mode": "tree,form",
            "res_model": "sd.dms.document",
            "domain": [("fascicolo_ids", "=", self.id)],
            "type": "ir.actions.act_window",
            "target": "current",
            "context": context,
        }

    def fascicolo_aggiungi_documenti(self, documento_ids):
        if self.state == "aperto":
            self.write({"documento_ids": [(4, documento_id) for documento_id in documento_ids]})
            self.storico_aggiunta_documento(documento_ids)
        else:
            raise UserError("Non è possibile aggiungere documenti in quanto lo stato del fascicolo deve essere aperto")

    def fascicolo_disassocia_documenti(self, documento_ids):
        self.write({"documento_ids": [(3, documento_id) for documento_id in documento_ids]})
        self.storico_disassocia_documento(documento_ids)

    @api.model
    def fascicolo_salva_contatto(self, fascicolo_id, contact_id, vals, save=False):
        contact_obj = self.env["sd.dms.contact"]
        if fascicolo_id:
            fascicolo = self.browse(fascicolo_id)
            contact = contact_obj.create(vals)
            if self.env.context.get("from", False):
                fascicolo.write({self.env.context.get("from"): [(4, contact.id)]})
        elif contact_id:
            contact = contact_obj.browse(contact_id)
            contact.write(vals)
        if save:
            contact.create_partner_from_contact()
        return contact