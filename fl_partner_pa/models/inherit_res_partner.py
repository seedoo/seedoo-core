from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

SELECTION_COMPANY_SUBJECT_TYPE = [
    ("private", "Private Company"),
    ("pa", "Public Administration"),
    ("gps", "Public Service Manager")
]

SELECTION_CONTACT_PA_TYPE = [
    ("aoo", "Homogeneous Organizational Area"),
    ("uo", "Organizational Unit")
]


class ResPartner(models.Model):
    _inherit = "res.partner"

    company_subject_type = fields.Selection(
        string="Company typology",
        selection=SELECTION_COMPANY_SUBJECT_TYPE
    )

    contact_pa_type = fields.Selection(
        string="Company PA typology",
        selection=SELECTION_CONTACT_PA_TYPE
    )

    parent_personal_id = fields.Many2one(
        string="Parent person",
        comodel_name="res.partner",
        compute="_compute_parent_id",
        inverse="_inverse_parent_id",
        readonly=False
    )

    display_name_html = fields.Html(
        string="Display name html",
        compute="_compute_display_name",
        store=True
    )

    parent_company_id = fields.Many2one(
        string="Parent company",
        comodel_name="res.partner",
        compute="_compute_parent_id",
        inverse="_inverse_parent_id",
        readonly=False
    )

    is_private_company = fields.Boolean(
        string="Is a private company",
        compute="_compute_company_values",
        store=True
    )

    is_pa = fields.Boolean(
        string="Is a PA/GPS",
        compute="_compute_company_values",
        store=True
    )

    is_amm = fields.Boolean(
        string="Is a PA",
        compute="_compute_company_values",
        store=True
    )

    is_gps = fields.Boolean(
        string="Is a GPS",
        compute="_compute_company_values",
        store=True
    )

    is_aoo = fields.Boolean(
        string="Is a AOO",
        compute="_compute_company_values",
        store=True
    )

    is_uo = fields.Boolean(
        string="Is a UO",
        compute="_compute_company_values",
        store=True
    )

    # Amministrazione

    amministrazione_id = fields.Many2one(
        string="PA / GPS",
        comodel_name="res.partner"
    )

    cod_amm = fields.Char(
        string="IPA code"
    )

    # Area Organizzativa Omogenea (AOO)

    aoo_id = fields.Many2one(
        string="Homogeneous Organizational Area",
        comodel_name="res.partner",
        domain=lambda self: self._get_domain_aoo_id()
    )

    aoo_ids = fields.One2many(
        string="AOO from (PA / GPS)",
        inverse_name="amministrazione_id",
        comodel_name="res.partner",
        domain=[("is_aoo", "=", True)]
    )

    cod_aoo = fields.Char(
        string="AOO code"
    )

    can_used_in_aoo = fields.Boolean(
        string="Can Used To Protocol",
        compute="_compute_can_used_in_aoo",
        search="_search_can_used_in_aoo"
    )

    # Unità Organizzativa (UO)

    uo_ids = fields.One2many(
        string="UO list (PA/GPS)",
        inverse_name="amministrazione_id",
        comodel_name="res.partner",
        domain=[("is_uo", "=", True)]
    )

    aoo_uo_ids = fields.One2many(
        string="UO list (AOO)",
        inverse_name="aoo_id",
        comodel_name="res.partner",
        domain=[("is_uo", "=", True)]
    )

    # Domicilio Digitale

    pa_digital_domicile_ids = fields.One2many(
        string="Digital domicile list (PA)",
        comodel_name="res.partner.digital.domicile",
        compute="_compute_pa_digital_domicile_ids",
        readonly=True
    )

    uo_digital_domicile_ids = fields.One2many(
        string="Digital domicile list (UO)",
        comodel_name="res.partner.digital.domicile",
        compute="_compute_uo_digital_domicile_ids",
        readonly=True
    )

    aoo_digital_domicile_ids = fields.One2many(
        string="Digital domicile list (AOO)",
        inverse_name="aoo_id",
        comodel_name="res.partner.digital.domicile"
    )

    # campo computed aggiunto solamente per mostrare la lista dei domicili digitali nella vista kanban in quanto odoo
    # non prevede l'utilizzo dei campi one2many all'interno della vista kanban: in futuro si potrebbe sostituire con
    # l'utilizzo di un modulo che effettui tale funzionalità o provare a usara un template
    digital_domicile_ids_html = fields.Char(
        string="Digital domicile list html",
        compute="_compute_digital_domicile_ids_html"
    )

    cod_ou = fields.Char(
        string="UO code"
    )

    parent_amm_name = fields.Char(
        string="Parent PA name",
        compute="_compute_parent_pa"
    )

    parent_gps_name = fields.Char(
        string="Parent GPS name",
        compute="_compute_parent_pa"
    )

    parent_aoo_name = fields.Char(
        string="Parent AOO name",
        compute="_compute_parent_pa"
    )

    parent_uo_name = fields.Char(
        string="Parent UO name",
        compute="_compute_parent_pa"
    )

    child_ids = fields.One2many(
        compute="_compute_child_ids",
        readonly=False
    )

    parent_child_aoo_id = fields.Many2one(
        string="Homogeneous Organizational Area",
        comodel_name="res.partner",
        compute="_compute_parent_id",
        inverse="_inverse_parent_child_id",
        readonly=False
    )

    parent_child_uo_id = fields.Many2one(
        string="Organizational Unit",
        comodel_name="res.partner",
        compute="_compute_parent_id",
        inverse="_inverse_parent_child_id"
    )

    email_address_ids = fields.One2many(
        string="Other e-mail PEC addresses",
        inverse_name="partner_id",
        comodel_name="res.partner.email.address"
    )

    # campo computed aggiunto solamente per mostrare la lista dei domicili digitali nella vista kanban in quanto odoo
    # non prevede l'utilizzo dei campi one2many all'interno della vista kanban: in futuro si potrebbe sostituire con
    # l'utilizzo di un modulo che effettui tale funzionalità o provare a usara un template
    email_address_ids_html = fields.Char(
        string="Other e-mail PEC addresses html",
        compute="_compute_email_address_ids_html"
    )

    def _get_domain_aoo_id(self):
        domain = [('is_aoo', '=', True)]
        if self.env.context.get("from_pa", False):
            domain.append(("amministrazione_id", "=", self.env.context.get("amministrazione_id")))
        return domain

    @api.depends("parent_id")
    def _compute_parent_id(self):
        for rec in self:
            rec.parent_company_id = rec.parent_id.id
            rec.parent_personal_id = rec.parent_id.id
            if rec.parent_id and rec.parent_id.is_aoo:
                rec.parent_child_aoo_id = rec.parent_id.id
                rec.parent_child_uo_id = False
            elif rec.parent_id and rec.parent_id.is_uo:
                rec.parent_child_aoo_id = rec.parent_id.aoo_id.id if rec.parent_id.aoo_id else False
                rec.parent_child_uo_id = rec.parent_id.id
            else:
                rec.parent_child_aoo_id = False
                rec.parent_child_uo_id = False

    def _inverse_parent_id(self):
        for rec in self:
            if rec.parent_company_id:
                rec.parent_id = rec.parent_company_id.id
            elif rec.parent_personal_id:
                rec.parent_id = rec.parent_personal_id.id
            else:
                rec.parent_id = False

    def _inverse_parent_child_id(self):
        for rec in self:
            if rec.parent_child_uo_id:
                rec.parent_id = rec.parent_child_uo_id.id
            elif rec.parent_child_aoo_id:
                rec.parent_id = rec.parent_child_aoo_id.id
            elif rec.parent_id and (rec.parent_id.is_uo or rec.parent_id.is_aoo or rec.parent_id.is_amm):
                rec.parent_id = rec.parent_id.id
            else:
                rec.parent_id = False

    @api.depends("company_subject_type", "contact_pa_type")
    def _compute_company_values(self):
        for rec in self:
            rec.is_private_company = rec.company_subject_type=="private" and rec.contact_pa_type!="uo"
            rec.is_pa = rec.company_subject_type in ["pa", "gps"]
            rec.is_amm = rec.company_subject_type=="pa" and not rec.contact_pa_type
            rec.is_gps = rec.company_subject_type=="gps" and not rec.contact_pa_type
            rec.is_aoo = rec.company_subject_type in ["pa", "gps"] and rec.contact_pa_type=="aoo"
            rec.is_uo = rec.company_subject_type in ["private", "pa", "gps"] and rec.contact_pa_type=="uo"

    @api.depends("aoo_ids", "aoo_ids.aoo_digital_domicile_ids")
    def _compute_pa_digital_domicile_ids(self):
        digital_domicile_obj = self.env["res.partner.digital.domicile"]
        for rec in self:
            if not rec.is_amm and not rec.is_gps:
                rec.pa_digital_domicile_ids = [(6, 0, [])]
                return
            digital_domicile_ids = digital_domicile_obj.search([ ("aoo_id", "in", rec.aoo_ids.ids)]).ids
            rec.pa_digital_domicile_ids = [(6, 0, digital_domicile_ids)]

    @api.depends("aoo_id", "aoo_id.aoo_digital_domicile_ids")
    def _compute_uo_digital_domicile_ids(self):
        digital_domicile_obj = self.env["res.partner.digital.domicile"]
        for rec in self:
            if not rec.is_uo:
                rec.uo_digital_domicile_ids = [(6, 0, [])]
                return
            digital_domicile_ids = digital_domicile_obj.search([("aoo_id", "in", [rec.aoo_id.id])]).ids if rec.aoo_id else []
            rec.uo_digital_domicile_ids = [(6, 0, digital_domicile_ids)]

    def _compute_child_ids(self):
        for rec in self:
            if rec.is_amm or rec.is_gps:
                domain = [
                    "|", "|",
                    ("parent_id", "=", rec.id),
                    ("parent_id", "in", rec.aoo_ids.ids),
                    ("parent_id", "in", rec.uo_ids.ids),
                ]
            elif rec.is_aoo:
                domain = [
                    "|",
                    ("parent_id", "=", rec.id),
                    ("parent_id", "in", rec.aoo_uo_ids.ids),
                ]
            else:
                domain = [
                    ("parent_id", "=", rec.id)
                ]
            child_ids = self.search(domain).ids
            rec.child_ids = [(6, 0, child_ids)]

    def _compute_digital_domicile_ids_html(self):
        for rec in self:
            digital_domicile_name_list = []
            digital_domicile_field = ""
            if rec.is_aoo:
                digital_domicile_field = "aoo_digital_domicile_ids"
            elif rec.is_uo:
                digital_domicile_field = "uo_digital_domicile_ids"
            if digital_domicile_field:
                for digital_domicile in rec[digital_domicile_field]:
                    digital_domicile_name_list.append(digital_domicile.email_address)
            rec.digital_domicile_ids_html = ", ".join(digital_domicile_name_list)

    def _compute_email_address_ids_html(self):
        for rec in self:
            email_address_list = []
            for email_address in rec.email_address_ids:
                email_address_list.append(email_address.email_address)
            rec.email_address_ids_html = ", ".join(email_address_list)

    @api.depends(
        'is_company', 'name', 'parent_id.display_name', 'parent_id.name', 'parent_id', 'type',
        'company_name', "amministrazione_id", "amministrazione_id.name", "amministrazione_id.display_name",
        "aoo_id", "aoo_id.display_name", "aoo_id.name")
    def _compute_display_name(self):
        super(ResPartner, self)._compute_display_name()
        for partner in self:
            display_name_list = []
            if partner.is_aoo or partner.is_amm or partner.is_gps:
                field_list = ["amministrazione_id", "aoo_id"]
                for field in field_list:
                    if partner[field]:
                        display_name_list.append(partner[field].name)
                if partner.name:
                    display_name_list.append(partner.name)
            elif partner.is_uo:
                display_name_list = [partner.amministrazione_id.name]
                if partner.aoo_id:
                    display_name_list.append(partner.aoo_id.name)
                if partner.name:
                    display_name_list.append(partner.name)
            elif partner.company_type in ["person", "company"]:
                if partner.parent_id.is_uo and partner.parent_id.name:
                    display_name_list.append(partner.parent_id.amministrazione_id.name)
                    if partner.parent_id.aoo_id:
                        display_name_list.append(partner.parent_id.aoo_id.name)
                    display_name_list.append(partner.parent_id.name)
                elif partner.parent_id.is_aoo and partner.parent_id.name:
                    display_name_list.append(partner.parent_id.amministrazione_id.name)
                    display_name_list.append(partner.parent_id.name)
                elif (partner.parent_id.is_amm or partner.parent_id.is_gps) and partner.parent_id.name:
                    display_name_list.append(partner.parent_id.name)
                elif partner.parent_id.is_company and partner.parent_id.name:
                    display_name_list.append(partner.parent_id.name)
                if partner.name:
                    display_name_list.append(partner.name)
            if display_name_list and False not in display_name_list:
                partner.display_name = ", ".join(display_name_list)
                display_name_list[-1] = "<b>%s</b>" % display_name_list[-1]
                partner.display_name_html = ", ".join(display_name_list)
            else:
                partner.display_name = ""
                partner.display_name_html = ""

    def _get_name(self):
        name = super(ResPartner, self)._get_name()
        if self.amministrazione_id or \
                self.aoo_id or \
                (self.parent_id and (self.parent_id.is_aoo or self.parent_id.is_uo or self.parent_id.is_amm or self.parent_id.is_gps)):
            name = self.display_name or name
        return name

    @api.onchange("company_type")
    def _onchange_company_type(self):
        super(ResPartner, self).onchange_company_type()
        self.parent_id = False
        if self.company_type!="company":
            self.company_subject_type = False
        if self.company_type!="company" or self.company_subject_type!="pa" or self.company_subject_type!="gps":
            self.contact_pa_type = False
        self.aoo_uo_ids = [(6, 0, [])]
        self.pa_digital_domicile_ids = [(6, 0, [])]
        self.aoo_digital_domicile_ids = [(6, 0, [])]
        self.uo_digital_domicile_ids = [(6, 0, [])]

    def _compute_parent_pa(self):
        for rec in self:
            rec.parent_amm_name = False
            rec.parent_gps_name = False
            rec.parent_aoo_name = False
            rec.parent_uo_name = False
            r = None
            if rec.parent_id:
                r = rec.parent_id
            elif rec.aoo_id:
                r = rec.aoo_id
            elif rec.amministrazione_id:
                r = rec.amministrazione_id
            else:
                continue
            if r.is_amm:
                rec.parent_amm_name = r.name
            elif r.is_gps:
                rec.parent_gps_name = r.name
            elif r.is_aoo:
                rec.parent_amm_name = r.amministrazione_id.name if r.amministrazione_id.is_amm else False
                rec.parent_gps_name = r.amministrazione_id.name if r.amministrazione_id.is_gps else False
                rec.parent_aoo_name = r.name
            elif r.is_uo:
                rec.parent_amm_name = r.aoo_id.amministrazione_id.name if r.aoo_id.amministrazione_id.is_amm else False
                rec.parent_gps_name = r.aoo_id.amministrazione_id.name if r.aoo_id.amministrazione_id.is_gps else False
                rec.parent_aoo_name = r.aoo_id.name
                rec.parent_uo_name = r.name

    @api.onchange("type")
    def onchange_type(self):
        self.parent_child_aoo_id = False
        self.parent_child_uo_id = False

    @api.onchange("parent_child_aoo_id")
    def onchange_parent_child_aoo_id(self):
        # il valore del campo parent_child_uo_id deve essere impostato a False se uno dei seguenti casi è vero:
        # caso 1: il campo parent_child_aoo_id non è valorizzato
        # caso 2: il campo parent_child_aoo_id è valorizzato con una AOO che è diversa dalla AOO associata alla UO
        caso1 = not self.parent_child_aoo_id
        caso2 = self.parent_child_aoo_id and \
                self.parent_child_uo_id and \
                self.parent_child_uo_id.aoo_id and \
                self.parent_child_uo_id.aoo_id.id!=self.parent_child_aoo_id.id
        if caso1 or caso2:
            self.parent_child_uo_id = False

    @api.onchange("parent_child_uo_id")
    def onchange_parent_child_uo_id(self):
        if self.parent_child_uo_id and self.parent_child_uo_id.aoo_id:
            self.parent_child_aoo_id = self.parent_child_uo_id.aoo_id.id

    def unlink(self):
        for rec in self:
            # Impedisce l'eliminazione di un record di tipo amministrazione se presente una AOO o una UO associata ad esso
            if rec.aoo_ids:
                raise ValidationError(_("It is not possible to delete a record with AOO!"))
        super(ResPartner, self).unlink()

    def write(self, vals):
        for rec in self:
            is_company_type_updated = vals.get("company_type", False) and rec.company_type and rec.company_type != vals.get("company_type", False)
            is_company_subject_type_updated = vals.get("company_subject_type", False) and rec.company_subject_type and rec.company_subject_type != vals.get("company_subject_type", False)
            if (is_company_type_updated or is_company_subject_type_updated) and \
                    rec.aoo_ids:
                raise ValidationError(_("It is not possible to change the type of contact with associated AOO!"))
            amministrazione_id = vals.get("amministrazione_id", False)
            # se in un contatto AOO si modifica il riferimento all'amministrazione allora lo si deve modificare in tutte
            # le UO ad essa appartenenti
            if rec.is_aoo and amministrazione_id:
                for uo in rec.aoo_uo_ids:
                    uo.write({"amministrazione_id": amministrazione_id})
            aoo_id = vals.get("aoo_id", False)
            # se in un contatto UO si modifica il riferimento alla AOO allora si deve modificare anche il riferimento
            # alla relativa amministrazione
            if rec.is_uo and aoo_id:
                aoo = self.browse(aoo_id)
                vals["amministrazione_id"] = aoo.amministrazione_id.id if aoo else False
            # se in un contatto si modifica il campo parent_child_uo_id allora si deve impostare anche il campo
            # parent_child_aoo_id (sempre se la UO ha una AOO associata)
            if "parent_child_uo_id" in vals and not ("parent_child_aoo_id" in vals):
                vals["parent_child_aoo_id"] = rec.parent_child_aoo_id.id if rec.parent_child_aoo_id else False
            # #creazione dei domicili digitali tramite pa/gps
            # if "pa_digital_domicile_ids" in vals and vals["pa_digital_domicile_ids"]:
            #     self._create_or_unlink_computed_one2many(vals["pa_digital_domicile_ids"], "res.partner.digital.domicile")
            # #creazione dei domicili digitali tramite uo
            # if "uo_digital_domicile_ids" in vals and vals["uo_digital_domicile_ids"] and rec.aoo_id:
            #     self._create_or_unlink_computed_one2many(vals["uo_digital_domicile_ids"], "res.partner.digital.domicile", "aoo_id", rec.aoo_id.id)
            #creazione dei contatti tramite il campo computed (modificato da questo modulo) child_ids
            if "child_ids" in vals and vals["child_ids"]:
                self._create_or_unlink_computed_one2many(vals["child_ids"], "res.partner", "parent_id", rec.id)
        return super(ResPartner, self).write(vals)

    @api.model
    def _create_or_unlink_computed_one2many(self, data_list, many2one_model, many2one_field=None, many2one_id=None):
        model_obj = self.env[many2one_model]
        for data in data_list:
            if len(data) == 3 and isinstance(data[1], str) and "virtual_" in data[1]:
                if many2one_field and many2one_id:
                    data[2][many2one_field] = many2one_id
                model_obj.create(data[2])
            elif data[0] == 2:
                model_obj.browse(data[1]).unlink()

    def name_get(self):
        res = super(ResPartner, self).name_get()
        display_field = self.env.context.get("display_field", False)
        if not display_field:
            return res
        for record in self:
            if display_field and display_field in record and record[display_field]:
                name = record[display_field]
                index = [i for i, r in enumerate(res) if r and r[0] == record.id]
                if index:
                    res[index[0]] = (record.id, name)
                else:
                    res.append((record.id, name))
        return res

    @api.model
    def get_uniqueness_mail_models(self):
        uniqueness_mail_models = super(ResPartner, self).get_uniqueness_mail_models()
        uniqueness_mail_models += ["res.partner.email.address", "res.partner.digital.domicile"]
        return uniqueness_mail_models

    @api.model
    def get_uniqueness_mail_domain(self, mail_type, value, model_name, check_id, parent_id=False):
        domain = super(ResPartner, self).get_uniqueness_mail_domain(mail_type, value, model_name, check_id, parent_id)
        # si aggiunge la gestione di un coso particolare nella univocità della pec mail: un partner di tipo pa o gps
        # può avere la stessa pec mail di un domicilio digitale associato ad una delle proprie AOO
        if model_name != self._name and model_name == "res.partner.digital.domicile" and parent_id:
            aoo = self.browse(parent_id)
            if aoo and aoo.amministrazione_id:
                domain.append(("id", "!=", aoo.amministrazione_id.id))
        return domain