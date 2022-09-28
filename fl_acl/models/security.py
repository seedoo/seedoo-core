from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.osv import expression
from odoo.osv.query import Query
from odoo.exceptions import AccessError
import time
import logging

_logger = logging.getLogger(__name__)


# Modello utilizzato per implementare gli algoritmi di controllo acl. Se si vuole che un modello usi la gestione acl si
# deve estendere il relativo modello con la classe in questione e creare un nuovo modello per la memorizzazione delle
# acl (per maggiori dettagli guardare la classe Acl). Ad esempio, se si vuole che il modello "sd.dms.folder" sfrutti la
# gestione acl si deve estendere il modello con la corrente classe. Nella classe figlia devono essere definiti i campi
# _parent_field e _parent_model in modo da far funzionare correttamente gli algoritmi della classe padre. Considerando
# sempre l'esempio del modello "sd.dms.folder" il campo _parent_field deve essere uguale "parent_folder_id" mentre il
# campo _parent_model deve essere uguale a "sd.dms.folder".
# Nel modello che estende la classe Security devono essere definiti anche i campi Many2many acl_ids, system_acl_ids,
# inherit_acl_ids impostando il corretto modello di riferimento delle acl.
class Security(models.AbstractModel):

    _name = "fl.security"
    _description = "Security"

    _parent_field = None
    _parent_model = None


    owner_id = fields.Many2one(
        string="Owner",
        comodel_name="res.users",
        required=True,
        default=lambda self: self.env.user.id
    )

    is_owner = fields.Boolean(
        string="Is owner",
        compute="_compute_is_owner",
        search="_search_is_owner",
        default=True
    )

    inherit_acl = fields.Boolean(
        "Inherit Acl",
        default=True
    )

    perm_create = fields.Boolean(
        string="Create Access",
        compute="_compute_perm_create",
        search="_search_perm_create",
        default=True
    )

    perm_read = fields.Boolean(
        string="Read Access",
        compute="_compute_perm_read",
        search="_search_perm_read",
        default=True
    )

    perm_write = fields.Boolean(
        string="Write Access",
        compute="_compute_perm_write",
        search="_search_perm_write",
        default=True
    )


    def _compute_perm_create(self):
        records = self._filter_access('create')
        for record in records:
            record.update({'perm_create': True})
        for record in self - records:
            record.update({'perm_create': False})


    def _search_perm_create(self, operator=None, operand=None):
        records = self.search([])._filter_access('create')
        return [("id", "in", records.ids)]


    def _compute_perm_read(self):
        records = self._filter_access('read')
        for record in records:
            record.update({'perm_read': True})
        for record in self - records:
            record.update({'perm_read': False})


    def _search_perm_read(self, operator=None, operand=None):
        records = self.search([])._filter_access('read')
        return [("id", "in", records.ids)]


    def _compute_perm_write(self):
        records = self._filter_access('write')
        for record in records:
            record.update({'perm_write': True})
        for record in self - records:
            record.update({'perm_write': False})


    def _search_perm_write(self, operator=None, operand=None):
        records = self.search([])._filter_access('write')
        return [("id", "in", records.ids)]


    def _compute_is_owner(self):
        for record in self:
            record.is_owner = record.owner_id.id == self.env.uid


    def _search_is_owner(self, operator=None, operand=None):
        records = self.search([('owner_id', '=', self.env.uid)])
        return [("id", "in", records.ids)]


    ####################################################################################################################
    # Metodi che estendo il crud base del modello richiamando l'algoritmo di gestione acl
    ####################################################################################################################

    # Nel caso del metodo _search si è stati costretti ad effettuare un ovverride del metodo originale al fine di
    # inserire nella query la clausola DISTINCT nella select in modo da evitare una duplicazione dei risultati. Quest'
    # ultima è dovuta alle modifiche apportate alla query di ricerca in modo da inserire direttamente all'interno della
    # stessa il controllo dei permessi sulle acl al fine di rendere più prestante alla query. In caso contrario si
    # sarebbe dovuto implementare il classico controllo (ID in [...]) il quale introduce delle problematiche
    # prestazionali all'aumentare della lista di ID.
    # Le parti di codice del metodo _search che hanno subito una modifica sono state evidenziate in modo da agevolare
    # eventuali controlli nel caso il codice del core dovesse subire modifiche.
    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        if self.skip_security():
            return super(Security, self)._search(args, offset, limit, order, count, access_rights_uid)
        model = self.with_user(access_rights_uid) if access_rights_uid else self
        model.check_access_rights('read')

        if expression.is_false(self, args):
            # optimization: no need to query, as no record satisfies the domain
            return 0 if count else []

        # the flush must be done before the _where_calc(), as the latter can do some selects
        self._flush_search(args, order=order)

        ################################################################################################################
        # le seguenti parti sono state aggiunte per verificare i permessi sulle acl all'interno della stessa query
        ################################################################################################################
        # query = self._where_calc(args)
        query = self._where_calc(args)
        alias_dict = {}
        self._set_joins(query, alias_dict)
        self._set_conditions(query, alias_dict)
        ################################################################################################################
        self._apply_ir_rules(query, 'read')

        if count:
            ############################################################################################################
            # se la query prevede un COUNT allora aggiungiamo solo il DISTINCT agli argomenti della SELECT
            ############################################################################################################
            # query_str, params = query.select("count(1)")
            query_str, params = query.select("count(DISTINCT {table}.id)".format(
                table=self._table
            ))
            ############################################################################################################
            self._cr.execute(query_str, params)
            res = self._cr.fetchone()
            return res[0]

        query.order = self._generate_order_by(order, query).replace('ORDER BY ', '')
        query.limit = limit
        query.offset = offset

        ################################################################################################################
        # se nella query è previsto un ordinamento allora si devono aggiungere alla SELECT anche le colonne su cui viene
        # fatto l'ordinamento altrimenti la SELECT DISTINCT genera errore
        ################################################################################################################
        # return query
        select_args = "DISTINCT {table}.id".format(
            table=self._table
        )
        if query.order:
            select_args += ", " + query.order.replace("ASC", "").replace("DESC", "")
        query_str, params = query.select(select_args)
        self._cr.execute(query_str, params)
        return [row[0] for row in self._cr.fetchall()]
        ################################################################################################################


    @api.model
    def create(self, vals):
        parent_field_value = vals.get(self._parent_field, False)
        if parent_field_value and self._parent_model:
            parent_model_obj = self.env[self._parent_model]
            parent_model_obj.browse(parent_field_value)._check_access("create")
        else:
            # le acl non possono essere ereditate se il record non ha padre, quindi si imposta inherit_acl a False
            vals["inherit_acl"] = False
        result = super(Security, self).create(vals)
        result.set_old_owner_acl(vals.get("owner_id", False), self.env.uid, self.env.user.name)
        # aggiorna le acl da ereditare
        result.update_inherit_acl(
            update_record_inherit_acls=True,
            add_children_inherit_acl_ids=result.acl_ids.ids + result.system_acl_ids.ids,
            del_children_inherit_acl_ids=[]
        )
        return result


    def read(self, fields=None, load="_classic_read"):
        self._check_access("read")
        return super(Security, self).read(fields, load)


    def write(self, vals):
        self._check_access("write")
        parent_field_value = vals.get(self._parent_field, False)
        if parent_field_value and self._parent_model:
            parent_model_obj = self.env[self._parent_model]
            for record in self:
                if not record[self._parent_field] or record[self._parent_field].id != parent_field_value:
                    parent_model_obj.browse(parent_field_value)._check_access("create")
        elif self._parent_field in vals and not parent_field_value and self._parent_model:
            # le acl non possono essere ereditate se il record non ha padre, quindi si imposta inherit_acl a False
            vals["inherit_acl"] = False
        # save old acl ids before to write vals
        dict_old_acl_ids = {}
        for record in self:
            dict_old_acl_ids[record.id] = set(record.acl_ids.ids + record.system_acl_ids.ids)
        # chiama il metodo padre
        result = super(Security, self).write(vals)
        # aggiorna se presente il field owner_id
        new_owner_id = vals.get("owner_id", False)
        if new_owner_id:
            for record in self:
                record.set_old_owner_acl(new_owner_id, self.env.uid, self.env.user.name)
        # aggiorna le acl da ereditare
        for record in self:
            new_acl_ids = set(record.acl_ids.ids + record.system_acl_ids.ids)
            old_acl_ids = dict_old_acl_ids[record.id]
            record.update_inherit_acl(
                update_record_inherit_acls=True if "inherit_acl" in vals else False,
                add_children_inherit_acl_ids=list(new_acl_ids - old_acl_ids),
                del_children_inherit_acl_ids=list(old_acl_ids - new_acl_ids)
            )
        return result


    def unlink(self):
        self._check_access("delete")
        return super(Security, self).unlink()


    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        acl_ids = []
        for acl in self.acl_ids:
            acl_copy = acl.copy()
            acl_ids.append(acl_copy.id)
        default["owner_id"] = self.env.uid
        default["acl_ids"] = [(6, 0, acl_ids)]
        default["system_acl_ids"] = [(6, 0, [])]
        return super(Security, self).copy(default=default)


    @api.model
    def flush(self, fnames=None, records=None):
        return super(Security, self.with_context(skip_security=True)).flush(fnames, records)


    def set_old_owner_acl(self, new_owner_id, old_owner_id, old_owner_name):
        """
        Se è stato modificato l'owner dell'istanza allora si deve aggiungere/aggiornare la acl del vecchio owner in modo
        da permettergli di continuare ad accedere all'istanza stessa.

        :param new_owner_id: id del nuovo owner
        :param old_owner_id: id del vecchio owner
        :param old_owner_name: name del vecchio owner
        :return:
        """
        #
        self.ensure_one()
        if not new_owner_id or new_owner_id == old_owner_id or SUPERUSER_ID == old_owner_id:
            return
        found = False
        for acl in self.sudo().acl_ids:
            if acl.res_model == "res_users" and acl.res_id == old_owner_id:
                acl.write({
                    "perm_create": True,
                    "perm_read": True,
                    "perm_write": True,
                    "perm_delete": True
                })
                found = True
        if not found:
            self.sudo().write({
                "acl_ids": [(0, 0, {
                    "res_model": "res_users",
                    "res_id": old_owner_id,
                    "res_name": old_owner_name,
                    "perm_create": True,
                    "perm_read": True,
                    "perm_write": True,
                    "perm_delete": True
                })]
            })


    def update_inherit_acl(self, update_record_inherit_acls=False, add_children_inherit_acl_ids=[], del_children_inherit_acl_ids=[]):
        """
        Le acl eraditate vengono calcolate automaticamente dal sistema al cambiamento del campo inherit_acl per il
        modello corrente e dei campi acl_ids, system_acl_ids nel caso del modello padre. Le acl ereditate sono
        identificate dal campo inherit_acl_ids (presente nel modello che estende la classe Security). Essendo un campo
        di tipo Many2many ogni acl da ereditare non sarà nuovamente istanziata ma si aggiungerà solamente un
        collegamento alla riga di acl ereditata. In questo modo, quando verrà eliminata la acl originale, in cascata
        verranno eliminati anche tutti gli altri collegamenti presenti nelle istanze che ereditano tale acl. Allo stesso
        modo, se si aggiornano i permessi CRUD della acl lo si farà per tutte le istanze che ereditano. Tuttavia, gli
        altri casi di modifica delle acl devono essere gestiti mediante il seguente metodo.
        """
        self.ensure_one()
        if not update_record_inherit_acls and not add_children_inherit_acl_ids and not del_children_inherit_acl_ids:
            return
        # se è stato modificato il valore del campo inherit_acl quindi si devono modificare le acl ereditate dal record
        if update_record_inherit_acls and self._parent_field:
            # si recuperano gli id delle acl del padre
            parent_acl_ids = self._get_parent_acl_ids(self[self._parent_field].id)
            if self.inherit_acl and self[self._parent_field]:
                # se il valore di inherit_acl è True si inseriscono gli id delle acl del padre al record corrente
                self._insert_parent_acl_ids(self.id, parent_acl_ids)
                # si inseriscono gli id delle acl del padre ai figli del record corrente
                self._update_inherit_children_acl(self.id, parent_acl_ids, [])
            else:
                # se il valore di inherit_acl è False si eliminano gli id delle acl del padre al record corrente
                self._delete_parent_acl_ids(self.id, parent_acl_ids)
                # si eliminano gli id delle acl del padre ai figli del record corrente
                self._update_inherit_children_acl(self.id, [], parent_acl_ids)
        # se si è aggiunta o eliminata una  o più acl al record allora si devono aggiorare le acl ereditate dai figli del record
        if add_children_inherit_acl_ids or del_children_inherit_acl_ids:
            self._update_inherit_children_acl(self.id, add_children_inherit_acl_ids, del_children_inherit_acl_ids)


    @api.model
    def _get_parent_acl_ids(self, parent_id):
        if not parent_id:
            return []
        # recupera le acl del parent che devono essere ereditate dal figlio
        parent_acl_table_rel = self._get_security_inherit_table_acl() + "_rel"
        sql_query = """
            SELECT acl_id
            FROM {parent_acl_table_rel}
            WHERE {parent_field} = {parent_id}
        """.format(
            parent_acl_table_rel=parent_acl_table_rel,
            parent_field=self.env[self._get_security_inherit_model_acl()].get_acl_field(),
            parent_id=parent_id,
        )
        self.env.cr.execute(sql_query)
        acl_ids = [row[0] for row in self.env.cr.fetchall()]
        # recupera le acl del parent che devono essere ereditate dal figlio
        parent_obj = self.env[self._parent_model]
        parent_acl_table_rel = parent_obj._get_security_inherit_table_acl() + "_inherit_rel"
        sql_query = """
            SELECT acl_id
            FROM {parent_acl_table_rel}
            WHERE {parent_field} = {parent_id}
        """.format(
            parent_acl_table_rel=parent_acl_table_rel,
            parent_field=self.env[parent_obj._get_security_inherit_model_acl()].get_acl_field(),
            parent_id=parent_id,
        )
        self.env.cr.execute(sql_query)
        inherit_acl_ids = [row[0] for row in self.env.cr.fetchall()]
        return acl_ids + inherit_acl_ids


    @api.model
    def _insert_parent_acl_ids(self, record_id, parent_acl_ids):
        if not parent_acl_ids:
            return
        start_time = time.time()
        record_acl_inherit_table_rel = self._get_security_table_acl() + "_inherit_rel"
        inherit_parent_acl_list = []
        for parent_acl_id in parent_acl_ids:
            inherit_parent_acl_list.append("(%s, %s)" % (record_id, parent_acl_id))
        sql_query = """
            INSERT INTO {record_acl_inherit_table_rel} ({record_field}, acl_id) VALUES {values}
        """.format(
            record_acl_inherit_table_rel=record_acl_inherit_table_rel,
            record_field=self.env[self._get_security_model_acl()].get_acl_field(),
            values=",".join(inherit_parent_acl_list)
        )
        self.env.cr.execute(sql_query)
        _logger.debug("--- insert parent_acl_ids %s in %s seconds ---" % (len(parent_acl_ids), time.time() - start_time))


    @api.model
    def _delete_parent_acl_ids(self, record_id, parent_acl_ids):
        if not parent_acl_ids:
            return
        start_time = time.time()
        record_acl_inherit_table_rel = self._get_security_table_acl() + "_inherit_rel"
        sql_query = """
            DELETE FROM {record_acl_inherit_table_rel} WHERE {record_field} = {record_id} AND acl_id IN ({acl_ids})
        """.format(
            record_acl_inherit_table_rel=record_acl_inherit_table_rel,
            record_field=self.env[self._get_security_model_acl()].get_acl_field(),
            record_id=record_id,
            acl_ids=",".join(map(str, parent_acl_ids))
        )
        self.env.cr.execute(sql_query)
        _logger.debug("--- insert parent_acl_ids %s in %s seconds ---" % (len(parent_acl_ids), time.time() - start_time))


    @api.model
    def _update_inherit_children_acl(self, record_id, add_children_inherit_acl_ids, del_children_inherit_acl_ids):
        recursive_table = "recursive_table"
        # si ricercano tutte le tabelle che ereditano le acl dalla tabella del record
        sql_query_children_model = """
            SELECT model
            FROM ir_model_fields
            WHERE name = 'inherit_acl_ids' AND
                  ttype = 'many2many' AND
                  related IS NULL AND
                  relation = '{security_table_acl}'
        """.format(
            security_table_acl=self._get_security_model_acl()
        )
        self.env.cr.execute(sql_query_children_model)
        children_model_list = [row[0] for row in self.env.cr.fetchall()]
        if not children_model_list:
            return []
        if not (self._get_security_model() in children_model_list):
            return []
        children_model_list.remove(self._get_security_model())
        # si ricercano tutti gli id dei figli con lo stesso modello (ad esempio tutte le cartelle che ereditano i
        # permessi a partire da una cartella con id record_id)
        sql_query = """
            WITH RECURSIVE
            {recursive_table} (id) AS
            (
                SELECT id, inherit_acl
                FROM {security_table}
                WHERE id = {record_id}
    
                UNION ALL
    
                SELECT {children_model_table}.id, {children_model_table}.inherit_acl
                FROM {recursive_table}, {children_model_table}
                WHERE {children_model_table}.{parent_field} = {recursive_table}.id AND 
                      {children_model_table}.inherit_acl = TRUE
            )
            SELECT id FROM {recursive_table}
        """.format(
            recursive_table=recursive_table,
            security_table=self._get_security_table(),
            record_id=record_id,
            children_model_table=self._get_security_table(),
            parent_field=self._parent_field
        )
        self.env.cr.execute(sql_query)
        same_model_inherit_children_ids = [row[0] for row in self.env.cr.fetchall()]
        if not same_model_inherit_children_ids:
            return []
        # si ricercano anche gli id dei figli di tutti i modelli differenti dal modello del record corrente (ad esempio
        # tutti i documenti)
        for children_model in children_model_list:
            children_model_obj = self.env[children_model]
            # si costruisce la query ricorsiva
            sql_query = """
                SELECT {children_model_table}.id
                FROM {children_model_table}
                WHERE {children_model_table}.inherit_acl = TRUE AND
                      {children_model_table}.{parent_field} IN ({same_model_inherit_children_ids})
            """.format(
                children_model_table=children_model_obj._get_security_table(),
                parent_field=children_model_obj._parent_field,
                same_model_inherit_children_ids=",".join(map(str, same_model_inherit_children_ids))
            )
            self.env.cr.execute(sql_query)
            inherit_children_ids = [row[0] for row in self.env.cr.fetchall()]
            # si aggiunge una acl per volta a tutti i figli che ereditano le acl dal record corrente
            for add_children_inherit_acl_id in add_children_inherit_acl_ids:
                self._insert_children_acl_id(inherit_children_ids, children_model, add_children_inherit_acl_id)
            # si elimina una acl per volta a tutti i figli che ereditano le acl dal record corrente
            for del_children_inherit_acl_id in del_children_inherit_acl_ids:
                self._delete_children_acl_id(inherit_children_ids, children_model, del_children_inherit_acl_id)
        # si elimina il record_id del record corrente in quanto le acl da lui ereditate sono state già aggiornate
        if record_id in same_model_inherit_children_ids:
            same_model_inherit_children_ids.remove(record_id)
        # si aggiunge una acl per volta a tutti i figli che ereditano le acl dal record corrente
        for add_children_inherit_acl_id in add_children_inherit_acl_ids:
            self._insert_children_acl_id(same_model_inherit_children_ids, self._get_security_model(), add_children_inherit_acl_id)
        # si elimina una acl per volta a tutti i figli che ereditano le acl dal record corrente
        for del_children_inherit_acl_id in del_children_inherit_acl_ids:
            self._delete_children_acl_id(same_model_inherit_children_ids, self._get_security_model(), del_children_inherit_acl_id)

    @api.model
    def _insert_children_acl_id(self, children_ids, children_model, acl_id):
        if not children_ids or not children_model or not acl_id:
            return
        start_time = time.time()
        children_obj = self.env[children_model]
        children_acl_inherit_table_rel = children_obj._get_security_table_acl() + "_inherit_rel"
        inherit_children_acl_list = []
        for children_id in children_ids:
            inherit_children_acl_list.append("(%s, %s)" % (children_id, acl_id))
        sql_query = """
            INSERT INTO {children_acl_inherit_table_rel} ({children_field}, acl_id) VALUES {values}
        """.format(
            children_acl_inherit_table_rel=children_acl_inherit_table_rel,
            children_field=self.env[children_obj._get_security_model_acl()].get_acl_field(),
            values=",".join(inherit_children_acl_list)
        )
        self.env.cr.execute(sql_query)
        _logger.debug("--- insert children_acl_id %s in %s seconds ---" % (len(children_ids), time.time() - start_time))


    @api.model
    def _delete_children_acl_id(self, children_ids, children_model, acl_id):
        if not children_ids or not children_model or not acl_id:
            return
        start_time = time.time()
        children_obj = self.env[children_model]
        children_acl_inherit_table_rel = children_obj._get_security_table_acl() + "_inherit_rel"
        sql_query = """
            DELETE FROM {children_acl_inherit_table_rel} WHERE {children_field} IN ({children_ids}) AND acl_id = {acl_id}
        """.format(
            children_acl_inherit_table_rel=children_acl_inherit_table_rel,
            children_field=self.env[children_obj._get_security_model_acl()].get_acl_field(),
            children_ids=",".join(map(str, children_ids)),
            acl_id=acl_id
        )
        self.env.cr.execute(sql_query)
        _logger.debug("--- delete children_acl_id %s in %s seconds ---" % (len(children_ids), time.time() - start_time))

    ####################################################################################################################


    ####################################################################################################################
    # Algoritmo di verifica acl
    ####################################################################################################################

    def _filter_access(self, operation):
        if self.check_access_rights(operation, False):
            records = self._filter_access_rules(operation)
            if self.skip_security():
                return records
            return self & self.browse(self._get_access_ids(records.ids, operation))
        return self.env[self._get_security_model()]


    def _check_access(self, operation):
        if self.skip_security():
            return None
        access_ids = self._get_access_ids(self.ids, operation)
        for id in self.ids:
            if id not in access_ids:
                raise AccessError(_(
                    "The requested operation cannot be completed due to group security restrictions. "
                    "Please contact your system administrator.\n\n(Document type: %s, Operation: %s)"
                ) % (self._description, operation))


    # Restituisce l'insieme degli id delle istanze per cui l'utente corrente è abilitato ad eseguire l'operazione
    # richiesta.
    @api.model
    def _get_access_ids(self, ids, operation):
        query = Query(None, self._table)
        alias_dict = {}
        self._set_joins(query, alias_dict, operation)
        self._set_conditions(query, alias_dict, operation)
        if ids:
            query.add_where("{table}.id IN ({ids})".format(
                table=self._table,
                ids=", ".join(str(id) for id in ids)
            ))
        query_str, params = query.select("DISTINCT {table}.id".format(
            table=self._table
        ))
        self.env.cr.execute(query_str, params)
        access_ids = [row[0] for row in self.env.cr.fetchall()]
        return access_ids


    # Il metodo _set_joins si occupa di settare nella query i join tra la tabella del modello che estende la classe
    # Security e la tabella delle acl. In realtà le tabelle coinvolte nelle acl sono due, una dove sono contenute le acl
    # e un'altra dove vengono memorizzati i collegamenti tra il modello e le acl. Se poi il modello presenta una
    # relazione parent->child allora è necessario definire settare altri due join per comprendere i permessi ereditati.
    @api.model
    def _set_joins(self, query, alias_dict, operation="read"):
        self._set_acl_joins(query, alias_dict, "user", False)
        self._set_acl_joins(query, alias_dict, "user", True)


    @api.model
    def _set_acl_joins(self, query, alias_dict, join_prefix, inherit):
        if inherit:
            table_acl = self._get_security_inherit_table_acl()
        else:
            table_acl = self._get_security_table_acl()
        table_acl_rel = "%s_acl_%srel" % (self._get_security_table(), "inherit_" if inherit else "")
        table_acl_rel_alias = query.left_join(
            alias_dict.get(self._get_security_table(), self._get_security_table()),
            "id",
            table_acl_rel,
            "%s" % self.env[self._get_security_model() + ".acl"].get_acl_field(),
            "%s_acl_%srel" % (join_prefix, "inherit_" if inherit else "")
        )
        table_acl_alias = query.left_join(
            table_acl_rel_alias,
            "acl_id",
            table_acl,
            "id",
            "%s_acl" % join_prefix
        )
        alias_dict[self._get_acl_rel_alias_key(join_prefix, inherit)] = table_acl_rel_alias
        alias_dict[self._get_acl_alias_key(join_prefix, inherit)] = table_acl_alias


    # Il metodo _set_conditions si occupa di settare nella query le condizioni per verificare che l'utente corrente
    # abbia il permesso definito nel parametro
    @api.model
    def _set_conditions(self, query, alias_dict, operation="read"):
        conditions = self._get_conditions(alias_dict, operation)
        query.add_where("(({conditions}))".format(conditions=") OR (".join(conditions)))


    @api.model
    def _get_conditions(self, alias_dict, operation):
        conditions = []
        conditions.append(self._get_author_conditions(alias_dict))
        conditions.append(self._get_user_acl_conditions(alias_dict, operation, False))
        conditions.append(self._get_user_acl_conditions(alias_dict, operation, True))
        return conditions


    # Restituisce la condizione per verificare che l'utente corrente sia autore dell'istanza
    @api.model
    def _get_author_conditions(self, alias_dict):
        return """{table}.owner_id = {uid}""".format(
            table=alias_dict.get(self._get_security_table(), self._get_security_table()),
            uid=self.env.uid
        )


    # Restituisce la condizione per verificare che l'utente corrente abbia il permesso ricercato nella acl
    @api.model
    def _get_user_acl_conditions(self, alias_dict, operation="read", inherit=True):
        conditions = """
            {table_acl}.perm_{operation} = TRUE AND
            {table_acl}.res_model = '{model}' AND
            {table_acl}.res_id = {uid}
        """.format(
            table_acl=alias_dict[self._get_acl_alias_key("user", inherit)],
            operation=operation,
            model="res_users",
            uid=self.env.uid
        )
        if not inherit:
            return conditions
        conditions += """
            AND {table}.inherit_acl = TRUE
        """.format(
            table=alias_dict.get(self._get_security_table(), self._get_security_table())
        )
        return conditions


    @api.model
    def _get_acl_alias_key(self, join_prefix, inherit):
        if inherit:
            return "table_%s_acl_%s" % (join_prefix, "inherit")
        else:
            return "table_%s_acl" % join_prefix


    @api.model
    def _get_acl_rel_alias_key(self, join_prefix, inherit):
        if inherit:
            return "table_%s_acl_%s_rel" % (join_prefix, "inherit")
        else:
            return "table_%s_acl_rel" % join_prefix


    @api.model
    def _get_security_table(self):
        return self._table


    @api.model
    def _get_security_table_acl(self):
        return "%s_acl" % (self._get_security_table(),)


    @api.model
    def _get_security_column(self):
        return "id"


    @api.model
    def _get_security_model(self):
        return self._name


    @api.model
    def _get_security_model_acl(self):
        return "%s.acl" % (self._get_security_model(),)


    @api.model
    def _get_security_inherit_model(self):
        if self._parent_field and self._parent_model:
            return self.env[self._parent_model]._name
        else:
            return self._get_security_model()


    @api.model
    def _get_security_inherit_table(self):
        if self._parent_field and self._parent_model:
            return self.env[self._parent_model]._table
        else:
            return self._get_security_table()


    @api.model
    def _get_security_inherit_model_acl(self):
        return "%s.acl" % (self._get_security_inherit_model(),)


    @api.model
    def _get_security_inherit_table_acl(self):
        return "%s_acl" % (self._get_security_inherit_table(),)


    @api.model
    def skip_security(self):
        return self.env.su or self.env.user.id == SUPERUSER_ID or self._context.get("skip_security", False)