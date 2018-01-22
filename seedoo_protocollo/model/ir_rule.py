# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp import models, SUPERUSER_ID

class IrRule(models.Model):
    _inherit = 'ir.rule'

    def domain_get(self, cr, uid, model_name, mode='read', context=None):
        if model_name == 'protocollo.protocollo':
            dom = self._compute_domain(cr, uid, model_name, mode)
            if dom:
                new_context = {}
                if context:
                    new_context = context.copy()
                new_context['uid'] = uid
                # _where_calc is called as superuser. This means that rules can
                # involve objects on which the real uid has no acces rights.
                # This means also there is no implicit restriction (e.g. an object
                # references another object the user can't see).
                query = self.pool[model_name]._where_calc(cr, SUPERUSER_ID, dom, active_test=False, context=new_context)
                return query.where_clause, query.where_clause_params, query.tables
            return [], [], ['"' + self.pool[model_name]._table + '"']

        return super(IrRule, self).domain_get(cr, uid, model_name, mode=mode, context=context)