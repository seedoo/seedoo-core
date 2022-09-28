from odoo import models, fields
import time
import logging

_logger = logging.getLogger(__name__)


class ProtocolloFilters(models.Model):
    _inherit = "sd.protocollo.protocollo"

    filter_protocolli_da_fascicolare = fields.Boolean(
        string="Protocolli da Inviare",
        compute="_compute_filter_protocolli_da_fascicolare",
        search="_search_filter_protocolli_da_fascicolare"
    )

    def _compute_filter_protocolli_da_fascicolare(self):
        self._compute_filter_value("protocolli_da_fascicolare")

    def _search_filter_protocolli_da_fascicolare(self, operator=None, operand=None):
        return self._search_filter_value(operator, operand, "protocolli_da_fascicolare")

    def _execute_query_protocolli_da_fascicolare(self, count=False):
        start_time = time.time()
        sql_query = """
            SELECT {select_type}
            FROM (
                SELECT spp.id AS id
                FROM sd_protocollo_protocollo spp
                WHERE spp.state IN ('registrato', 'annullato') AND
                      spp.active = TRUE AND
                      spp.protocollatore_stato = 'lavorazione' AND
                      spp.protocollatore_id = {uid} AND
                      spp.company_id IN ({company_ids})

                UNION

                SELECT spp.id AS id
                FROM sd_protocollo_protocollo spp, sd_protocollo_assegnazione spa
                WHERE spp.id = spa.protocollo_id AND
                      spp.state IN ('registrato', 'annullato') AND
                      spp.active = TRUE AND
                      spa.assegnatario_tipologia = 'utente' AND
                      spa.tipologia = 'competenza' AND
                      spa.assegnatario_utente_id = {uid} AND
                      spa.state IN ('preso_in_carico', 'letto_co') AND
                      spp.company_id IN ({company_ids})
            ) as p
            WHERE p.id IN (
                SELECT DISTINCT spp.id
                FROM sd_protocollo_protocollo spp 
                INNER JOIN sd_dms_document sdd ON sdd.protocollo_id = spp.id 
                LEFT JOIN sd_fascicolo_fascicolo_sd_dms_document_rel sffsddr ON sffsddr.documento_id = sdd.id
                WHERE sffsddr.documento_id IS NULL AND
                      spp.active = TRUE AND
                      spp.company_id IN ({company_ids})
            )                           
            """.format(
            select_type=("COUNT(DISTINCT(p.id))" if count else "DISTINCT(p.id)"),
            uid=self.env.uid,
            company_ids=", ".join(str(company_id) for company_id in self.env["res.company"].get_selected_company_ids())
        )
        self.env.cr.execute(sql_query)
        if count:
            result = self.env.cr.fetchall()[0][0]
            _logger.debug("--- count query_protocolli_da_fascicolare %s seconds ---" % (time.time() - start_time))
            return result
        results = [result[0] for result in self.env.cr.fetchall()]
        _logger.debug("--- select query_protocolli_da_fascicolare %s seconds ---" % (time.time() - start_time))
        return results
