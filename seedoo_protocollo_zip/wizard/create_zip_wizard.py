# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

import logging
from openerp.osv import fields, osv
from openerp.tools.translate import _
import tempfile
import zipfile
import os

_logger = logging.getLogger(__name__)


class wizard(osv.TransientModel):
    """
        A wizard to manage the download of protocol attachments
    """
    _name = 'protocollo.archivio.zip'
    _description = 'Download Zip Attachments'
    _transient_max_hours = 0.1

    _columns = {
        'datas_fname': fields.char('Nome Archivio',
                                   size=256,
                                   readonly=True),
        'datas': fields.binary('File Documento',
                               required=False,
                               readonly=True),
        'view_fields': fields.boolean('View Fields'),
    }

    def _get_name(self, cr, uid, context):
        protocol_obj = self.pool.get('protocollo.protocollo')
        protocol = protocol_obj.browse(cr,
                                       uid,
                                       context['active_id']
                                       )
        return protocol.name + '_' + str(protocol.year) + '.zip'

    def _get_datas(self, cr, uid, context):
        protocol_obj = self.pool.get('protocollo.protocollo')
        protocol = protocol_obj.browse(cr,
                                       uid,
                                       context['active_id']
                                       )
        attachment_obj = self.pool.get('ir.attachment')
        attachment_ids = attachment_obj.search(cr, uid,
                                               [('id',
                                                 '!=',
                                                 protocol.doc_id.id),
                                                ('res_model',
                                                 '=',
                                                 'protocollo.protocollo'),
                                                ('res_id',
                                                 '=',
                                                 context['active_id'])]
                                               )
        location = self.pool.get('ir.config_parameter')\
            .get_param(cr, uid, 'ir_attachment.location') + '/protocollazioni'
        # Creates Temporary File
        with tempfile.NamedTemporaryFile(prefix='Prot' +
                                         protocol.complete_name,
                                         suffix='.zip', delete=False) as tmp:
            with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as archive:
                # Add primary document to archive
                file_path = protocol_obj._full_path(cr,
                                                    uid,
                                                    location,
                                                    protocol.doc_id.store_fname
                                                    )
                archive.write(file_path, protocol.name + '_' +
                              str(protocol.year) + '/' + protocol.doc_id.name)
                for num, attachment in enumerate(attachment_obj.browse(
                        cr, uid, attachment_ids, context=context)):
                    file_path = protocol_obj._full_path(cr,
                                                        uid,
                                                        location,
                                                        attachment.store_fname
                                                        )
                    prefix = 'All' + str(num + 1) + '-Prot' + \
                        protocol.complete_name + '-'
                    archive.write(file_path, protocol.name + '_' +
                                  str(protocol.year) + '/' +
                                  prefix + attachment.name)
        with open(tmp.name) as zipf:
            datas = zipf.read().encode('base64')
        os.remove(tmp.name)
        return datas

    _defaults = {
        'view_fields': False,
    }

    def view_init(self, cr, uid, fields_list, context=None):
        protocollo_model = self.pool.get('protocollo.protocollo')
        if context is None:
            context = {}
        if context.get('active_id', False):
            protocollo = protocollo_model.browse(cr, uid,
                                                 context['active_id'],
                                                 context=context)
            if protocollo.reserved:
                raise osv.except_osv(_('Attenzione!'),
                                     _('Operazione non permessa:'
                                       'protocollo riservato')
                                     )
            if protocollo.state \
                    not in \
                    ('registered', 'sent', 'notified'):
                raise osv.except_osv(_('Attenzione!'),
                                     _('Operazione non permessa in \
                                     questo stato del protocollo')
                                     )

    def create_archive(self, cr, uid, ids, context=None):
        file_name = self._get_name(cr, uid, context)
        file_datas = self._get_datas(cr, uid, context)
        vals = {
            'datas_fname': file_name,
            'datas': file_datas,
            'view_fields': True
        }
        self.write(cr, uid, ids[0], vals, context=context)
        return {
            'name': _('Archivio Protocollo'),
            'type': 'ir.actions.act_url',
            'url': '#id=%s&view_type=form&model=protocollo.archivio.zip'
            % str(ids[0])
            }

    def action_done(self, cr, uid, ids, context=None):
        return {'type': 'ir.actions.act_window_close'}
