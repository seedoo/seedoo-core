# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

import logging
from openerp.osv import fields, osv
import mimetypes

_logger = logging.getLogger(__name__)


class wizard(osv.TransientModel):
    """
        A wizard to manage the upload of document protocollo
    """
    _name = 'protocollo.upload.wizard'
    _description = 'Upload Document Management'

    _rec_name = 'datas_fname'

    _columns = {
        'datas_fname': fields.char(
            'Nome Documento',
            size=256,
            readonly=False
        ),
        'datas': fields.binary(
            'File Documento',
            required=False
        ),
    }

    def _clear_doc(self, cr, uid, attachment_obj, pid):
        attachment_ids = attachment_obj.search(
            cr,
            uid,
            [
                ('res_model',
                 '=',
                 'protocollo.protocollo'),
                ('res_id',
                 '=',
                 pid),
                ('is_protocol',
                 '=',
                 True),
            ]
        )
        if attachment_ids:
            return attachment_obj.unlink(cr, uid, attachment_ids)

    def action_save(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids[0], context)
        if wizard.datas and wizard.datas_fname:
            ftype = mimetypes.guess_type(wizard.datas_fname)
            mimetype = mimetypes.guess_extension(ftype[0])
            if mimetype not in ('.pdf'):
                raise osv.except_osv(
                    _('Attenzione!'),
                    _('Il documento da protocollare \
                       deve necessariamente avere \
                       estensione .pdf!')
                )
            protocollo_obj = self.pool.get('protocollo.protocollo')
            attachment_obj = self.pool.get('ir.attachment')
            self._clear_doc(cr, uid, attachment_obj, context['active_id'])
            attachment_id = attachment_obj.create(
                cr, uid,
                {
                    'name': wizard.datas_fname,
                    'datas': wizard.datas,
                    'datas_fname': wizard.datas_fname,
                    'res_model': 'protocollo.protocollo',
                    'is_protocol': True,
                    'res_id': context['active_id'],
                }
            )
            protocollo_obj.write(
                cr,
                uid,
                context['active_id'],
                {'doc_id': attachment_id}
            )
        return {'type': 'ir.actions.act_window_close'}
