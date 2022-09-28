from odoo import models,fields
import time
import logging

_logger = logging.getLogger(__name__)


class MailFilters(models.Model):
    _inherit = "mail.mail"

    filter_mail_da_protocollare_pec = fields.Boolean(
        string="Mail da Protocollare PEC",
        compute="_compute_filter_mail_da_protocollare_pec",
        search="_search_filter_mail_da_protocollare_pec"
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

    def _compute_filter_mail_da_protocollare_pec(self):
        return self._compute_filter_value("mail_da_protocollare_pec")

    def _search_filter_mail_da_protocollare_pec(self, operator=None, operand=None):
        return self._search_filter_value(operator, operand, "mail_da_protocollare_pec")

    def _execute_query_mail_da_protocollare_pec(self, count=False):
        start_time = time.time()
        # se l'utente corrente non ha il permesso group_sd_protocollo_crea_protocollo_ingresso_da_pec allora non ci
        # saranno mail da protocollare
        if not self.env.user.has_group("sd_protocollo_pec.group_sd_protocollo_crea_protocollo_ingresso_da_pec"):
            return 0 if count else []
        domain = [
            ("protocollo_action", "=", "mail_da_protocollare"),
            ("pec", "=", True),
        ]
        if count:
            result = self.search(domain, count=count)
            _logger.debug("--- count query_mail_da_protocollare_pec %s seconds ---" % (time.time() - start_time))
            return result
        results = self.search_read(domain, ["id"])
        ids = [result["id"] for result in results]
        _logger.debug("--- select query_mail_da_protocollare_pec %s seconds ---" % (time.time() - start_time))
        return ids