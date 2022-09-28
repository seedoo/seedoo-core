from odoo import models, fields, api
import time
import logging

_logger = logging.getLogger(__name__)


class InheritResPartnerFilters(models.Model):
    _inherit = "res.partner"

    filter_res_partner_with_digital_domicile = fields.One2many(
        string="PA/GPS/AOO/UO with digital domicile",
        comodel_name="res.partner",
        compute="_compute_filter_res_partner_with_digital_domicile",
        search="_search_filter_res_partner_with_digital_domicile"
    )

    def _compute_filter_res_partner_with_digital_domicile(self):
        for rec in self:
            filter_value = False
            if rec.id in self._execute_query_res_partner_with_digital_domicile("=", rec.name):
                filter_value = True
            rec.filter_res_partner_with_digital_domicile = filter_value

    def _search_filter_res_partner_with_digital_domicile(self, operator=None, operand=None):
        return [("id", "in", self._execute_query_res_partner_with_digital_domicile(operator, operand))]

    def _execute_query_res_partner_with_digital_domicile(self, operator, operand):
        start_time = time.time()
        sql_query = """
            SELECT DISTINCT(p.id)
            FROM (
                SELECT DISTINCT(rp.id)
                FROM res_partner rp, res_partner rp2, res_partner_digital_domicile rpdd
                WHERE rp.id = rp2.amministrazione_id AND 
                      rp2.id = rpdd.aoo_id AND
                      rp.is_pa = TRUE AND
                      rp2.is_aoo = TRUE AND 
                      rpdd.email_address {operator} '{operand}'
                
                UNION
                
                SELECT DISTINCT(rp.id)
                FROM res_partner rp, res_partner_digital_domicile rpdd
                WHERE rp.id = rpdd.aoo_id AND
                      rp.is_aoo = TRUE AND 
                      rpdd.email_address {operator} '{operand}'
                
                UNION
                
                SELECT DISTINCT(rp.id)
                FROM res_partner rp, res_partner rp2, res_partner_digital_domicile rpdd
                WHERE rp.aoo_id = rp2.id AND
                      rpdd.aoo_id = rp2.id AND
                      rp.is_uo = TRUE AND
                      rp2.is_aoo = TRUE AND  
                      rpdd.email_address {operator} '{operand}'
            ) p
            """.format(
            operator=operator,
            operand="%"+operand+"%" if operator.upper()=="ILIKE" else operand,
        )
        self.env.cr.execute(sql_query)
        results = [result[0] for result in self.env.cr.fetchall()]
        _logger.debug("--- select query_res_partner_with_digital_domicile %s seconds ---" % (time.time() - start_time))
        return results