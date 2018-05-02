# -*- coding: utf-8 -*-

from openerp import models, fields, api


class TileTile(models.Model):
    _inherit = "tile.tile"

    SELECTION_MODE = [
        ("domain", "Compute count on domain result"),
        ("method", "Run a method of the selected model")
    ]

    mode = fields.Selection(
        string="Mode",
        help="Mode",
        selection=SELECTION_MODE,
        default=SELECTION_MODE[0][0]
    )

    method = fields.Char(
        string="Method name",
        help="Method name"
    )

    domain_method = fields.Char(
        string="Domain/Method",
        help="Domain/Method",
        compute="_compute_domain_method"
    )

    @api.onchange("mode")
    def _onchange_mode(self):
        for rec in self:
            if rec.mode == self.SELECTION_MODE[1][0]:
                rec.primary_function = "count"

    @api.one
    def _compute_data(self):
        if not self.active:
            return

        model = self.env[self.model_id.model]
        eval_context = self._get_eval_context()
        domain = self.domain or "[]"

        try:
            if self.mode == self.SELECTION_MODE[0][0]:
                count = model.search_count(eval(domain, eval_context))
            elif self.mode == self.SELECTION_MODE[1][0]:
                model_method = getattr(model, self.method)
                count = model_method()
        except Exception as e:
            self.primary_value = self.secondary_value = "ERR!"
            self.error = str(e)
            return

        if any([
            self.primary_function and self.primary_function != "count",
            self.secondary_function and self.secondary_function != "count"
        ]):
            records = model.search(eval(domain, eval_context))

        for f in ["primary_", "secondary_"]:
            f_function = f + "function"
            f_field_id = f + "field_id"
            f_format = f + "format"
            f_value = f + "value"
            value = 0

            if self[f_function] == "count":
                value = count
            elif self[f_function]:
                func = self.FIELD_FUNCTIONS[self[f_function]]["func"]
                if func and self[f_field_id] and count:
                    vals = [x[self[f_field_id].name] for x in records]
                    value = func(vals)

            if self[f_function]:
                try:
                    self[f_value] = (self[f_format] or "{:,}").format(value)
                except ValueError as e:
                    self[f_value] = "F_ERR!"
                    self.error = str(e)
                    return
            else:
                self[f_value] = False

    def _compute_domain_method(self):
        for rec in self:
            if rec.mode == self.SELECTION_MODE[0][0]:
                rec.domain_method = rec.domain
            elif rec.mode == self.SELECTION_MODE[1][0]:
                rec.domain_method = rec.method

    @api.multi
    def open_link(self):
        self.ensure_one()

        res = {
            "name": self.name,
            "view_type": "form",
            "view_mode": "tree",
            "view_id": [False],
            "res_model": self.model_id.model,
            "type": "ir.actions.act_window",
            "context": self.env.context,
            "nodestroy": True,
            "target": "current",
            "domain": self.domain,
        }

        if self.action_id:
            res.update(self.action_id.read(["domain", "view_type", "view_mode", "type"])[0])

        return res
