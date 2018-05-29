# -*- coding: utf-8 -*-
# © 2017 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import fields, models


class IrModelData(models.Model):
    _inherit = 'ir.model.data'

    def update_vals(self, cr, uid, domain, vals, context=None):
        data_ids = self.search(cr, uid, domain)
        if data_ids:
            self.write(cr, uid, data_ids, vals)