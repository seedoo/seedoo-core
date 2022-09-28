# Copyright 2020-2022 Flosslab S.r.l.
# Copyright 2017-2019 MuK IT GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, fields, api, _
from odoo.exceptions import  ValidationError



class WizardDocumentAddContact(models.TransientModel):
    _inherit = "sd.dms.wizard.document.add.contact"

    def save_contact_action(self):
        fascicolo_id = self.env.context.get("fascicolo_id", False)
        contact_id = self.env.context.get("contact_id", False)
        if fascicolo_id:
            if self.env.context.get("from") == "amministrazione_titolare_ids" and self.company_subject_type != "pa":
                raise ValidationError(_("Administration owner can only be a company of type PA!"))
            if self.env.context.get("from") == "amministrazione_partecipante_ids" and self.company_subject_type != "pa":
                raise ValidationError(_("Participating Administration can only be a company of type PA!"))
            if self.env.context.get("from") == "rup_ids" and (self.company_type != "person" and not self.contact_pa_name):
                raise ValidationError(_("Single procedure manager can only be a person!"))
            return self.env["sd.fascicolo.fascicolo"].fascicolo_salva_contatto(
                fascicolo_id=fascicolo_id,
                contact_id=contact_id,
                vals=self._get_contact_vals(contact_id),
                save=self.save_partner
            )
        else:
            return super(WizardDocumentAddContact,self).save_contact_action()

