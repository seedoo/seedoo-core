from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


SELECTION_RES_MODEL = [
    ("res_users", "User")
]


# Modello utilizzato per memorizzare le acl dei modelli che estendo la classe Security. Infatti, se si vuole estendere
# la security base di un modello con la gestione acl si deve creare un nuovo modello avente come _name il nome del
# modello + ".acl" e che estende la classe Acl. Ad esempio, dato il modello "sd.dms.folder" per implementare la gestione
# acl si deve creare un nuovo modello "sd.dms.folder.acl" che estende la classe Acl. Nella classe figlia deve essere
# definito anche il campo _acl_field in modo da far funzionare correttamente gli algoritmi della classe padre.
# Considerando sempre l'esempio del modello "sd.dms.folder" il campo _acl_field deve essere uguale a "folder_id".
# Essendo la classe corrente una classe astratta, quando viene implementata nel corrispondente modello crea una tabella
# acl per ogni modello. Questa scelta è stata fatta in modo da evitare da avere un unico tabellone contenente tutte le
# acl, in questo modo si hanno diverse tabelle e le relative query sono più leggere.
# Sempre all'interno del modello che estende la classe corrente devono essere definiti il trigger SQL che permette di
# eliminare le righe di acl non più utilizzate e il metodo get_default_module_id per restituire il modulo corretto dal
# quale vengono create le varie acl. Un esempio di entrambe i casi possono essere trovati nel modello "sd.dms.folder".
class Acl(models.AbstractModel):

    _name = "fl.acl"
    _description = "Acl"

    _acl_field = None
    _security_field = None

    _rec_name = "res_name"

    @api.model
    def get_default_module_id(self):
        return False

    #TODO: valutare un refactoring per farlo diventare un campo many2one in modo da evitare il bug di eliminazione dei
    # valori delle selection per cui è stato fatto il fix nel metodo _process_end_unlink_record nel modulo fl_acl_set
    res_model = fields.Selection(
        string="Resource Model",
        selection=SELECTION_RES_MODEL
    )

    res_id = fields.Integer(
        string="Resource Id"
    )

    res_name = fields.Char(
        string="Resource Name",
        compute="_compute_res_name",
    )

    perm_create = fields.Boolean(
        string="Create",
        default=False
    )

    perm_read = fields.Boolean(
        string="Read",
        readonly=True,
        default=True
    )

    perm_write = fields.Boolean(
        string="Write",
        default=False
    )

    perm_delete = fields.Boolean(
        string="Delete",
        default=False,
        readonly=True
    )

    # Riferimento al modulo che ha creato la acl
    module_id = fields.Many2one(
        string="Module",
        comodel_name="ir.module.module",
        default=lambda self: self.get_default_module_id(),
        readonly=True
    )

    # Indica se la acl è stato creato da un automatismo di sistema (True) oppure da un utente (False)
    create_system = fields.Boolean(
        string="Created by System",
        default=False
    )

    create_uid = fields.Many2one(
        string="Created by",
        comodel_name="res.users",
        readonly=True
    )

    create_date = fields.Datetime(
        string="Created on",
        readonly=True
    )

    write_uid = fields.Many2one(
        string="Last Updated by",
        comodel_name="res.users",
        readonly=True
    )

    write_date = fields.Datetime(
        string="Last Updated on",
        readonly=True
    )

    # Campo usato solamente nella vista per agevolare la valorizzazione del campo res_id, infatti la valorizzazione dei
    # campi res_* avviene attraverso il metodo _set_res_values definito nell'attributo inverse del campo
    res_users_id = fields.Many2one(
        string="User",
        comodel_name="res.users",
        compute="_compute_many2one_res_values",
        inverse="_set_res_values",
    )

    # Campo usato solamente nella vista per evitare di valorizzare il campo res_users_id con utenti per cui è già stato
    # inserito una acl
    acl_res_users_ids = fields.Many2many(
        string="Acl Users",
        comodel_name="res.users",
        compute="_compute_acl_res_users_ids",
    )


    @api.depends("res_model", "res_id")
    def _compute_res_name(self):
        for acl in self:
            acl.res_name = False
            if not acl.res_model:
                continue
            res_many2one_field_name = self._get_many2one_res_model_field(acl.res_model)
            if not res_many2one_field_name:
                continue
            if not (res_many2one_field_name in acl):
                continue
            acl.res_name = acl[res_many2one_field_name].display_name


    @api.model
    def get_acl_field(self):
        if not self._acl_field:
            raise UserError(_("Acl field not defined in the inherited document type %s") % self._description)
        return self._acl_field


    @api.model
    def _get_many2one_res_model_field(self, res_model):
        return "%s_id" % res_model


    @api.depends("res_model", "res_id")
    def _compute_many2one_res_values(self):
        for acl in self:
            # imposta a False tutti i campi many2one computed
            for res_model_value in self._fields["res_model"].selection:
                setattr(acl, self._get_many2one_res_model_field(res_model_value[0]), False)
            # se res_model e res_id sono valorizzati allora imposta il relativo campo many2one computed
            if acl.res_model and acl.res_id:
                setattr(acl, self._get_many2one_res_model_field(acl.res_model), acl.res_id)


    def _set_res_values(self):
        for acl in self:
            if acl.res_users_id:
                acl.res_id = acl.res_users_id.id
                acl.res_model = "res_users"
            else:
                acl.res_id = False
                acl.res_model = False


    @api.depends("res_model")
    def _compute_acl_res_users_ids(self):
        self._compute_acl_res_ids("res_users", "res_users_id", "acl_res_users_ids")


    def _compute_acl_res_ids(self, res_model_param, res_field_param, res_ids_field_param):
        acl_values = self._context.get("acl_values", [])
        for acl in self:
            res_ids = []
            for acl_value in acl_values:
                acl_operation = acl_value[0]
                acl_data = acl_value[2]
                # caso [(6, 0, [acl_id_1, acl_id_2, ...])]: associa tutte le acl nella lista eliminando le vecchie
                if acl_operation == 6:
                    for acl_id in acl_data:
                        acl_found = self.browse(acl_id)
                        res_model = acl_found.res_model
                        if acl_found and res_model == res_model_param:
                            res_id = getattr(acl_found, res_field_param).id
                            res_ids.append(res_id)
                # caso [(1, 0, {values})]: aggiunge una nuova acl
                elif acl_operation == 0 and acl_data and isinstance(acl_data, dict):
                    if acl_data.get("res_model", False) == res_model_param:
                        res_id = acl_data.get(res_field_param, False)
                        res_ids.append(res_id)
            setattr(acl, res_ids_field_param, res_ids)


    # Metodo usato solamente nella vista form per azionare il metodo _compute_acl_field_ids con la valorizzazione dei
    # campi res_model e res_id. Infatti la reale valorizzazione dei campi res_model, res_id e viene fatta tramite il
    # metodo _compute_many2one_res_values
    @api.onchange('res_users_id')
    def _onchange_res_users_id(self):
        if self.res_users_id:
            self.res_id = self.res_users_id.id
            self.res_model = "res_users"
        else:
            self.res_id = False
            self.res_model = False

    @api.model
    def create(self, vals):
        acl = super(Acl, self).create(vals)
        if not self._security_field:
            return acl
        # aggiorna le acl da ereditare
        for security_record in acl[self._security_field]:
            security_record.update_inherit_acl(
                update_record_inherit_acls=False,
                add_children_inherit_acl_ids=[acl.id],
                del_children_inherit_acl_ids=[]
            )
        return acl

    def write(self, vals):
        # se il campo di riferimento ai record su cui sono associate le acl non viene aggiornato, allora non c'è alcun
        # bisogno di aggiornare le acl ereditate da tali record
        if not (self._security_field in vals) or not self._security_field:
            return super(Acl, self).write(vals)
        # salva i riferimenti ai vecchi record di security
        dict_old_security_ids = {}
        for acl in self:
            dict_old_security_ids[acl.id] = set(acl[self._security_field].ids)
        # chiama il metodo padre
        result = super(Acl, self).write(vals)
        # aggiorna le acl da ereditare
        for acl in self:
            security_model = acl[self._security_field]._name
            security_obj = self.env[security_model]
            new_security_ids = set(acl[self._security_field].ids)
            old_security_ids = dict_old_security_ids[acl.id]
            for del_security_id in list(old_security_ids - new_security_ids):
                security_obj.browse(del_security_id).update_inherit_acl(
                    update_record_inherit_acls=False,
                    add_children_inherit_acl_ids=[],
                    del_children_inherit_acl_ids=[acl.id]
                )
            for add_security_id in list(new_security_ids - old_security_ids):
                security_obj.browse(add_security_id).update_inherit_acl(
                    update_record_inherit_acls=False,
                    add_children_inherit_acl_ids=[acl.id],
                    del_children_inherit_acl_ids=[]
                )
        return result