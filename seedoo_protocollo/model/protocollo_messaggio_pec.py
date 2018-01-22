# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import orm, fields


class protocollo_messaggio_pec(orm.Model):
    _name = 'protocollo.messaggio.pec'

    def _get_default_name(self, cr, uid, context=None):
        return 'PEC'

    _columns = {
        'name': fields.char('Nome', size=256, required=True),
        'type': fields.selection(
            [
                ('messaggio', 'Messaggio'),
                ('conferma', 'Conferma'),
                ('annullamento', 'Annullamento')
            ],
            'Tipologia', size=32, required=False),
        'messaggio_ref': fields.many2one('mail.message', 'Messaggio PEC'),
        'accettazione_ref': fields.many2one('mail.message', 'Accettazione PEC', readonly=True),
        'consegna_ref': fields.many2one('mail.message', 'Consegna PEC', readonly=True),
        'errore_consegna_ref': fields.many2one('mail.message', 'Errore Consegna PEC', readonly=True),
        'messaggio_id': fields.related('messaggio_ref', 'id', type='float', string = 'Id Messaggio', readonly = True),
        'accettazione_id': fields.related('accettazione_ref', 'id', type='float', string = 'Id Accettazione', readonly = True),
        'messaggio_ora': fields.related('messaggio_ref', 'date', type='datetime', string='Orario Invio PEC', readonly=False, store=False),
        'accettazione_ora': fields.related('accettazione_ref', 'cert_datetime', type='datetime', string='Orario PEC Accettazione', readonly=False, store=False),
        'consegna_ora': fields.related('consegna_ref', 'cert_datetime', type='datetime', string='Orario PEC Consegna', readonly=False, store=False),
        'errore_consegna_ora': fields.related('errore_consegna_ref', 'cert_datetime', type='datetime', string='Orario PEC Errore Consegna', readonly=False, store=False),
        'messaggio_direction': fields.related('messaggio_ref', 'direction', type='char', string='Direzione Messaggio', readonly=False, store=False)
    }

    _defaults = {
        'name': _get_default_name
    }

    def go_to_pec_action(self, cr, uid, context=None):
        model_data_obj = self.pool.get('ir.model.data')
        view_rec = model_data_obj.get_object_reference(cr, uid, 'seedoo_protocollo', 'protocollo_pec_form')
        view_id = view_rec and view_rec[1] or False
        return {
            'name': 'PEC',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [view_id],
            'res_model': 'mail.message',
            'target': 'new',
            'res_id': context.get('pec_ref', False),
            'type': 'ir.actions.act_window',
            'flags': {'form': {'options': {'mode': 'view'}}}
        }

    def go_to_messaggio_action(self, cr, uid, ids, context=None):
        return self.go_to_pec_action(cr, uid, context=context)

    def go_to_accettazione_action(self, cr, uid, ids, context=None):
        return self.go_to_pec_action(cr, uid, context=context)

    def go_to_consegna_action(self, cr, uid, ids, context=None):
        return self.go_to_pec_action(cr, uid, context=context)

    def go_to_errore_consegna_action(self, cr, uid, ids, context=None):
        return self.go_to_pec_action(cr, uid, context=context)