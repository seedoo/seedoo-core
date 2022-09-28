from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class InheritSdDmsDocument(models.Model):
    _inherit = "sd.dms.document"

    fascicolo_ids = fields.Many2many(
        string="Fascicoli",
        comodel_name="sd.fascicolo.fascicolo",
        relation="sd_fascicolo_fascicolo_sd_dms_document_rel",
        column1="documento_id",
        column2="fascicolo_id"
    )

    fascicolo_ids_count = fields.Integer(
        string="# Dossiers ",
        compute="_compute_fascicolo_ids_count",
    )

    fascicolo_acl_ids = fields.One2many(
        string="Dossier acl inherited",
        comodel_name="sd.fascicolo.fascicolo.document.acl",
        inverse_name="document_id",
        compute="_compute_fascicolo_acl_ids",
        readonly=True,
        store=True
    )

    def _compute_fascicolo_ids_count(self):
        document_dossiers_obj = self.env["sd.fascicolo.fascicolo"]
        for document in self:
            fascicolo_ids_count = document_dossiers_obj.search([("documento_ids", "=", self.id)], count=True)
            document.fascicolo_ids_count = fascicolo_ids_count

    @api.depends("fascicolo_ids.inherit_acl_ids", "fascicolo_ids.system_acl_ids", "fascicolo_ids.acl_ids")
    def _compute_fascicolo_acl_ids(self):
        fascicolo_document_acl_obj = self.sudo().env["sd.fascicolo.fascicolo.document.acl"]
        for document in self:
            fascicolo_ids = []
            fascicolo_acl_ids = []
            for fascicolo in document.sudo().fascicolo_ids:
                fascicolo_ids.append(fascicolo.id)
                acl_ids = fascicolo.inherit_acl_ids.ids + fascicolo.system_acl_ids.ids + fascicolo.acl_ids.ids
                # ricerca delle righe di acl da rimuovere
                fascicolo_document_acl_data_list = fascicolo_document_acl_obj.search_read([
                    ("document_id", "=", document.id),
                    ("fascicolo_id", "=", fascicolo.id),
                    ("acl_id", "not in", acl_ids),
                ], ["id"])
                for acl_data in fascicolo_document_acl_data_list:
                    fascicolo_acl_ids.append((2, acl_data["id"]))
                # ricerca delle righe di acl da aggiungere
                fascicolo_document_acl_data_list = fascicolo_document_acl_obj.search_read([
                    ("document_id", "=", document.id),
                    ("fascicolo_id", "=", fascicolo.id),
                    ("acl_id", "in", acl_ids),
                ], ["acl_id"])
                saved_acl_ids = [acl_data["acl_id"][0] for acl_data in fascicolo_document_acl_data_list]
                create_acl_ids = list(set(acl_ids) - set(saved_acl_ids))
                for create_acl_id in create_acl_ids:
                    fascicolo_acl_ids.append((0, 0, {
                        "document_id": document.id,
                        "fascicolo_id": fascicolo.id,
                        "acl_id": create_acl_id
                    }))
            # ricerca delle righe di acl da rimuovere a causa della disassociazione di un fascicolo
            fascicolo_document_acl_data_list = fascicolo_document_acl_obj.search_read([
                ("document_id", "=", document.id),
                ("fascicolo_id", "not in", fascicolo_ids)
            ], ["id"])
            for acl_data in fascicolo_document_acl_data_list:
                fascicolo_acl_ids.append((2, acl_data["id"]))
            document.fascicolo_acl_ids = fascicolo_acl_ids

    ####################################################################################################################
    # CRUD
    ####################################################################################################################

    def write(self, vals):
        for rec in self:
            # Controllo per evitare di modificare la classificazione di un documento quando esso è già associato a dei
            # fascicoli. Nella vista il campo della classificazione viene reso readonly quindi questo controllo viene
            # fatto per gestire tutti gli altri aggiornamenti che non passano per la vista
            voce_titolario_id = vals.get("voce_titolario_id", False)
            if voce_titolario_id and rec.voce_titolario_id and voce_titolario_id!=rec.voce_titolario_id.id and \
                    rec.fascicolo_ids:
                raise ValidationError(_("The classification of the document cannot be modified when the document is associated with dossiers!"))
        return super(InheritSdDmsDocument, self).write(vals)

    ####################################################################################################################
    # Security
    ####################################################################################################################

    @api.model
    def _set_joins(self, query, alias_dict, operation="read"):
        super(InheritSdDmsDocument, self)._set_joins(query, alias_dict, operation)
        if not self._check_fascicolo_operation(operation):
            return
        if self._check_fascicolo_manager_group():
            return self._set_fascicolo_joins(query, alias_dict, operation)
        return self._set_fascicolo_acl_joins(query, alias_dict, operation)

    @api.model
    def _set_fascicolo_joins(self, query, alias_dict, operation):
        fascicolo_documento_alias = query.left_join(
            alias_dict.get(self._get_security_table(), self._get_security_table()),
            "id",
            "sd_fascicolo_fascicolo_sd_dms_document_rel",
            "documento_id",
            "fd"
        )
        alias_dict["fascicolo_documento_alias"] = fascicolo_documento_alias

    @api.model
    def _set_fascicolo_acl_joins(self, query, alias_dict, operation):
        fascicolo_documento_acl_alias = query.left_join(
            alias_dict.get(self._get_security_table(), self._get_security_table()),
            "id",
            self.env["sd.fascicolo.fascicolo.document.acl"]._table,
            "document_id",
            "fda"
        )
        fascicolo_acl_alias = query.left_join(
            fascicolo_documento_acl_alias,
            "acl_id",
            self.env["sd.fascicolo.fascicolo.acl"]._table,
            "id",
            "fa"
        )
        alias_dict["fascicolo_documento_acl_alias"] = fascicolo_documento_acl_alias
        alias_dict["fascicolo_acl_alias"] = fascicolo_acl_alias
        # Se il modulo fl_acl_set non è installato allora non deve essere fatto anche il join con la tabella dei set
        if not self._check_fasciolo_acl_set():
            return []
        fascicolo_acl_set_alias = query.left_join(
            fascicolo_acl_alias,
            "res_id",
            "fl_set_set_res_users_rel",
            "set_id",
            "fas",
            "%s.res_model = 'fl_set_set'" % fascicolo_acl_alias
        )
        alias_dict["fascicolo_acl_set_alias"] = fascicolo_acl_set_alias

    @api.model
    def _get_conditions(self, alias_dict, operation):
        conditions = super(InheritSdDmsDocument, self)._get_conditions(alias_dict, operation)
        if not self._check_fascicolo_operation(operation):
            return conditions
        if self._check_fascicolo_manager_group():
            return conditions + self._get_fascicolo_conditions(alias_dict, operation)
        return conditions + self._get_fascicolo_acl_conditions(alias_dict, operation)

    @api.model
    def _get_fascicolo_conditions(self, alias_dict, operation):
        conditions = []
        conditions.append("""
            {table_rel}.fascicolo_id IS NOT NULL
        """.format(
            table_rel=alias_dict["fascicolo_documento_alias"]
        ))
        return conditions

    @api.model
    def _get_fascicolo_acl_conditions(self, alias_dict, operation):
        conditions = []
        conditions.append("""
            {table_acl}.perm_{operation} = TRUE AND
            {table_acl}.res_model = '{model}' AND
            {table_acl}.res_id = {uid}
        """.format(
            table_acl=alias_dict["fascicolo_acl_alias"],
            operation=operation,
            model="res_users",
            uid=self.env.uid
        ))
        # Se il modulo fl_acl_set non è installato allora non deveno essere inserite le condizioni per i set
        if not self._check_fasciolo_acl_set():
            return conditions
        conditions.append("""
            {table_acl}.perm_{operation} = TRUE AND
            {table_acl}.res_model = '{model}' AND
            {table_acl_set_rel}.user_id = {uid}
        """.format(
            table_acl=alias_dict["fascicolo_acl_alias"],
            table_acl_set_rel=alias_dict["fascicolo_acl_set_alias"],
            operation=operation,
            model="fl_set_set",
            uid=self.env.uid
        ))
        return conditions

    @api.model
    def _check_fascicolo_operation(self, operation):
        """
        Il controllo delle acl del fascicolo a cui il documento appartiene deve essere fatto solo per le operazione di
        read. Per tutte le altre operazioni, le acl del fascicolo non influiscono su quelle del documento. Quindi gli
        utenti potranno vedere tutti i documenti appartenenti ai fascicoli di cui hanno visibilità, ma non potranno
        modificarli e/o cancellarli.
        :param operation:
        :return:
        """
        if operation == "read":
            return True
        return False

    @api.model
    def _check_fascicolo_manager_group(self):
        """
        Se l'utente ha almeno il gruppo group_sd_fascicolo_manager allora ha visibilità di tutti i fascicoli e di
        conseguenza di tutti i documenti appartenenti ad essi, quindi nella query non si controllano le acl ma solo il
        relativo collegamento con i fascicoli.
        :return:
        """
        if self.env.user.has_group("sd_fascicolo.group_sd_fascicolo_manager"):
            return True
        return False

    @api.model
    def _check_fasciolo_acl_set(self):
        """
        Se il modulo fl_acl_set non è installato allora non deve essere fatto anche il join con la tabella dei set
        :return:
        """
        if self.env["ir.module.module"].sudo().search([("name", "=", "fl_acl_set"), ("state", "=", "installed")]):
            return True
        return False