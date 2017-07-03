# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

import logging
from openerp.osv import fields, osv
from openerp.tools.translate import _
import mimetypes
from openerp import netsvc

_logger = logging.getLogger(__name__)


class wizardAttachments(osv.TransientModel):
    """
        Attachments for this document
    """
    _name = 'gedoc.upload.attachment.wizard'
    _description = 'Document Attachment'
    _rec_name = 'ldatas_fname'

    _columns = {
        'ldatas_fname': fields.char('Nome',
                                   size=256,
                                   readonly=False,
                                   required=True),
        'ldatas': fields.binary('File Allegato',
                               required=True),
        'wizard_id': fields.many2one('gedoc.upload.doc.wizard',
                                     'Upload Document Wizard'),
    }


class wizard(osv.TransientModel):
    """
        A wizard to manage the upload of an administrative document
    """
    _name = 'gedoc.upload.doc.wizard'
    _description = 'Administrative Document'

    _columns = {
        'name': fields.char('Numero Interno',
                            size=256,
                            required=True,
                            readonly=True),
        'datas_fname': fields.char('Nome Documento',
                                   size=256,
                                   readonly=False),
        'datas': fields.binary('File Documento',
                               required=False),
        'attachs': fields.one2many('gedoc.upload.attachment.wizard',
                                   'wizard_id',
                                   'Altri Allegati al Documento Principale')
    }

    _defaults = {
        'name': 'Nuovo Documento',
    }

    def action_save(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids[0], context)
        if not wizard.datas_fname:
            raise osv.except_osv(_('Attenzione!'), _('Documento non trovato!'))
        gedoc_document_obj = self.pool.get('gedoc.document')
        attachment_obj = self.pool.get('ir.attachment')
        # Nuovi Allegati
        for attach in wizard.attachs:
            attachment_obj.create(
                cr,
                uid,
                {
                    'name': attach.ldatas_fname,
                    'datas': attach.ldatas,
                    'datas_fname': attach.ldatas_fname,
                    'res_model': 'gedoc.document',
                    'res_id': context['active_id'],
                }
            )
        # Doc Principale
        attachment_id = attachment_obj.create(
            cr,
            uid,
            {
                'name': wizard.datas_fname,
                'datas': wizard.datas,
                'datas_fname': wizard.datas_fname,
                'res_model': 'gedoc.document',
                'res_id': context['active_id'],
            }
        )
        vals = {
            'name': wizard.datas_fname,
            'data_doc': fields.datetime.now(),
            'main_doc_id': attachment_id
        }
        gedoc_document_obj.write(cr, uid, context['active_id'], vals)
        return {'type': 'ir.actions.act_window_close'}
