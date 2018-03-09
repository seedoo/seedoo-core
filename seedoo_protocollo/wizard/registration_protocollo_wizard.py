
from openerp.osv import fields
from openerp import models

class protocollo_registration_confirmation_wizard(models.TransientModel):
    _name = 'protocollo.registration.confirmation.wizard'
    _description = 'Wizard di Conferma Registrazione Protocollo'

    _columns = {
        'subject': fields.char('Subject', readonly=True),
        # 'assegnatari_competenza_uffici_ids': fields.one2many('protocollo.assegna.ufficio.wizard',
        #          'competenza_uffici_wizard_id', 'Uffici Assegnatari per Competenza'),
        # 'assegnatari_competenza_dipendenti_ids': fields.one2many('protocollo.assegna.dipendente.wizard',
        #          'competenza_dipendenti_wizard_id', 'Dipendenti Assegnatari per Competenza'),
    }

    def _default_protocollo_subject(self, cr, uid, context):
        if 'active_id' in context:
            protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'])
        else:
            return None
        return protocollo.id

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
        'subject': _default_protocollo_subject,
        # 'assegnatari_competenza_uffici_ids': _default_assegnatari_competenza_uffici_ids,
        # 'assegnatari_competenza_dipendenti_ids': _default_assegnatari_competenza_dipendenti_ids,
    }


    def go_to_registration_response(self, cr, uid, ids, context=None):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'])
        res = protocollo.action_register_process()
        context.update({'registration_message': res})

        return {
            'name': 'Wizard Protocollo Registration Response',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'protocollo.registration.response.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context
        }

class protocollo_registration_response_wizard(models.TransientModel):
    _name = 'protocollo.registration.response.wizard'
    _description = 'Protocollo Registration Response wizard'
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