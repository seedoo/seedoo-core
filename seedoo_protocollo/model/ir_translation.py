# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp import models


class IrTranslation(models.Model):
    _inherit = 'ir.translation'

    def _get_import_cursor(self, cr, uid, context=None):
        """Allow translation updates."""
        if context is None:
            context = {}
        context['overwrite'] = True
        return super(IrTranslation, self)._get_import_cursor(cr, uid, context=context)