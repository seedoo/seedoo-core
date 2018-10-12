# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.
import base64

from openerp import SUPERUSER_ID
from openerp.osv import fields, osv
from lxml import etree


class CreaProtocolloDaDocumentoWizard(osv.TransientModel):
    _name = 'dematerializzazione.crea.protocollo.da.documento.wizard'
    _description = 'Create Protocollo da Documento'

    _columns = {
        'registration_employee_department_id': fields.many2one('hr.department', 'Il mio ufficio'),
        'registration_employee_department_id_invisible': fields.boolean('Campo registration_employee_department_id invisible', readonly=True),
        'doc_principale': fields.many2one('ir.attachment', 'Documento da protocollare', readonly=True),
        'doc_fname': fields.related('doc_principale', 'datas_fname', type='char', readonly=True),
        'doc_description': fields.char('Descrizione documento', size=256, readonly=False),
        'preview': fields.binary('Anteprima allegato PDF'),
    }

    def _default_registration_employee_department_id(self, cr, uid, context):
        department_ids = self.pool.get('hr.department').search(cr, uid, [('can_used_to_protocol', '=', True)])
        if department_ids:
            return department_ids[0]
        return False

    def _default_registration_employee_department_id_invisible(self, cr, uid, context):
        department_ids = self.pool.get('hr.department').search(cr, uid, [('can_used_to_protocol', '=', True)])
        if len(department_ids) == 1:
            return True
        return False

    def _get_attachment_id(self, cr, uid, context):
        attachments = self.pool.get('ir.attachment').search(cr, uid, [
            ('res_model', '=', 'gedoc.document'),
            ('res_id', '=', context.get('active_id', False))
        ])
        if attachments:
            return attachments[0]
        return False

    def _default_doc_principale(self, cr, uid, context):
        return self._get_attachment_id(cr, uid, context)

    def _default_preview(self, cr, uid, context):
        attachment_id = self._get_attachment_id(cr, uid, context)
        if attachment_id:
            return self.pool.get('ir.attachment').browse(cr, uid, attachment_id).datas
        return False

    _defaults = {
        'registration_employee_department_id': _default_registration_employee_department_id,
        'registration_employee_department_id_invisible': _default_registration_employee_department_id_invisible,
        'doc_principale': _default_doc_principale,
        'preview': _default_preview,
    }

    def action_save(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids[0], context=context)
        protocollo_obj = self.pool.get('protocollo.protocollo')

        document = self.pool.get('gedoc.document').browse(cr, uid, context.get('active_id'))

        vals = {}
        vals['type'] = 'in'
        vals['user_id'] = uid
        vals['typology'] = document.typology_id.id if document.typology_id else False
        vals['doc_imported_ref'] = context.get('active_id')
        vals['registration_employee_department_id'] = wizard.registration_employee_department_id.id
        vals['registration_employee_department_name'] = wizard.registration_employee_department_id.complete_name
        protocollo_id = protocollo_obj.create(cr, uid, vals)

        protocollo_obj.carica_documento_principale(cr, uid, protocollo_id, wizard.preview, wizard.doc_fname,
                                                   wizard.doc_description,
                                                   {'skip_check': True})
        protocollo_obj.associa_importer_protocollo(cr, SUPERUSER_ID, protocollo_id, document.importer_id.id)

        action_class = "history_icon print"
        post_vars = {
            'subject': "Creata Bozza Protocollo",
            'body': "<div class='%s'><ul><li>Documento convertito in bozza di protocollo</li></ul></div>" % action_class,
            'res_id': protocollo_id,
            'model': 'protocollo.protocollo',
        }
        thread_pool = self.pool.get('protocollo.protocollo')
        thread_pool.message_post(cr, uid, protocollo_id, type="notification", context=context, **post_vars)

        self.pool.get('gedoc.document').write(cr, uid, [context.get('active_id')], {
                                                                                        'protocollo_id': protocollo_id,
                                                                                        'doc_protocol_state': 'protocol'
                                                                                    })

        obj_model = self.pool.get('ir.model.data')
        model_data_ids = obj_model.search(cr, uid, [('model', '=', 'ir.ui.view'), ('name', '=', 'protocollo_protocollo_form')])
        resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'protocollo.protocollo',
            'res_id': protocollo_id,
            'views': [(resource_id, 'form')],
            'type': 'ir.actions.act_window',
            'context': context,
        }