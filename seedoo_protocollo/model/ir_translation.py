# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp import models


class IrTranslation(models.Model):
    _inherit = 'ir.translation'

    def delete_template_translations(self, cr, uid, domain, context=None):
        data_ids = self.search(cr, uid, domain)
        if data_ids:
            self.unlink(cr, uid, data_ids)