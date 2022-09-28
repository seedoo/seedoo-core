import textwrap

from odoo import models, api


class UtilityString(models.AbstractModel):
    _name = "fl.utility.string"
    _description = "Utility for strings manipulation"

    @api.model
    def truncate(self, string: str, max_length: int = 150) -> str:
        if not isinstance(string, str):
            return ""

        short_string = textwrap.shorten(
            string,
            width=max_length,
            tabsize=4
        )

        return short_string
