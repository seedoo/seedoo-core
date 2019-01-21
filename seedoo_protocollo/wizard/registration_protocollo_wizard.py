
from openerp.osv import fields, orm
from openerp import models
from openerp.tools.translate import _

class protocollo_registration_confirmation_wizard(models.TransientModel):
    _name = 'protocollo.registration.confirmation.wizard'
    _description = 'Wizard di Conferma Registrazione Protocollo'

    _columns = {
        'senders': fields.html('Mittenti', readonly=True),
        'receivers': fields.html('Destinatari', readonly=True),
        'subject': fields.char('Oggetto', readonly=True),
        'assegnatario_competenza_id': fields.many2one('protocollo.assegnatario',
                                                      'Assegnatario Competenza',
                                                      readonly=True),
        'assegnatario_conoscenza_ids': fields.html('Assegnatari CC', readonly=True),
        'message_verifica_campi_obbligatori': fields.html('Verifica campi obbligatori', readonly=True)
    }

    def _default_protocollo_subject(self, cr, uid, context):
        if 'active_id' in context:
            protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'], {'skip_check': True})
        else:
            return None
        return protocollo.subject

    def _default_protocollo_senders(self, cr, uid, context):
        if 'active_id' in context:
            protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'], {'skip_check': True})
            if protocollo.senders:
                senders_list = ''
                for sender in protocollo.sender_receivers:
                    senders_list = senders_list + sender.name + '</br>'
                return senders_list
        return False

    def _default_protocollo_receivers(self, cr, uid, context):
        if 'active_id' in context:
            protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'], {'skip_check': True})
            if protocollo.receivers:
                receivers_list = ''
                for receiver in protocollo.sender_receivers:
                    receivers_list = receivers_list + receiver.name + '</br>'
                return receivers_list
        return False

    def _default_assegnatario_competenza_id(self, cr, uid, context):
        if 'active_id' in context:
            assegnazione_obj = self.pool.get('protocollo.assegnazione')
            assegnazione_ids = assegnazione_obj.search(cr, uid, [
                ('protocollo_id', '=', context['active_id']),
                ('tipologia_assegnazione', '=', 'competenza'),
                ('parent_id', '=', False)
            ])
            if assegnazione_ids:
                assegnazione = assegnazione_obj.browse(cr, uid, assegnazione_ids[0])
                return assegnazione.assegnatario_id.id
        return False

    def _default_assegnatario_conoscenza_ids(self, cr, uid, context):
        if 'active_id' in context:
            assegnazione_obj = self.pool.get('protocollo.assegnazione')
            assegnazione_ids = assegnazione_obj.search(cr, uid, [
                ('protocollo_id', '=', context['active_id']),
                ('tipologia_assegnazione', '=', 'conoscenza'),
                ('parent_id', '=', False)
            ])
            assegnatari_conoscenza_list = ''
            if assegnazione_ids:
                assegnazione_ids = assegnazione_obj.browse(cr, uid, assegnazione_ids)
                for assegnazione in assegnazione_ids:
                    if assegnazione.tipologia_assegnatario == 'department':
                        assegnatari_conoscenza_list = assegnatari_conoscenza_list + \
                                                        assegnazione.assegnatario_department_id.name + '</br>'
                    else:
                        assegnatari_conoscenza_list = assegnatari_conoscenza_list + \
                                                        assegnazione.assegnatario_employee_department_id.name + ' / ' + \
                                                        assegnazione.assegnatario_employee_id.name + '</br>'
                return assegnatari_conoscenza_list
        return False

    def _default_message_verifica_campi_obbligatori(self, cr, uid, context):
        if 'active_id' in context:
            protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'], {'skip_check': True})
            response_verifica_campi_obbligatori = self.pool.get('protocollo.configurazione').verifica_campi_obbligatori(cr, uid, protocollo)
            if response_verifica_campi_obbligatori is not True:
                return response_verifica_campi_obbligatori
        return False

    # def _default_assegnatari_competenza_uffici_ids(self, cr, uid, context):
    #     protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'])
    #     assegnatari = []
    #     for assegnatario in protocollo.assegnatari_competenza_uffici_ids:
    #         assegnatari.append({
    #             'protocollo_assegnatario_ufficio_id': assegnatario.id,
    #             'department_id': assegnatario.department_id.id,
    #             'tipo': assegnatario.tipo,
    #         })
    #     return assegnatari
    #
    # def _default_assegnatari_competenza_dipendenti_ids(self, cr, uid, context):
    #     protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'])
    #     assegnatari = []
    #     for assegnatario in protocollo.assegnatari_competenza_dipendenti_ids:
    #         assegnatari.append({
    #             'protocollo_assegnatario_dipendenti_id': assegnatario.id,
    #             'dipendente_id': assegnatario.dipendente_id.id,
    #             'state': assegnatario.state,
    #         })
    #     return assegnatari

    _defaults = {
        'senders': _default_protocollo_senders,
        'receivers': _default_protocollo_receivers,
        'subject': _default_protocollo_subject,
        'message_verifica_campi_obbligatori': _default_message_verifica_campi_obbligatori,
        'assegnatario_competenza_id': _default_assegnatario_competenza_id,
        'assegnatario_conoscenza_ids': _default_assegnatario_conoscenza_ids
        # 'assegnatari_competenza_uffici_ids': _default_assegnatari_competenza_uffici_ids,
        # 'assegnatari_competenza_dipendenti_ids': _default_assegnatari_competenza_dipendenti_ids,
    }


    def go_to_registration_response(self, cr, uid, ids, context=None):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'], {'skip_check': True})
        res = protocollo.action_register_process()
        context.update({'registration_message': res})

        return {
            'name': 'Conferma Registrazione Protocollo',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'protocollo.registration.response.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context
        }

class protocollo_registration_response_wizard(models.TransientModel):
    _name = 'protocollo.registration.response.wizard'
    _description = 'Esito Registrazione Protocollo'
    _columns = {
        'message': fields.html(string="Esito Registrazione", readonly=True, store=False)
    }

    def _default_message(self, cr, uid, context=None):
        res = ""
        if context is None:
            context = {}
        if 'registration_message' in context and context['registration_message']:
            res += "<ul>"
            for operation in context['registration_message']:
                for operation_item in operation:
                    if operation[operation_item]['Res'] and operation_item == 'Registrazione':
                        res += "<li><h2><span class='fa fa-check-circle'></span> %s </h2></li>" % (operation[operation_item]['Msg'])
                    elif not operation[operation_item]['Res'] and operation[operation_item]['Msg'] is not None:
                        res += "<li><span class='fa fa-exclamation-triangle'></span> %s</li>" % (operation[operation_item]['Msg'])
            res += "</ul>"
            return res
        return res

    _defaults = {
        'message': _default_message
    }