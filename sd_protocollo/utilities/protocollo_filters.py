from odoo import models, fields, api
import time
import logging

_logger = logging.getLogger(__name__)


class ProtocolloFilters(models.Model):
    _inherit = "sd.protocollo.protocollo"

    filter_protocolli_assegnati_a_me = fields.Boolean(
        string="Protocolli Assegnati a Me",
        compute="_compute_filter_protocolli_assegnati_a_me",
        search="_search_filter_protocolli_assegnati_a_me"
    )

    filter_protocolli_in_lavorazione = fields.Boolean(
        string="Protocolli in Lavorazione",
        compute="_compute_filter_protocolli_in_lavorazione",
        search="_search_filter_protocolli_in_lavorazione"
    )

    filter_protocolli_bozza = fields.Boolean(
        string="Protocolli Bozza",
        compute="_compute_filter_protocolli_bozza",
        search="_search_filter_protocolli_bozza"
    )

    filter_protocolli_assegnati_a_me_competenza = fields.Boolean(
        string="Protocolli Assegnati a me per Competenza",
        compute="_compute_filter_protocolli_assegnati_a_me_competenza",
        search="_search_filter_protocolli_assegnati_a_me_competenza"
    )

    filter_protocolli_assegnati_mio_ufficio = fields.Boolean(
        string="Protocolli Assegnati al mio Ufficio",
        compute="_compute_filter_protocolli_assegnati_mio_ufficio",
        search="_search_filter_protocolli_assegnati_mio_ufficio"
    )

    filter_protocolli_assegnati_mio_ufficio_competenza = fields.Boolean(
        string="Protocolli Assegnati al mio Ufficio per Competenza",
        compute="_compute_filter_protocolli_assegnati_mio_ufficio_competenza",
        search="_search_filter_protocolli_assegnati_mio_ufficio_competenza"
    )

    filter_protocolli_da_assegnare = fields.Boolean(
        string="Protocolli da Assegnare",
        compute="_compute_filter_protocolli_da_assegnare",
        search="_search_filter_protocolli_da_assegnare"
    )

    filter_protocolli_da_inviare = fields.Boolean(
        string="Protocolli da Inviare",
        compute="_compute_filter_protocolli_da_inviare",
        search="_search_filter_protocolli_da_inviare"
    )

    filter_protocolli_assegnati_da_me = fields.Boolean(
        string="Protocolli Assegnati da me",
        compute="_compute_filter_protocolli_assegnati_da_me",
        search="_search_filter_protocolli_assegnati_da_me"
    )

    filter_protocolli_rifiutati = fields.Boolean(
        string="Protocolli Rifiutati",
        compute="_compute_filter_protocolli_rifiutati",
        search="_search_filter_protocolli_rifiutati"
    )

    filter_protocolli_assegnati_conoscenza = fields.Boolean(
        string="Protocolli Assegnati per Conoscenza",
        compute="_compute_filter_protocolli_assegnati_conoscenza",
        search="_search_filter_protocolli_assegnati_conoscenza"
    )

    def _compute_filter_value(self, filter_name):
        execute_query_method_name = "_execute_query_%s" % filter_name
        execute_query_method = getattr(self, execute_query_method_name)
        for rec in self:
            filter_value = False
            if rec.id in execute_query_method():
                filter_value = True
            rec["filter_%s" % filter_name] = filter_value

    def _search_filter_value(self, operator, operand, filter_name):
        execute_query_method_name = "_execute_query_%s" % filter_name
        execute_query_method = getattr(self, execute_query_method_name)
        return [("id", "in", execute_query_method())]

    # protocolli assegnati a me
    def _compute_filter_protocolli_assegnati_a_me(self):
        self._compute_filter_value("protocolli_assegnati_a_me")

    def _search_filter_protocolli_assegnati_a_me(self, operator=None, operand=None):
        return self._search_filter_value(operator, operand, "protocolli_assegnati_a_me")

    def _execute_query_protocolli_assegnati_a_me(self, count=False):
        start_time = time.time()
        sql_query = """
            SELECT {select_type}
            FROM sd_protocollo_protocollo spp, sd_protocollo_assegnazione spa
            WHERE spp.id = spa.protocollo_id AND
                  spp.active = TRUE AND
                  spp.state IN ('registrato', 'annullato') AND
                  spa.assegnatario_tipologia = 'utente' AND
                  spa.assegnatario_utente_id = {uid} AND
                  spa.state = 'assegnato' AND
                  spa.parent_id IS NULL AND
                  spp.company_id IN ({company_ids})
            """.format(
            select_type=("COUNT(DISTINCT(spp.id))" if count else "DISTINCT(spp.id)"),
            uid=self.env.uid,
            company_ids=", ".join(str(company_id) for company_id in self.env["res.company"].get_selected_company_ids())
        )
        self.env.cr.execute(sql_query)
        if count:
            result = self.env.cr.fetchall()[0][0]
            _logger.debug("--- count query_protocolli_assegnati_a_me %s seconds ---" % (time.time() - start_time))
            return result
        results = [result[0] for result in self.env.cr.fetchall()]
        _logger.debug("--- select query_protocolli_assegnati_a_me %s seconds ---" % (time.time() - start_time))
        return results

    # protocolli in lavorazione
    def _compute_filter_protocolli_in_lavorazione(self):
        self._compute_filter_value("protocolli_in_lavorazione")

    def _search_filter_protocolli_in_lavorazione(self, operator=None, operand=None):
        return self._search_filter_value(operator, operand, "protocolli_in_lavorazione")

    def _execute_query_protocolli_in_lavorazione(self, count=False):
        start_time = time.time()
        sql_query = """
            SELECT {select_type}
            FROM (
                SELECT spp.id AS id
                FROM sd_protocollo_protocollo spp
                WHERE spp.state IN ('registrato', 'annullato') AND
                      spp.active = TRUE AND
                      spp.protocollatore_id = {uid} AND
                      spp.protocollatore_stato = 'lavorazione' AND
                      spp.company_id IN ({company_ids})

                UNION ALL

                SELECT spp.id AS id
                FROM sd_protocollo_protocollo spp, sd_protocollo_assegnazione spa
                WHERE spp.id = spa.protocollo_id AND
                      spp.active = TRUE AND
                      spp.state IN ('registrato', 'annullato') AND
                      spa.state IN ('preso_in_carico', 'letto_cc', 'letto_co') AND
                      spa.assegnatario_tipologia = 'utente' AND
                      spa.assegnatario_utente_id = {uid} AND
                      spp.company_id IN ({company_ids})
            ) p
            """.format(
            select_type=("COUNT(DISTINCT(p.id))" if count else "DISTINCT(p.id)"),
            uid=self.env.uid,
            company_ids=", ".join(str(company_id) for company_id in self.env["res.company"].get_selected_company_ids())
        )
        self.env.cr.execute(sql_query)
        if count:
            result = self.env.cr.fetchall()[0][0]
            _logger.debug("--- count query_protocolli_in_lavorazione %s seconds ---" % (time.time() - start_time))
            return result
        results = [result[0] for result in self.env.cr.fetchall()]
        _logger.debug("--- select query_protocolli_in_lavorazione %s seconds ---" % (time.time() - start_time))
        return results

    # Protocolli in stato bozza
    def _compute_filter_protocolli_bozza(self):
        self._compute_filter_value("protocolli_bozza")

    def _search_filter_protocolli_bozza(self, operator=None, operand=None):
        return self._search_filter_value(operator, operand, "protocolli_bozza")

    def _execute_query_protocolli_bozza(self, count=False):
        start_time = time.time()
        sql_query = """
            SELECT {select_type}
            FROM sd_protocollo_protocollo spp
            WHERE spp.state = 'bozza' AND
                  spp.active = TRUE AND
                  spp.protocollatore_id = {uid} AND
                  spp.company_id IN ({company_ids})
            """.format(
            select_type=("COUNT(DISTINCT(spp.id))" if count else "DISTINCT(spp.id)"),
            uid=self.env.uid,
            company_ids=", ".join(str(company_id) for company_id in self.env["res.company"].get_selected_company_ids())
        )
        self.env.cr.execute(sql_query)
        if count:
            result = self.env.cr.fetchall()[0][0]
            _logger.debug("--- count query_protocolli_bozza %s seconds ---" % (time.time() - start_time))
            return result
        results = [result[0] for result in self.env.cr.fetchall()]
        _logger.debug("--- select query_protocolli_bozza %s seconds ---" % (time.time() - start_time))
        return results

    # Protocolli assegnati a me per competenza
    def _compute_filter_protocolli_assegnati_a_me_competenza(self):
        self._compute_filter_value("protocolli_assegnati_a_me")

    def _search_filter_protocolli_assegnati_a_me_competenza(self, operator=None, operand=None):
        return self._search_filter_value(operator, operand, "protocolli_assegnati_a_me_competenza")

    def _execute_query_protocolli_assegnati_a_me_competenza(self, count=False):
        start_time = time.time()
        sql_query = """
            SELECT {select_type}
            FROM sd_protocollo_protocollo spp, sd_protocollo_assegnazione spa
            WHERE spp.id = spa.protocollo_id AND
                  spp.active = TRUE AND
                  spp.state IN ('registrato', 'annullato') AND
                  spa.assegnatario_tipologia = 'utente' AND
                  spa.tipologia = 'competenza' AND
                  spa.assegnatario_utente_id = {uid} AND
                  spa.state = 'assegnato' AND
                  spa.parent_id IS NULL AND
                  spp.company_id IN ({company_ids})
            """.format(
            select_type=("COUNT(DISTINCT(spp.id))" if count else "DISTINCT(spp.id)"),
            uid=self.env.uid,
            company_ids=", ".join(str(company_id) for company_id in self.env["res.company"].get_selected_company_ids())
        )
        self.env.cr.execute(sql_query)
        if count:
            result = self.env.cr.fetchall()[0][0]
            _logger.debug("--- count query_protocolli_assegnati_a_me_competenza %s seconds ---" % (time.time() - start_time))
            return result
        results = [result[0] for result in self.env.cr.fetchall()]
        _logger.debug("--- select query_protocolli_assegnati_a_me_competenza %s seconds ---" % (time.time() - start_time))
        return results

    # Protocolli assegnati al mio ufficio
    def _compute_filter_protocolli_assegnati_mio_ufficio(self):
        self._compute_filter_value("protocolli_assegnati_mio_ufficio")

    def _search_filter_protocolli_assegnati_mio_ufficio(self, operator=None, operand=None):
        return self._search_filter_value(operator, operand, "protocolli_assegnati_mio_ufficio")

    def _execute_query_protocolli_assegnati_mio_ufficio(self, count=False):
        start_time = time.time()
        config_obj = self.env["ir.config_parameter"].sudo()
        assegnazione_state_list = "('assegnato')"
        if bool(config_obj.get_param("sd_protocollo.abilita_lettura_assegnazione_competenza")):
            assegnazione_state_list = "('assegnato', 'preso_in_carico', 'lavorazione_completata')"
        sql_query = """
            SELECT {select_type}
            FROM sd_protocollo_protocollo spp, sd_protocollo_assegnazione spa, fl_set_set_res_users_rel fssrur
            WHERE spp.id = spa.protocollo_id AND
                  spp.active = TRUE AND
                  spp.imported_other_software IS NOT TRUE AND
                  spa.assegnatario_ufficio_id = fssrur.set_id AND
                  fssrur.user_id = {uid} AND
                  spp.state IN ('registrato', 'annullato') AND
                  spa.assegnatario_tipologia = 'ufficio' AND
                  spa.state IN {assegnazione_state_list} AND
                  spp.company_id IN ({company_ids}) AND
                  spa.id NOT IN (
                      SELECT spa2.parent_id AS id
                      FROM sd_protocollo_protocollo spp2, sd_protocollo_assegnazione spa2
                      WHERE spp2.id = spa2.protocollo_id AND
                            spp2.active = TRUE AND
                            spa2.assegnatario_utente_id = {uid} AND
                            spp2.state IN ('registrato', 'annullato') AND
                            spa2.assegnatario_tipologia = 'utente' AND
                            spa2.parent_id IS NOT NULL AND
                            spa2.state NOT IN ('assegnato') AND
                            spp2.company_id IN ({company_ids})
                      )
            """.format(
            select_type=("COUNT(DISTINCT(spp.id))" if count else "DISTINCT(spp.id)"),
            uid=self.env.uid,
            assegnazione_state_list=assegnazione_state_list,
            company_ids=", ".join(str(company_id) for company_id in self.env["res.company"].get_selected_company_ids())
        )
        self.env.cr.execute(sql_query)
        if count:
            result = self.env.cr.fetchall()[0][0]
            _logger.debug("--- count query_protocolli_assegnati_mio_ufficio %s seconds ---" % (time.time() - start_time))
            return result
        results = [result[0] for result in self.env.cr.fetchall()]
        _logger.debug("--- select query_protocolli_assegnati_mio_ufficio %s seconds ---" % (time.time() - start_time))
        return results

    # Protocolli assegnati al mio ufficio per competenza
    def _compute_filter_protocolli_assegnati_mio_ufficio_competenza(self):
        self._compute_filter_value("protocolli_assegnati_mio_ufficio_competenza")

    def _search_filter_protocolli_assegnati_mio_ufficio_competenza(self, operator=None, operand=None):
        return self._search_filter_value(operator, operand, "protocolli_assegnati_mio_ufficio_competenza")

    def _execute_query_protocolli_assegnati_mio_ufficio_competenza(self, count=False):
        start_time = time.time()
        config_obj = self.env["ir.config_parameter"].sudo()
        assegnazione_state_list = "('assegnato')"
        if bool(config_obj.get_param("sd_protocollo.abilita_lettura_assegnazione_competenza")):
            assegnazione_state_list = "('assegnato', 'preso_in_carico', 'lavorazione_completata')"
        sql_query = """
            SELECT {select_type}
            FROM sd_protocollo_protocollo spp, sd_protocollo_assegnazione spa, fl_set_set_res_users_rel fssrur
            WHERE spp.id = spa.protocollo_id AND
                  spp.active = TRUE AND
                  spa.assegnatario_ufficio_id = fssrur.set_id AND
                  fssrur.user_id = {uid} AND
                  spp.state IN ('registrato', 'annullato') AND
                  spa.assegnatario_tipologia = 'ufficio' AND
                  spa.tipologia = 'competenza' AND
                  spa.state IN {assegnazione_state_list} AND
                  spp.company_id IN ({company_ids}) AND
                  spa.id NOT IN (
                      SELECT spa2.assegnatario_utente_parent_id AS id
                      FROM sd_protocollo_protocollo spp2, sd_protocollo_assegnazione spa2
                      WHERE spp2.id = spa2.protocollo_id AND
                            spp2.active = TRUE AND
                            spp2.state IN ('registrato', 'annullato') AND
                            spa2.tipologia = 'competenza' AND
                            spa2.assegnatario_utente_id = {uid} AND
                            spa2.assegnatario_tipologia = 'utente' AND
                            spa2.parent_id IS NOT NULL AND
                            spa2.state NOT IN ('assegnato') AND
                            spp2.company_id IN ({company_ids})
                      )
            """.format(
            select_type=("COUNT(DISTINCT(spp.id))" if count else "DISTINCT(spp.id)"),
            uid=self.env.uid,
            assegnazione_state_list=assegnazione_state_list,
            company_ids=", ".join(str(company_id) for company_id in self.env["res.company"].get_selected_company_ids())
        )
        self.env.cr.execute(sql_query)
        if count:
            result = self.env.cr.fetchall()[0][0]
            _logger.debug("--- count query_protocolli_assegnati_mio_ufficio_competenza %s seconds ---" % (time.time() - start_time))
            return result
        results = [result[0] for result in self.env.cr.fetchall()]
        _logger.debug("--- select query_protocolli_assegnati_mio_ufficio_competenza %s seconds ---" % (time.time() - start_time))
        return results

    # Protocolli da assegnare
    def _compute_filter_protocolli_da_assegnare(self):
        self._compute_filter_value("protocolli_da_assegnare")

    def _search_filter_protocolli_da_assegnare(self, operator=None, operand=None):
        return self._search_filter_value(operator, operand, "protocolli_da_assegnare")

    def _execute_query_protocolli_da_assegnare(self, count=False):
        start_time = time.time()
        sql_query = """
            SELECT {select_type}
            FROM sd_protocollo_protocollo spp
            WHERE spp.state IN ('registrato', 'annullato') AND
                  spp.active = TRUE AND
                  spp.protocollatore_stato = 'lavorazione' AND
                  spp.protocollatore_id = {uid} AND
                  spp.da_assegnare = TRUE AND
                  spp.company_id IN ({company_ids})
            """.format(
            select_type=("COUNT(DISTINCT(spp.id))" if count else "DISTINCT(spp.id)"),
            uid=self.env.uid,
            company_ids=", ".join(str(company_id) for company_id in self.env["res.company"].get_selected_company_ids())
        )
        self.env.cr.execute(sql_query)
        if count:
            result = self.env.cr.fetchall()[0][0]
            _logger.debug("--- count query_protocolli_da_assegnare %s seconds ---" % (time.time() - start_time))
            return result
        results = [result[0] for result in self.env.cr.fetchall()]
        _logger.debug("--- select query_protocolli_da_assegnare %s seconds ---" % (time.time() - start_time))
        return results

    # Protocolli da Inviare
    def _compute_filter_protocolli_da_inviare(self):
        self._compute_filter_value("protocolli_da_inviare")

    def _search_filter_protocolli_da_inviare(self, operator=None, operand=None):
        return self._search_filter_value(operator, operand, "protocolli_da_inviare")

    def _execute_query_protocolli_da_inviare(self, count=False):
        start_time = time.time()
        sql_query = """
            SELECT {select_type}
            FROM sd_protocollo_protocollo spp
            WHERE spp.state IN ('registrato', 'annullato') AND
                  spp.active = TRUE AND
                  spp.da_inviare = TRUE AND
                  spp.protocollatore_stato = 'lavorazione' AND
                  spp.protocollatore_id = {uid} AND
                  spp.company_id IN ({company_ids})
            """.format(
            select_type=("COUNT(DISTINCT(spp.id))" if count else "DISTINCT(spp.id)"),
            uid=self.env.uid,
            company_ids=", ".join(str(company_id) for company_id in self.env["res.company"].get_selected_company_ids())
        )
        self.env.cr.execute(sql_query)
        if count:
            result = self.env.cr.fetchall()[0][0]
            _logger.debug("--- count query_protocolli_da_inviare %s seconds ---" % (time.time() - start_time))
            return result
        results = [result[0] for result in self.env.cr.fetchall()]
        _logger.debug("--- select query_protocolli_da_inviare %s seconds ---" % (time.time() - start_time))
        return results

    # Protocolli da Inviare
    def _compute_filter_protocolli_assegnati_da_me(self):
        self._compute_filter_value("protocolli_assegnati_da_me")

    def _search_filter_protocolli_assegnati_da_me(self, operator=None, operand=None):
        return self._search_filter_value(operator, operand, "protocolli_assegnati_da_me")

    def _execute_query_protocolli_assegnati_da_me(self, count=False):
        start_time = time.time()
        sql_query = """
            SELECT {select_type}
            FROM (
                SELECT spp.id AS id
                FROM sd_protocollo_protocollo spp, sd_protocollo_assegnazione spa
                WHERE spp.id = spa.protocollo_id AND
                      spp.active = TRUE AND
                      spp.protocollatore_id = spa.assegnatore_id AND
                      spp.protocollatore_id = {uid} AND
                      spp.protocollatore_stato = 'lavorazione' AND
                      spp.state IN ('registrato', 'annullato') AND
                      spa.tipologia = 'competenza' AND
                      spa.state = 'assegnato' AND
                      spp.company_id IN ({company_ids})

                UNION

                SELECT spp.id AS id
                FROM sd_protocollo_protocollo spp, sd_protocollo_assegnazione spa1, sd_protocollo_assegnazione spa2
                WHERE spp.id = spa1.protocollo_id AND
                      spp.id = spa2.protocollo_id AND
                      spp.active = TRUE AND
                      spp.state IN ('registrato', 'annullato') AND
                      spa1.assegnatario_utente_id = {uid} AND
                      spa1.tipologia = 'competenza' AND
                      spa1.state = 'preso_in_carico' AND
                      spa2.assegnatore_id = {uid} AND
                      spa2.tipologia = 'competenza' AND
                      spa2.state = 'assegnato' AND
                      spp.company_id IN ({company_ids})
            ) p
            """.format(
            select_type=("COUNT(DISTINCT(p.id))" if count else "DISTINCT(p.id)"),
            uid=self.env.uid,
            company_ids=", ".join(str(company_id) for company_id in self.env["res.company"].get_selected_company_ids())
        )
        self.env.cr.execute(sql_query)
        if count:
            result = self.env.cr.fetchall()[0][0]
            _logger.debug("--- count query_protocolli_assegnati_da_me %s seconds ---" % (time.time() - start_time))
            return result
        results = [result[0] for result in self.env.cr.fetchall()]
        _logger.debug("--- select query_protocolli_assegnati_da_me %s seconds ---" % (time.time() - start_time))
        return results

    # Protocolli Rifiutati
    def _compute_filter_protocolli_rifiutati(self):
        self._compute_filter_value("protocolli_rifiutati")

    def _search_filter_protocolli_rifiutati(self, operator=None, operand=None):
        return self._search_filter_value(operator, operand, "protocolli_rifiutati")

    def _execute_query_protocolli_rifiutati(self, count=False):
        start_time = time.time()
        sql_query = """
            SELECT {select_type}
            FROM (
                SELECT spp.id AS id
                FROM sd_protocollo_protocollo spp, sd_protocollo_assegnazione spa
                WHERE spp.id = spa.protocollo_id AND
                      spp.active = TRUE AND
                      spp.protocollatore_id = spa.assegnatore_id AND
                      spp.protocollatore_id = {uid} AND
                      spp.protocollatore_stato = 'lavorazione' AND
                      spp.state IN ('registrato', 'annullato') AND
                      spa.tipologia = 'competenza' AND
                      spa.state = 'rifiutato' AND
                      spp.company_id IN ({company_ids})

                UNION

                SELECT spp.id AS id
                FROM sd_protocollo_protocollo spp, sd_protocollo_assegnazione spa1, sd_protocollo_assegnazione spa2
                WHERE spp.id = spa1.protocollo_id AND
                      spp.id = spa2.protocollo_id AND
                      spp.active = TRUE AND
                      spp.state IN ('registrato', 'annullato') AND
                      spa1.assegnatario_utente_id = {uid} AND
                      spa1.tipologia = 'competenza' AND
                      spa1.state = 'preso_in_carico' AND
                      spa2.assegnatore_id = {uid} AND
                      spa2.tipologia = 'competenza' AND
                      spa2.state = 'rifiutato' AND
                      spp.company_id IN ({company_ids})
            ) p
            """.format(
            select_type=("COUNT(DISTINCT(p.id))" if count else "DISTINCT(p.id)"),
            uid=self.env.uid,
            company_ids=", ".join(str(company_id) for company_id in self.env["res.company"].get_selected_company_ids())
        )
        self.env.cr.execute(sql_query)
        if count:
            result = self.env.cr.fetchall()[0][0]
            _logger.debug("--- count query_protocolli_rifiutati %s seconds ---" % (time.time() - start_time))
            return result
        results = [result[0] for result in self.env.cr.fetchall()]
        _logger.debug("--- select query_protocolli_rifiutati %s seconds ---" % (time.time() - start_time))
        return results

    # Protocolli Assegnati per Conoscenza
    def _compute_filter_protocolli_assegnati_conoscenza(self):
        self._compute_filter_value("protocolli_assegnati_conoscenza")

    def _search_filter_protocolli_assegnati_conoscenza(self, operator=None, operand=None):
        return self._search_filter_value(operator, operand, "protocolli_assegnati_conoscenza")

    def _execute_query_protocolli_assegnati_conoscenza(self, count=False):
        start_time = time.time()
        sql_query = """
            SELECT {select_type}
            FROM (
                (
                    SELECT spp.id AS id
                    FROM sd_protocollo_protocollo spp, sd_protocollo_assegnazione spa, fl_set_set_res_users_rel fssrur
                    WHERE spp.id = spa.protocollo_id AND
                          spp.active = TRUE AND
                          spa.assegnatario_ufficio_id = fssrur.set_id AND
                          fssrur.user_id = {uid} AND
                          spp.state IN ('registrato', 'annullato') AND
                          spa.assegnatario_tipologia = 'ufficio' AND
                          spa.tipologia = 'conoscenza' AND
                          spa.state IN ('assegnato', 'letto_co', 'lavorazione_completata') AND
                          spp.company_id IN ({company_ids})

                    EXCEPT

                    SELECT spp.id AS id
                    FROM sd_protocollo_protocollo spp, sd_protocollo_assegnazione spa
                    WHERE spp.id = spa.protocollo_id AND
                          spp.active = TRUE AND
                          spa.assegnatario_utente_id = {uid} AND
                          spp.state IN ('registrato', 'annullato') AND
                          spa.assegnatario_tipologia = 'utente' AND
                          spa.tipologia = 'conoscenza' AND
                          spa.state IN ('letto_co', 'lavorazione_completata') AND
                          spa.parent_id IS NOT NULL AND
                          spp.company_id IN ({company_ids})
                )

                UNION

                SELECT spp.id AS id
                FROM sd_protocollo_protocollo spp, sd_protocollo_assegnazione spa
                WHERE spp.id = spa.protocollo_id AND
                      spp.active = TRUE AND
                      spp.state IN ('registrato', 'annullato') AND
                      spa.assegnatario_utente_id = {uid} AND
                      spa.assegnatario_tipologia = 'utente' AND
                      spa.tipologia = 'conoscenza' AND
                      spa.state = 'assegnato' AND
                      spa.parent_id IS NULL AND
                      spp.company_id IN ({company_ids})

            ) p
            """.format(
            select_type=("COUNT(DISTINCT(p.id))" if count else "DISTINCT(p.id)"),
            uid=self.env.uid,
            company_ids=", ".join(str(company_id) for company_id in self.env["res.company"].get_selected_company_ids())
        )
        self.env.cr.execute(sql_query)
        if count:
            result = self.env.cr.fetchall()[0][0]
            _logger.debug("--- count query_protocolli_assegnati_conoscenza %s seconds ---" % (time.time() - start_time))
            return result
        results = [result[0] for result in self.env.cr.fetchall()]
        _logger.debug("--- select query_protocolli_assegnati_conoscenza %s seconds ---" % (time.time() - start_time))
        return results