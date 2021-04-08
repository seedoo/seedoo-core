
from openerp.osv import fields, orm
from openerp import models
from openerp import SUPERUSER_ID
from openerp.tools.translate import _

class confirm_operation_wizard(models.TransientModel):
    _name = 'confirm.operation.wizard'
    _description = 'Wizard di Conferma operazione'

    _columns = {
        'message': fields.html(string="Conferma operazione", readonly=True, store=False)
    }

    def _default_message(self, cr, uid, context=None):
        res = ""
        if context is None:
            context = {}
        if 'action_not_protocol_pec' in context and context['action_not_protocol_pec']:
            res = '<p>Vuoi archiviare questo messaggio PEC?</p>'
        if 'action_not_protocol_sharedmail' in context and context['action_not_protocol_sharedmail']:
            res = '<p>Vuoi archiviare questo messaggio e-mail?</p>'
        if 'action_not_protocol_document' in context and context['action_not_protocol_document']:
            res = '<p>Vuoi archiviare questo messaggio documento?</p>'
        return res

    _defaults = {
        'message': _default_message
    }


    def go_to_operation(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        if 'action_not_protocol_sharedmail' in context and context['action_not_protocol_sharedmail']:
            message_obj = self.pool.get('mail.message')
            message = message_obj.browse(cr, SUPERUSER_ID, context['active_id'])
            if message.sharedmail_state == 'new':
                message_obj.write(cr, uid, context['active_id'], {'sharedmail_state': 'not_protocol'})
            else:
                raise orm.except_orm(_("Avviso"), _("Messaggio gia' archiviato in precedenza: aggiorna la pagina"))

        if 'action_not_protocol_pec' in context and context['action_not_protocol_pec']:
            message_obj = self.pool.get('mail.message')
            message = message_obj.browse(cr, SUPERUSER_ID, context['active_id'])
            if message.pec_state == 'new':
                message_obj.write(cr, uid, context['active_id'], {'pec_state': 'not_protocol'})
            else:
                raise orm.except_orm(_("Avviso"), _("Messaggio gia' archiviato in precedenza: aggiorna la pagina"))

        if 'action_not_protocol_document' in context and context['action_not_protocol_document']:
            document_obj = self.pool.get('gedoc.document')
            document = document_obj.browse(cr, SUPERUSER_ID, context['active_id'])
            if document.doc_protocol_state == 'new':
                document_obj.write(cr, SUPERUSER_ID, context['active_id'], {'doc_protocol_state': 'not_protocol'})
            else:
                raise orm.except_orm(_("Avviso"), _("Documento gia' archiviato in precedenza: aggiorna la pagina"))

        return True

    # def go_to_operation(self, cr, uid, ids, context=None):
    #     protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'])
    #     res = protocollo.action_register_process()
    #     context.update({'registration_message': res})
    #
    #     return {
    #         'name': 'Wizard Protocollo Registration Response',
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'res_model': 'protocollo.registration.response.wizard',
    #         'type': 'ir.actions.act_window',
    #         'target': 'new',
    #         'context': context
    #     }