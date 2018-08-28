# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import orm, osv, fields
from openerp import SUPERUSER_ID


class board_board(osv.osv):

    _inherit = 'board.board'

    def fields_view_get(self, cr, user, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        if view_id and user!=SUPERUSER_ID:
            dashboard_view_id = self.pool.get('ir.model.data').get_object_reference(cr, user, 'seedoo_protocollo',
                                                                                    'protocollo_dashboard_form')[1]
            error = self.pool.get('protocollo.protocollo').seedoo_error(cr, user)
            if view_id == dashboard_view_id and error:
                view_id = self.pool.get('ir.model.data').get_object_reference(cr, user, 'seedoo_protocollo',
                                                                              'protocollo_dashboard_error_form')[1]
        res = super(board_board, self).fields_view_get(cr, user, view_id, view_type, context=context, toolbar=toolbar, submenu=submenu)
        return res