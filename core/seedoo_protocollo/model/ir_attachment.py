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

_logger = logging.getLogger(__name__)


class ir_attachment(osv.Model):
    _inherit = 'ir.attachment'

    def _full_path(self, cr, uid, location, path):
        # location = 'file:filestore'
        assert location.startswith('file:'), \
            "Unhandled filestore location %s" % location
        location = location[5:]

        # sanitize location name and path
        location = re.sub('[.]', '', location)
        location = location.strip('/\\')

        path = re.sub('[.]', '', path)
        path = path.strip('/\\')
        return os.path.join('/', location, cr.dbname, path)

    def _get_full_path(self, cr, uid, ids, location):
        # TODO check if removable
        if not location:
            raise except_orm(
                _('Error'), _('Please set ir_attachment.location'))
        res = self.read(cr, uid, ids, ['res_model'])
        locations = {}
        for model_location in res:
            if model_location['res_model'] == 'protocollo.protocollo':
                #TODO insert here new path for fake document
                # if the protocol is reserved and state not draft
                location_def = location + '/protocollazioni'
            elif model_location['res_model'] == 'protocollo.protocollo.imp':
                location_def = location + '/sinekarta'
            else:
                location_def = location
            locations[model_location['id']] = location_def
        return locations

    def _data_get(self, cr, uid, ids, name, arg, context=None):
        if context is None:
            context = {}
        result = {}
        location = self.pool.get('ir.config_parameter').\
            get_param(cr, uid, 'ir_attachment.location')
        locations = self._get_full_path(cr, uid, ids, location)
        bin_size = context.get('bin_size')
        for attach in self.browse(cr, uid, ids, context=context):
            if location and attach.store_fname:
                result[attach.id] = self._file_read(
                                                    cr,
                                                    uid,
                                                    locations[attach.id],
                                                    attach.store_fname,
                                                    bin_size)
            else:
                result[attach.id] = attach.db_datas
        return result

    def _data_set(self, cr, uid, aid, name, value, arg, context=None):
        # We dont handle setting data to null
        if not value:
            return True
        if context is None:
            context = {}
        location = self.pool.get('ir.config_parameter').\
            get_param(cr, uid, 'ir_attachment.location')
        location = self._get_full_path(cr, uid, [aid], location)[aid]
        file_size = len(value.decode('base64'))
        if location:
            attach = self.browse(cr, uid, aid, context=context)
            if attach.store_fname:
                self._file_delete(cr, uid, location, attach.store_fname)
            fname = self._file_write(cr, uid, location, value)
            # SUPERUSER_ID as probably don't have write access,
            # trigger during create
            super(ir_attachment, self).write(cr, SUPERUSER_ID, [aid],
                                             {'store_fname': fname,
                                              'file_size': file_size},
                                             context=context)
        else:
            super(ir_attachment, self).write(cr, SUPERUSER_ID, [aid],
                                             {'db_datas': value,
                                              'file_size': file_size},
                                             context=context)
        return True

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
                resource = self.pool.get(attach.res_model).browse(cr, uid, attach.res_id)
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
                resource = self.pool.get(attach.res_model).browse(cr, uid, attach.res_id)
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
        'datas': fields.function(
                         _data_get,
                         fnct_inv=_data_set,
                         string='File Content',
                         type="binary",
                         nodrop=True),
        'is_pdf': fields.function(_get_is_pdf, type='boolean', string='PDF'),
        'datas_description': fields.char('Descrizione documento',  size=256),
        'is_message_attach': fields.function(_is_message_attach, fnct_search=_is_message_attach_search,
                                                  type='boolean', method=True, string='Visibile'),
        'is_eml': fields.function(_is_eml, type='boolean', method=True, string='EML'),
    }

    _order = 'is_main'

    def check(self, cr, uid, ids, mode, context=None, values=None):
        """Overwrite check to verify protocol attachments"""
        if not isinstance(ids, list):
            ids = [ids]

        super(ir_attachment, self).check(cr, uid, ids, mode,
                                         context=context, values=values)
        res = []
        state = None
        if mode != 'read':
            if ids:
                cr.execute('SELECT DISTINCT res_model, res_id \
                    from ir_attachment \
                    WHERE id in %s', (tuple(ids),))
                res = cr.fetchall()
            elif values:
                if values.get('res_model') and values.get('res_id'):
                    res.append([values['res_model'], values['res_id']])
            else:
                pass
            # for res_model, res_id in res:
            #     if res_model == 'protocollo.protocollo':
            #         cr.execute('SELECT state from protocollo_protocollo \
            #             WHERE id = %s', (str(res_id),))
            #         if cr.fetchone()[0]:
            #             state = cr.fetchone()[0]
                    # if state != 'draft':
                    #     raise except_orm(_('Operazione non permessa'),
                    #                      'Si sta cercando di modificare un \
                    #                      protocollo registrato')

    def _file_read(self, cr, uid, location, fname, bin_size=False):
        full_path = self._full_path(cr, uid, location, fname)
        r = ''
        try:
            if bin_size:
                r = os.path.getsize(full_path)
            else:
                r = open(full_path,'rb').read().encode('base64')
        except IOError:
            _logger.exception("_read_file reading %s", full_path)
        return r


    def _file_write(self, cr, uid, location, value):
        bin_value = value.decode('base64')
        fname, full_path = self._get_path(cr, uid, location, bin_value)
        if not os.path.exists(full_path):
            try:
                with open(full_path, 'wb') as fp:
                    fp.write(bin_value)
            except IOError:
                _logger.exception("_file_write writing %s", full_path)
        return fname

    def _get_path(self, cr, uid, location, bin_data):
        sha = hashlib.sha1(bin_data).hexdigest()
        sha = sha + '-%d' % random.randint(0, 1000)

        # retro compatibility
        fname = sha[:3] + '/' + sha
        full_path = self._full_path(cr, uid, location, fname)
        if os.path.isfile(full_path):
            return fname, full_path        # keep existing path

        # scatter files across 256 dirs
        # we use '/' in the db (even on windows)
        fname = sha[:2] + '/' + sha
        full_path = self._full_path(cr, uid, location, fname)
        dirname = os.path.dirname(full_path)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        return fname, full_path




    def _file_delete(self, cr, uid, location, fname):
        # using SQL to include files hidden through unlink or due to record rules
        cr.execute("SELECT COUNT(*) FROM ir_attachment WHERE store_fname = %s", (fname,))
        count = cr.fetchone()[0]
        full_path = self._full_path(cr, uid, location, fname)
        if count and os.path.exists(full_path):
            try:
                os.unlink(full_path)
            except OSError:
                _logger.exception("_file_delete could not unlink %s", full_path)
            except IOError:
                # Harmless and needed for race conditions
                _logger.exception("_file_delete could not unlink %s", full_path)

    def unlink(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        self.check(cr, uid, ids, 'unlink', context=context)
        location = self.pool.get('ir.config_parameter').get_param(cr, uid, 'ir_attachment.location')
        if location:
            for attach in self.browse(cr, uid, ids, context=context):
                location = self._get_full_path(cr, uid, [attach.id], location)[attach.id]
                if attach.store_fname:
                    #TODO check meaning for location and attach_store_fname
                    self._file_delete(cr, uid, location, attach.store_fname)
        return super(ir_att, self).unlink(cr, uid, ids, context)
