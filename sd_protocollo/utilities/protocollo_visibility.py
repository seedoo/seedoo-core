from odoo import models, api
import logging

_logger = logging.getLogger(__name__)


class ProtocolloVisibility(models.Model):
    _inherit = "sd.protocollo.protocollo"

    @api.model
    def aggiorna_acl(self, evento, protocollo_id):
        evento_list = [
            "creazione",
            "riservato",
            "registrazione",
            "assegnazione",
            "rifiuto"
        ]
        if not (evento in evento_list):
            _logger.error("L'evento %s non è gestito fra gli eventi di aggiornamento ACL del protocollo" % evento)
            return
        if evento == "creazione":
            if not protocollo_id:
                _logger.error("Il parametro protocollo_id è obbligatorio nell'evento di creazione")
            self._aggiorna_acl(protocollo_id, visibilita_min="xl")
        elif evento == "riservato":
            if not protocollo_id:
                _logger.error("Il parametro protocollo_id è obbligatorio nell'evento di creazione")
            self._aggiorna_acl(protocollo_id, visibilita_min="xl")
        elif evento == "registrazione":
            if not protocollo_id:
                _logger.error("Il parametro protocollo_id è obbligatorio nell'evento di registrazione")
            self._aggiorna_acl(protocollo_id, visibilita_max="l")
        elif evento == "assegnazione":
            if not protocollo_id:
                _logger.error("Il parametro protocollo_id è obbligatorio nell'evento di assegnazione")
            self._aggiorna_acl(protocollo_id)
        elif evento == "rifiuto":
            if not protocollo_id:
                _logger.error("Il parametro protocollo_id è obbligatorio nell'evento di rifiuto assegnazione")
            self._aggiorna_acl(protocollo_id)

    @api.model
    def _aggiorna_acl(self, protocollo_id, user_id=None, visibilita_min=None, visibilita_max=None):
        user_ids = []
        # visibilità XS
        if visibilita_min in [None, "xs"]:
            acl_xs_user_ids = self._search_acl_user_ids(protocollo_id, "xs")
            xs_user_ids = self._get_visibilita_xs_user_ids(protocollo_id, user_id)
            self._update_acl_user_ids(protocollo_id, list(set(xs_user_ids) - set(acl_xs_user_ids)), "xs")
            self._unlink_acl_user_ids(protocollo_id, list(set(acl_xs_user_ids) - set(xs_user_ids)), "xs")
            user_ids = xs_user_ids
        if visibilita_max == "xs":
            return
        # visibilità S
        if visibilita_min in [None, "xs", "s"]:
            acl_s_user_ids = self._search_acl_user_ids(protocollo_id, "s")
            s_user_ids = self._get_visibilita_s_user_ids(protocollo_id, user_id)
            s_user_ids = list(set(s_user_ids) - set(user_ids))
            self._update_acl_user_ids(protocollo_id, list(set(s_user_ids) - set(acl_s_user_ids)), "s")
            self._unlink_acl_user_ids(protocollo_id, list(set(acl_s_user_ids) - set(s_user_ids)), "s")
            user_ids += s_user_ids
        if visibilita_max == "s":
            return
        # visibilità M
        if visibilita_min in [None, "xs", "s", "m"]:
            acl_m_user_ids = self._search_acl_user_ids(protocollo_id, "m")
            m_user_ids = self._get_visibilita_m_user_ids(protocollo_id, user_id)
            m_user_ids = list(set(m_user_ids) - set(user_ids))
            self._update_acl_user_ids(protocollo_id, list(set(m_user_ids) - set(acl_m_user_ids)), "m")
            self._unlink_acl_user_ids(protocollo_id, list(set(acl_m_user_ids) - set(m_user_ids)), "m")
            user_ids += m_user_ids
        if visibilita_max == "m":
            return
        # visibilità L
        if visibilita_min in [None, "xs", "s", "m", "l"]:
            acl_l_user_ids = self._search_acl_user_ids(protocollo_id, "l")
            l_user_ids = self._get_visibilita_l_user_ids(protocollo_id, user_id)
            l_user_ids = list(set(l_user_ids) - set(user_ids))
            self._update_acl_user_ids(protocollo_id, list(set(l_user_ids) - set(acl_l_user_ids)), "l")
            self._unlink_acl_user_ids(protocollo_id, list(set(acl_l_user_ids) - set(l_user_ids)), "l")
            user_ids += l_user_ids
        if visibilita_max == "l":
            return
        # visibilità XL
        if visibilita_min in [None, "xs", "s", "m", "l", "xl"]:
            acl_xl_user_ids = self._search_acl_user_ids(protocollo_id, "xl")
            xl_user_ids = self._get_visibilita_xl_user_ids(protocollo_id, user_id)
            xl_user_ids = list(set(xl_user_ids) - set(user_ids))
            self._update_acl_user_ids(protocollo_id, list(set(xl_user_ids) - set(acl_xl_user_ids)), "xl")
            self._unlink_acl_user_ids(protocollo_id, list(set(acl_xl_user_ids) - set(xl_user_ids)), "xl")
            user_ids += xl_user_ids
        if visibilita_max == "xl":
            return

    @api.model
    def _search_acl_user_ids(self, protocollo_id, visibilita):
        acl_data_list = self.env["sd.dms.document.acl"].search_read([
            ("protocollo_id", "=", protocollo_id),
            ("protocollo_visibility", "=", visibilita),
            ("module_id", "=", self.env.ref("base.module_sd_protocollo").id),
            ("res_model", "=", "res_users"),
            ("create_system", "=", True)
        ], ["res_id"])
        acl_user_ids = [acl_data["res_id"] for acl_data in acl_data_list]
        return acl_user_ids

    @api.model
    def _update_acl_user_ids(self, protocollo_id, user_ids, visibilita):
        acl_obj = self.env["sd.dms.document.acl"]
        for user_id in user_ids:
            acl = acl_obj.search([
                ("protocollo_id", "=", protocollo_id),
                ("module_id", "=", self.env.ref("base.module_sd_protocollo").id),
                ("res_model", "=", "res_users"),
                ("res_id", "=", user_id),
                ("create_system", "=", True)
            ])
            if acl:
                acl.write({
                    "protocollo_visibility": visibilita
                })
            else:
                # il metodo create è esteso nel file sd_dms_document_acl.py per gestire in maniera automatica la
                # associazione della acl creata a tutti i documenti del protocollo relativo al value protocollo_id
                acl_obj.create({
                    "protocollo_id": protocollo_id,
                    "protocollo_visibility": visibilita,
                    "module_id": self.env.ref("base.module_sd_protocollo").id,
                    "res_model": "res_users",
                    "res_id": user_id,
                    "perm_create": False,
                    "perm_read": True,
                    "perm_write": True,
                    "perm_delete": False,
                    "create_system": True
                })

    @api.model
    def _unlink_acl_user_ids(self, protocollo_id, user_ids, visibilita):
        acl_obj = self.env["sd.dms.document.acl"]
        for user_id in user_ids:
            domain = [
                ("protocollo_id", "=", protocollo_id),
                ("protocollo_visibility", "=", visibilita),
                ("module_id", "=", self.env.ref("base.module_sd_protocollo").id),
                ("res_model", "=", "res_users"),
                ("res_id", "=", user_id),
                ("create_system", "=", True)
            ]
            acl = acl_obj.search(domain)
            if acl:
                acl.unlink()

    @api.model
    def _get_visibilita_xs_user_ids(self, protocollo_id, user_id=None):
        group_ids = [
            self.env.ref("sd_protocollo.group_sd_protocollo_visibilita_xs").id,
            self.env.ref("sd_protocollo.group_sd_protocollo_visibilita_s").id,
            self.env.ref("sd_protocollo.group_sd_protocollo_visibilita_m").id,
            self.env.ref("sd_protocollo.group_sd_protocollo_visibilita_l").id,
            self.env.ref("sd_protocollo.group_sd_protocollo_visibilita_xl").id
        ]
        # Per i seguenti due casi non è necessario fare una query per recuperare gli id dei protocolli per cui dovrà
        # essere aggiunta una acl XS in quanto l'algoritmo di visibilità stesso garantisce l'accesso alle istanze il cui
        # create_uid coincide con l'utente corrente:
        # - bozze protocollo create da se stesso
        # - protocolli registrati da se stesso

        # Per i seguenti casi è invece necessaria una query
        # - protocolli registrati e da lui assegnati
        # - protocolli registrati e a lui assegnati
        # - protocolli registrati, a lui assegnati e presi in carico
        # - protocolli registrati e assegnati al suo ufficio
        # - protocolli registrati, assegnati al suo ufficio e presi in carico
        # - ESCLUSIONE protocolli registrati da un altro utente, a lui assegnati e da lui rifiutati
        # - ESCLUSIONE protocolli registrati da un altro utente, assegnati al suo ufficio e rifiutati da lui o da un
        #   altro utente dell’ufficio stesso
        sql_query = """
            SELECT DISTINCT(u.id)
            FROM (
                SELECT DISTINCT(rsur.uid) AS id
                FROM sd_protocollo_protocollo spp, 
                     sd_protocollo_assegnazione spa, 
                     res_groups_users_rel rsur
                WHERE spp.id = spa.protocollo_id AND
                      spp.active = TRUE AND 
                      spp.state IN ('registrato', 'annullato') AND
                      spa.assegnatario_tipologia = 'utente' AND
                      spa.assegnatario_utente_id = rsur.uid AND
                      rsur.gid IN ({group_ids}) AND
                      rsur.uid NOT IN (SELECT rsur2.uid FROM res_groups_users_rel rsur2 WHERE rsur2.gid = {exclude_group_id}) AND
                      spa.state <> 'rifiutato' AND 
                      spa.parent_id IS NULL AND
                      spp.id = {protocollo_id} AND
                      {user_condition}
                
                UNION
                
                SELECT DISTINCT(rsur.uid) AS id
                FROM sd_protocollo_protocollo spp, 
                     sd_protocollo_assegnazione spa, 
                     fl_set_set_res_users_rel fssrur,
                     res_groups_users_rel rsur
                WHERE spp.id = spa.protocollo_id AND
                      spa.assegnatario_ufficio_id = fssrur.set_id AND
                      fssrur.user_id = rsur.uid AND
                      rsur.gid IN ({group_ids}) AND
                      rsur.uid NOT IN (SELECT rsur2.uid FROM res_groups_users_rel rsur2 WHERE rsur2.gid = {exclude_group_id}) AND
                      spp.active = TRUE AND
                      spp.state IN ('registrato', 'annullato') AND
                      spa.assegnatario_tipologia = 'ufficio' AND
                      spa.state <> 'rifiutato' AND 
                      spp.id = {protocollo_id} AND
                      {user_condition}
            ) u
            """.format(
            group_ids=",".join(str(group_id) for group_id in group_ids),
            exclude_group_id=self.env.ref("sd_protocollo.group_sd_protocollo_superadmin").id,
            user_condition="rsur.uid = %s" % user_id if user_id else "rsur.uid IS NOT NULL",
            protocollo_id=protocollo_id
        )
        self.env.cr.execute(sql_query)
        xs_user_ids = [result[0] for result in self.env.cr.fetchall()]

        # - protocolli registrati di cui lui o il suo ufficio è il mittente
        sql_query = """
            SELECT DISTINCT(u.id)
            FROM (
                SELECT DISTINCT(rsur.uid) AS id
                FROM sd_protocollo_protocollo spp, 
                     res_groups_users_rel rsur
                WHERE spp.active = TRUE AND
                      spp.state IN ('registrato', 'annullato') AND
                      spp.mittente_interno_utente_id = rsur.uid AND
                      rsur.gid IN ({group_ids}) AND
                      rsur.uid NOT IN (SELECT rsur2.uid FROM res_groups_users_rel rsur2 WHERE rsur2.gid = {exclude_group_id}) AND
                      spp.id = {protocollo_id} AND
                      {user_condition}

                UNION

                SELECT DISTINCT(rsur.uid) AS id
                FROM sd_protocollo_protocollo spp, 
                     fl_set_set_res_users_rel fssrur,
                     res_groups_users_rel rsur
                WHERE spp.mittente_interno_ufficio_id = fssrur.set_id AND
                      fssrur.user_id = rsur.uid AND
                      rsur.gid IN ({group_ids}) AND
                      rsur.uid NOT IN (SELECT rsur2.uid FROM res_groups_users_rel rsur2 WHERE rsur2.gid = {exclude_group_id}) AND
                      spp.active = TRUE AND
                      spp.state IN ('registrato', 'annullato') AND
                      spp.id = {protocollo_id} AND
                      {user_condition}
            ) u
            """.format(
            group_ids=",".join(str(group_id) for group_id in group_ids),
            exclude_group_id=self.env.ref("sd_protocollo.group_sd_protocollo_superadmin").id,
            user_condition="rsur.uid = %s" % user_id if user_id else "rsur.uid IS NOT NULL",
            protocollo_id=protocollo_id
        )
        self.env.cr.execute(sql_query)
        xs_user_ids.extend([result[0] for result in self.env.cr.fetchall()])

        return xs_user_ids

    @api.model
    def _get_visibilita_s_user_ids(self, protocollo_id, user_id=None):
        group_ids = [
            self.env.ref("sd_protocollo.group_sd_protocollo_visibilita_s").id,
            self.env.ref("sd_protocollo.group_sd_protocollo_visibilita_m").id,
            self.env.ref("sd_protocollo.group_sd_protocollo_visibilita_l").id,
            self.env.ref("sd_protocollo.group_sd_protocollo_visibilita_xl").id
        ]
        # - protocolli registrati dal mio ufficio
        sql_query = """
            SELECT DISTINCT(rsur.uid)
            FROM sd_protocollo_protocollo spp, 
                 fl_set_set_res_users_rel fssrur,
                 res_groups_users_rel rsur
            WHERE spp.protocollatore_ufficio_id = fssrur.set_id AND
                  fssrur.user_id = rsur.uid AND
                  rsur.gid IN ({group_ids}) AND
                  rsur.uid NOT IN (SELECT rsur2.uid FROM res_groups_users_rel rsur2 WHERE rsur2.gid = {exclude_group_id}) AND
                  spp.active = TRUE AND
                  spp.state IN ('registrato', 'annullato') AND
                  spp.riservato = FALSE AND
                  spp.id = {protocollo_id} AND
                  {user_condition}
            """.format(
            group_ids=",".join(str(group_id) for group_id in group_ids),
            exclude_group_id=self.env.ref("sd_protocollo.group_sd_protocollo_superadmin").id,
            user_condition="rsur.uid = %s" % user_id if user_id else "rsur.uid IS NOT NULL",
            protocollo_id=protocollo_id
        )
        self.env.cr.execute(sql_query)
        s_user_ids = [result[0] for result in self.env.cr.fetchall()]
        return s_user_ids

    @api.model
    def _get_visibilita_m_user_ids(self, protocollo_id, user_id=None):
        group_ids = [
            self.env.ref("sd_protocollo.group_sd_protocollo_visibilita_m").id,
            self.env.ref("sd_protocollo.group_sd_protocollo_visibilita_l").id,
            self.env.ref("sd_protocollo.group_sd_protocollo_visibilita_xl").id
        ]
        # - protocolli assegnati ad un utente del mio ufficio
        sql_query = """
            SELECT DISTINCT(rsur.uid)
            FROM sd_protocollo_protocollo spp, 
                 sd_protocollo_assegnazione spa, 
                 fl_set_set_res_users_rel fssrur, 
                 res_groups_users_rel rsur
            WHERE spp.id = spa.protocollo_id AND
                  spp.active = TRUE AND
                  spp.state IN ('registrato', 'annullato') AND
                  spp.riservato = FALSE AND
                  spa.assegnatario_tipologia = 'utente' AND
                  spa.assegnatario_utente_parent_id = fssrur.set_id AND
                  fssrur.user_id = rsur.uid AND
                  rsur.gid IN ({group_ids}) AND
                  rsur.uid NOT IN (SELECT rsur2.uid FROM res_groups_users_rel rsur2 WHERE rsur2.gid = {exclude_group_id}) AND
                  spa.parent_id IS NULL AND
                  spa.state <> 'rifiutato' AND 
                  spp.id = {protocollo_id} AND
                  {user_condition}
            """.format(
            group_ids=",".join(str(group_id) for group_id in group_ids),
            exclude_group_id=self.env.ref("sd_protocollo.group_sd_protocollo_superadmin").id,
            user_condition="rsur.uid = %s" % user_id if user_id else "rsur.uid IS NOT NULL",
            protocollo_id=protocollo_id
        )
        self.env.cr.execute(sql_query)
        m_user_ids = [result[0] for result in self.env.cr.fetchall()]
        return m_user_ids

    @api.model
    def _get_visibilita_l_user_ids(self, protocollo_id, user_id=None):
        group_ids = [
            self.env.ref("sd_protocollo.group_sd_protocollo_visibilita_l").id,
            self.env.ref("sd_protocollo.group_sd_protocollo_visibilita_xl").id
        ]
        l_user_ids = []
        sql_query = """
            SELECT DISTINCT(rsur.uid)
            FROM res_groups_users_rel rsur
            WHERE rsur.gid IN ({group_ids}) AND
                  rsur.uid NOT IN (SELECT rsur2.uid FROM res_groups_users_rel rsur2 WHERE rsur2.gid = {exclude_group_id}) AND
                  {user_condition}
            """.format(
            group_ids=",".join(str(group_id) for group_id in group_ids),
            exclude_group_id=self.env.ref("sd_protocollo.group_sd_protocollo_superadmin").id,
            user_condition="rsur.uid = %s" % user_id if user_id else "rsur.uid IS NOT NULL"
        )
        self.env.cr.execute(sql_query)
        l_ids = [result[0] for result in self.env.cr.fetchall()]

        user_obj = self.env["res.users"]
        for l_id in l_ids:
            ufficio_figlio_ids = []
            for set in user_obj.browse(l_id).fl_set_set_ids:
                ufficio_figlio_ids += set.get_all_child_set_ids()
            if not ufficio_figlio_ids:
                continue
            # - protocolli registrati da un ufficio figlio
            # - protocolli assegnati ad un ufficio figlio
            # - protocolli assegnati ad un utente di un ufficio figlio
            sql_query = """
                SELECT DISTINCT(p.id)
                FROM (
                    SELECT DISTINCT(spp.id)
                    FROM sd_protocollo_protocollo spp
                    WHERE spp.active = TRUE AND
                          spp.state IN ('registrato', 'annullato') AND
                          spp.riservato = FALSE AND
                          spp.protocollatore_ufficio_id IN ({ufficio_figlio_ids}) AND
                          spp.id = {protocollo_id}
    
                    UNION
    
                    SELECT DISTINCT(spp.id)
                    FROM sd_protocollo_protocollo spp, 
                         sd_protocollo_assegnazione spa
                    WHERE spp.id = spa.protocollo_id AND
                          spp.active = TRUE AND
                          spp.state IN ('registrato', 'annullato') AND
                          spp.riservato = FALSE AND
                          spa.assegnatario_tipologia = 'ufficio' AND
                          spa.assegnatario_ufficio_id IN ({ufficio_figlio_ids}) AND
                          spa.state <> 'rifiutato' AND 
                          spp.id = {protocollo_id}
    
                    UNION
    
                    SELECT DISTINCT(spp.id)
                    FROM sd_protocollo_protocollo spp, 
                         sd_protocollo_assegnazione spa
                    WHERE spp.id = spa.protocollo_id AND
                          spp.active = TRUE AND
                          spp.state IN ('registrato', 'annullato') AND
                          spp.riservato = FALSE AND
                          spa.assegnatario_tipologia = 'utente' AND
                          spa.assegnatario_utente_parent_id IN ({ufficio_figlio_ids}) AND
                          spa.parent_id IS NULL AND
                          spa.state <> 'rifiutato' AND
                          spp.id = {protocollo_id}
                ) p
                """.format(
                ufficio_figlio_ids=",".join(map(str, ufficio_figlio_ids)),
                protocollo_id=protocollo_id
            )
            self.env.cr.execute(sql_query)
            ids = [result[0] for result in self.env.cr.fetchall()]
            if ids:
                l_user_ids.append(l_id)
        return l_user_ids

    @api.model
    def _get_visibilita_xl_user_ids(self, protocollo_id, user_id=None):
        group_ids = [
            self.env.ref("sd_protocollo.group_sd_protocollo_visibilita_xl").id
        ]
        protocollo = self.browse(protocollo_id)
        if protocollo.riservato:
            return []
        # - tutti i protocolli non riservati
        sql_query = """
            SELECT DISTINCT(rsur.uid)
            FROM res_groups_users_rel rsur
            WHERE rsur.gid IN ({group_ids}) AND
                  rsur.uid NOT IN (SELECT rsur2.uid FROM res_groups_users_rel rsur2 WHERE rsur2.gid = {exclude_group_id}) AND
                  {user_condition} 
            """.format(
            group_ids=",".join(str(group_id) for group_id in group_ids),
            exclude_group_id=self.env.ref("sd_protocollo.group_sd_protocollo_superadmin").id,
            user_condition="rsur.uid = %s" % user_id if user_id else "rsur.uid IS NOT NULL"
        )
        self.env.cr.execute(sql_query)
        xl_user_ids = [result[0] for result in self.env.cr.fetchall()]
        return xl_user_ids