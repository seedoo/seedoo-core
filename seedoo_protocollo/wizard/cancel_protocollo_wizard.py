# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

import logging
from openerp import SUPERUSER_ID
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
from openerp import netsvc

_logger = logging.getLogger(__name__)


class wizard(osv.TransientModel):
    """
        A wizard to manage the cancel state of protocol
    """
    _name = 'protocollo.cancel.wizard'
    _description = 'Cancel Protocol Management'

    _columns = {
        'name': fields.char(
            'Causa Cancellazione',
            required=True,
            readonly=False
        ),
        'user_id': fields.many2one(
            'hr.employee',
            'Responsabile',
            readonly=True
        ),
        'agent_id': fields.many2one(
            'hr.employee',
            'Mandante',
            readonly=False
        ),
        'date_cancel': fields.datetime(
            'Data Cancellazione',
            required=True,
            readonly=True
        ),
    }

    def _default_user_id(self, cr, uid, context):
        employee_obj = self.pool.get('hr.employee')
        assegnazione_obj = self.pool.get('protocollo.assegnazione')
        protocollo_obj = self.pool.get('protocollo.protocollo')
        protocollo = protocollo_obj.browse(cr, uid, context['active_id'], {'skip_check': True})

        if uid == protocollo.user_id.id:
            employee_ids = employee_obj.search(cr, uid, [
                ('user_id', '=', uid),
                ('department_id', '=', protocollo.registration_employee_department_id.id)
            ])
            if employee_ids:
                return employee_ids[0]
        else:
            assegnazione_ids = assegnazione_obj.search(cr, uid, [
                ('assegnatario_employee_id.user_id.id', '=', uid),
                ('protocollo_id', '=', protocollo.id),
                ('tipologia_assegnazione', '=', 'competenza'),
                ('tipologia_assegnatario', '=', 'employee'),
                ('state', '=', 'preso')
            ])
            if assegnazione_ids:
                assegnazione = assegnazione_obj.browse(cr, uid, assegnazione_ids[0])
                return assegnazione.assegnatario_employee_id.id

        if uid == SUPERUSER_ID:
            employee_ids = employee_obj.search(cr, uid, [('user_id', '=', uid)])
            if employee_ids:
                return employee_ids[0]

        return False

    _defaults = {
        'user_id': _default_user_id,
        'date_cancel': fields.datetime.now
    }

    def action_cancel(self, cr, uid, ids, context=None):
        configurazione_ids = self.pool.get('protocollo.configurazione').search(cr, uid, [])
        configurazione = self.pool.get('protocollo.configurazione').browse(cr, uid, configurazione_ids[0])
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'], {'skip_check': True})
        wizard = self.browse(cr, uid, ids[0], context)

        if protocollo.state in 'canceled':
            raise orm.except_orm(_("Avviso"),
                                 _("Il protocollo è già stato annullato in precedenza"))

        if wizard.name and wizard.date_cancel:
            wf_service = netsvc.LocalService('workflow')
            wf_service.trg_validate(uid, 'protocollo.protocollo', context['active_id'], 'cancel', cr)


            if protocollo.type == 'in' and protocollo.pec and configurazione.annullamento_xml_invia:
                new_context = dict(context).copy()
                new_context.update({'receipt_cancel_reason': wizard.name})
                new_context.update({'receipt_cancel_author': wizard.agent_id.name})
                new_context.update({'receipt_cancel_date': wizard.date_cancel})
                self.pool.get('protocollo.protocollo').action_send_receipt(cr, uid, [protocollo.id], 'annullamento', context=new_context)

            action_class = "history_icon trash"

            request_by = wizard.user_id.name
            if wizard.agent_id:
                request_by = wizard.agent_id.name
            body = "<div class='%s'><ul><li>Annullamento richiesto da <span style='color:#990000;'>%s</span></li></ul></div>" % (action_class, request_by)

            post_vars = {'subject': "Protocollo annullato:  %s" %wizard.name,
                         'body': body,
                         'model': "protocollo.protocollo",
                         'res_id': context['active_id'],
                         }

            thread_pool = self.pool.get('protocollo.protocollo')
            thread_pool.message_post(cr, uid, context['active_id'], type="notification", context=context, **post_vars)

        return {'type': 'ir.actions.act_window_close'}
