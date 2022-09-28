from odoo import models, fields
import time
import logging

_logger = logging.getLogger(__name__)


class ProtocolloFilters(models.Model):
    _inherit = "sd.protocollo.protocollo"

    filter_protocolli_da_classificare = fields.Boolean(
        string="Protocolli da Classificare",
        compute="_compute_filter_protocolli_da_classificare",
        search="_search_filter_protocolli_da_classificare"
    )

    def _compute_filter_protocolli_da_classificare(self):
        self._compute_filter_value("protocolli_da_classificare")

    def _search_filter_protocolli_da_classificare(self, operator=None, operand=None):
        return self._search_filter_value(operator, operand, "protocolli_da_classificare")

    def _execute_query_protocolli_da_classificare(self, count=False):
        start_time = time.time()
        sql_query = """
            SELECT {select_type}
            FROM sd_protocollo_protocollo spp, sd_dms_document sdd
            WHERE spp.documento_id = sdd.id AND
                  sdd.voce_titolario_id IS NULL AND
                  spp.state IN ('registrato', 'annullato') AND
                  spp.active = TRUE AND
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
            _logger.debug("--- count query_protocolli_da_classificare %s seconds ---" % (time.time() - start_time))
            return result
        results = [result[0] for result in self.env.cr.fetchall()]
        _logger.debug("--- select query_protocolli_da_classificare %s seconds ---" % (time.time() - start_time))
        return results
