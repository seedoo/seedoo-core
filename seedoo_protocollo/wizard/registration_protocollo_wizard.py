
from openerp.osv import fields
from openerp import models

class protocollo_registration_wizard(models.TransientModel):
    _name = 'protocollo.registration.wizard'
    _description = 'Protocollo Registration wizard'
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