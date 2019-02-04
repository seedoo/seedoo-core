# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import fields, osv
from openerp.osv.orm import except_orm
from openerp.tools.translate import _
from openerp.addons.base.ir.ir_attachment import ir_attachment as ir_att
from openerp.modules.registry import RegistryManager
from openerp import SUPERUSER_ID
import logging
import os
import re
import hashlib
import random
import itertools


_logger = logging.getLogger(__name__)


class ir_attachment(osv.Model):
    _inherit = 'ir.attachment'

    def _get_preview_datas(self, cr, uid, ids, field, arg, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        res = dict.fromkeys(ids, False)
        for attach in self.browse(cr, uid, ids):
            res[attach.id] = attach.datas
        return res

    def _get_is_main(self, cr, uid, ids, field, arg, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        res = dict.fromkeys(ids, False)
        for attach in self.browse(cr, uid, ids):
            res[attach.id] = False
            if attach.is_protocol and attach.res_model and attach.res_id:
                resource = self.pool.get(attach.res_model).browse(cr, SUPERUSER_ID, attach.res_id)
                if resource and resource.doc_id and resource.doc_id.id == attach.id:
                    res[attach.id] = True
        return res

    def _get_reserved(self, cr, uid, ids, field, arg, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        res = dict.fromkeys(ids, False)
        for attach in self.browse(cr, uid, ids):
            res[attach.id] = False
            if attach.is_protocol and attach.res_model and attach.res_id:
                new_context = dict(context or {})
                new_context['skip_check'] = True
                resource = self.pool.get(attach.res_model).browse(cr, uid, attach.res_id, new_context)
                if resource and resource.reserved:
                    res[attach.id] = True
        return res

    def _get_is_pdf(self, cr, uid, ids, field, arg, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        res = dict.fromkeys(ids, False)
        for attach in self.browse(cr, uid, ids):
            res[attach.id] = False
            if attach.file_type == 'application/pdf':
                res[attach.id] = True
        return res

    def _is_eml(self, cr, uid, ids, field, arg, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        res = dict.fromkeys(ids, False)
        for attach in self.browse(cr, uid, ids):
            res[attach.id] = False
            if attach.name == 'original_email.eml':
                res[attach.id] = True
        return res


    def _is_message_attach(self, cr, uid, ids, name, arg, context=None):
        return {}

    def _is_message_attach_search(self, cr, uid, obj, name, args, domain=None, context=None):
        attachment_list = []
        message_id = context.get('message_id', False)
        if message_id:
            cr.execute("SELECT distinct attachment_id from message_attachment_rel where message_id = " + str(message_id))
            rec_ids = cr.dictfetchall()
            for record in rec_ids:
                attachment_list.append(record['attachment_id'])
        return [('id', 'in', attachment_list)]

    _columns = {
        'is_protocol': fields.boolean('Doc Protocollo'),
        'reserved': fields.function(_get_reserved, type='boolean', string='Documento Riservato'),
        'preview': fields.function(_get_preview_datas, type='binary', string='Preview'),
        'is_main': fields.function(_get_is_main, type='boolean', string='Documento Principale'),
        #'datas': fields.function(_data_get, fnct_inv=_data_set, string='File Content', type="binary", nodrop=True),
        'is_pdf': fields.function(_get_is_pdf, type='boolean', string='PDF'),
        'datas_description': fields.char('Descrizione documento',  size=256),
        'is_message_attach': fields.function(_is_message_attach, fnct_search=_is_message_attach_search,
                                                  type='boolean', method=True, string='Visibile'),
        'is_eml': fields.function(_is_eml, type='boolean', method=True, string='EML'),
    }

    _order = 'is_main'

    def _search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False, access_rights_uid=None):
        new_context = dict(context or {})
        new_context['skip_check'] = True
        return super(ir_attachment, self)._search(cr, uid, args, offset=offset,
                                                 limit=limit, order=order,
                                                 context=new_context, count=False,
                                                 access_rights_uid=access_rights_uid)

    def check(self, cr, uid, ids, mode, context=None, values=None):
        new_context = dict(context or {})
        new_context['skip_check'] = True
        return super(ir_attachment, self).check(cr, uid, ids, mode, context=new_context, values=None)


    def _file_read(self, cr, uid, fname, bin_size=False):
        result = False
        try:
            result = super(ir_attachment, self)._file_read(cr, uid, fname, bin_size)
        except OSError, e:
            _logger.exception("_read_file reading %s", fname)
        return result